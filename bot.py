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
        'Dating 🇲🇲 Botမှကြိုဆိုပါတယ်။သင့်ရဲ့Profile Dataများကို ပြည့်စုံစွာပို့ပေးရန်လိုအက်ပါသည်။'
        'သင့်ရဲ့ Telegram Usernameကိုမှတ်သားလိုက်ပါပြီ။Usernameမဖြည့်ရသေးရင်သင့်ရဲ့ TG Accမှာသွားဖြည့်ထားပါ။ ဥပမာ : @yourname'
    )
    return GENDER

async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    ref = db.reference(f'users/{user_id}')
    ref.update({'username': update.message.text})
    await update.message.reply_text(
        'ကျေးဇူးပါ။ သင့်ရဲ့လိင်အမျိုးအစား (ကျား/မ)ရေွး‌ေပးပါ',
        reply_markup=ReplyKeyboardMarkup([['Male', 'Female']], one_time_keyboard=True)
    )
    return GENDER


# Gender handler
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    ref = db.reference(f'users/{user_id}')
    ref.update({'gender': update.message.text})
    await update.message.reply_text('သင့်ရဲ့အသက်ကိုအတိအကျ(မှန်မှန်ကန်ကန်)ထည့်ပေးပါ.')
    return AGE

# Age handler
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    ref = db.reference(f'users/{user_id}')
    ref.update({'age': update.message.text})
    await update.message.reply_text('သင့်ကိုသင်အလှဆုံးပါလို့ထင်ရသောသင့်ရဲ့မျက်နှာပါသောပုံတစ်ပုံပို့ပေးပါ။')
    return PHOTO

# Photo handler
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f'{user_id}.jpg'
    await photo_file.download(photo_path)
    ref = db.reference(f'users/{user_id}')
    ref.update({'photo': photo_path})
    await update.message.reply_text('ကျွန်တော့်ဆီမှာသင့်ရဲ့ Profile ကိုသိမ်းထားလိုက်ပါပြီ။ကောင်မလေး(သို့)ကောင်‌ေလးရှာရန် /search ဟုပို့ပါ')
    return ConversationHandler.END

#Username handle 


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
        await update.message.reply_text('သင့်အတွက်ရှာမတွေ့သေးပါ။ကျွန်တော့်ဆီမှာလာရှာခိုင်းတဲ့လူတိုင်းအတွဲကိုယ်ဆီရသွားကြပါပြီ။အတွဲမဖြစ်သေးသူမရှိသေးပါ။နောက်ထပ်ကျွန်တော့်ကိုသုံးမယ့် User အသစ်များထပ်တိုးလာအောင် Share ပေးပါ။သို့မှသာ Single များထပ်တိုးလာမှာဖြစ်ပြီးသင့်အတွက်ရှာဖွေချိတ်ဆက်ပေးနိုင်မှာပါ။ကျေးဇူးပါ🥰')
        return ConversationHandler.END

    partner_id = context.user_data['partners'].pop()
    partner_profile = db.reference(f'users/{partner_id}').get()

    await update.message.reply_photo(
        photo=open(partner_profile['username'],['photo'], 'rb'),
        caption=f"Age: {partner_profile['age']}\nသူ့ကိုသဘောကျပါသလား???",
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

        await context.bot.send_message(partner_id, f"သင့်အတွက် Partner ချိတ်ပေးလိုက်ပါပြီ: {update.message.from_user.username}")
        await update.message.reply_text(f"သင့်အတွက် {partner_id} နှင့်ချိတ်ဆက်ပေးလိုက်ပါပြီ။အပြန်အလှန်စကားပြောလို့ရပါပြီ။ကျေးဇူးပါ။🥰")
        return ConversationHandler.END
    else:
        return await show_partner(update, context)

# Disconnect command handler
async def disconnect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    matches_ref = db.reference(f'matches/{user_id}')
    matches = matches_ref.get()

    if not matches:
        await update.message.reply_text('သင့်ဆန္ဒအတိုင်းချိတ်ဆက်မှုကိုပြန်ဖြုတ်လိုက်ပါပြီ')
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

    await update.message.reply_text(f'သင့်နှင့်ချိတ်ဆက်ထားသော {partner_id}  ကချိတ်ဆက်မှုကိုဖြုတ်လိုက်ပါပြီ')
    await context.bot.send_message(partner_id, f'ချိတ်ဆက်မှုရပ်တန့်လိုက်ပါပြီ {update.message.from_user.username}')
    return ConversationHandler.END

def main() -> None:
    application = ApplicationBuilder().token('YOUR_BOT_API_TOKEN').build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'GENDER': [MessageHandler(filters.TEXT & ~filters.COMMAND, gender)],
            'AGE': [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            'PHOTO': [MessageHandler(filters.PHOTO & ~filters.COMMAND, photo)],
            'SEARCH': [CommandHandler('search', search)],
            'CONNECT': [MessageHandler(filters.TEXT & ~filters.COMMAND, connect)],
            'DISCONNECT': [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_disconnect)],
            'USERNAME': [MessageHandler(filters.TEXT & ~filters.COMMAND, username)]
},
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('disconnect', disconnect))
    application.run_polling()

if __name__ == '__main__':
    main()
