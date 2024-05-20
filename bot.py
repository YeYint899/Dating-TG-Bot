import logging
import firebase_admin
from firebase_admin import credentials, db
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Firebase setup
cred = credentials.Certificate('path/to/firebase_credentials.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-database-name.firebaseio.com/'
})

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Stages
GENDER, AGE, PHOTO, SEARCH, CONNECT = range(5)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hi! I am your Dating Bot. Let\'s create your profile.\n'
        'Are you male or female?',
        reply_markup=ReplyKeyboardMarkup([['Male', 'Female']], one_time_keyboard=True)
    )
    return GENDER

# Gender handler
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    ref = db.reference(f'users/{user_id}')
    ref.update({'gender': update.message.text})
    await update.message.reply_text('Please enter your age.')
    return AGE

# Age handler
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    ref = db.reference(f'users/{user_id}')
    ref.update({'age': update.message.text})
    await update.message.reply_text('Please send me your profile photo.')
    return PHOTO

# Photo handler
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f'{user_id}.jpg'
    await photo_file.download(photo_path)
    ref = db.reference(f'users/{user_id}')
    ref.update({'photo': photo_path})
    await update.message.reply_text('Profile created! You can now search for a partner using /search')
    return ConversationHandler.END

# Search command handler
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_gender = db.reference(f'users/{user_id}/gender').get()
    target_gender = 'Female' if user_gender == 'Male' else 'Male'
    
    # Filter users who are not already matched with the current user
    matches_ref = db.reference(f'matches/{user_id}')
    matched_users = set(matches_ref.get().keys() if matches_ref.get() else [])

    partners = db.reference('users').order_by_child('gender').equal_to(target_gender).get()
    filtered_partners = {k: v for k, v in partners.items() if k not in matched_users}

    if not filtered_partners:
        await update.message.reply_text('No partners found. Try again later.')
        return ConversationHandler.END

    context.user_data['partners'] = list(filtered_partners.keys())
    await show_partner(update, context)
    return SEARCH

# Show partner handler
async def show_partner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.user_data['partners']:
        await update.message.reply_text('No more partners found.')
        return ConversationHandler.END

    partner_id = context.user_data['partners'].pop()
    partner_profile = db.reference(f'users/{partner_id}').get()

    await update.message.reply_photo(
        photo=open(partner_profile['photo'], 'rb'),
        caption=f"Age: {partner_profile['age']}\nDo you like this profile?",
        reply_markup=ReplyKeyboardMarkup([['Yes', 'No']], one_time_keyboard=True)
    )
    context.user_data['current_partner'] = partner_id
    return CONNECT

# Connect handler
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == 'Yes':
        user_id = update.message.from_user.id
        partner_id = context.user_data['current_partner']
        db.reference(f'matches/{user_id}/{partner_id}').set(True)
        db.reference(f'matches/{partner_id}/{user_id}').set(True)

        await context.bot.send_message(partner_id, f"You have a new match: {update.message.from_user.username}")
        await update.message.reply_text(f"You are now connected with {partner_id}. Start chatting!")
        return ConversationHandler.END
    else:
        return await show_partner(update, context)

# Disconnect command handler
async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    matches_ref = db.reference(f'matches/{user_id}')
    matches = matches_ref.get()

    if not matches:
        await update.message.reply_text('You have no matches to disconnect.')
        return

    match_ids = list(matches.keys())
    keyboard = [[str(uid)] for uid in match_ids]

    await update.message.reply_text(
        'Select a match to disconnect:',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return 'DISCONNECT'

async def confirm_disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    partner_id = update.message.text

    # Remove from matches
    db.reference(f'matches/{user_id}/{partner_id}').delete()
    db.reference(f'matches/{partner_id}/{user_id}').delete()

    await update.message.reply_text(f'You have disconnected from {partner_id}.')
    await context.bot.send_message(partner_id, f'You have been disconnected by {update.message.from_user.username}')
    return ConversationHandler.END

def main() -> None:
    application = ApplicationBuilder().token('YOUR_BOT_API_TOKEN').build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            PHOTO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, photo)],
            SEARCH: [CommandHandler('search', search)],
            CONNECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, connect)],
            'DISCONNECT': [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_disconnect)]
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('disconnect', disconnect))
    application.run_polling()

if __name__ == '__main__':
    main()
