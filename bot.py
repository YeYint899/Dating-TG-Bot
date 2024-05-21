import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import firebase_admin
from firebase_admin import credentials, firestore

API_TOKEN = 'Your_TG_Bot_Token'
bot = telebot.TeleBot(API_TOKEN)

# Firebase Admin SDK Initialization
cred = credentials.Certificate("/home/Your_file&location/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

users_collection = db.collection('users')
pairs_collection = db.collection('pairs')

# Define gender options
g_options = ["male", "female"]

# Create inline keyboard for gender selection
def create_g_keyboard():
    g_buttons = [InlineKeyboardButton(text=gender, callback_data=gender) for gender in g_options]
    g_markup = InlineKeyboardMarkup()
    g_markup.add(*g_buttons)
    return g_markup

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Dating 🇲🇲 Bot မှကြိုဆိုပါတယ်။သင်ဟာယောက်ျားလားမိန်းမလားဆိုတာသေချာရွေးချယ်ပေးပါ။‌ေစာက်တလွဲမလုပ်ပါနဲ့🙂", reply_markup=create_g_keyboard())

# Handle callback query from gender selection
@bot.callback_query_handler(func=lambda call: call.data in g_options)
def g_selection(call):
    user_id = call.from_user.id
    username = call.from_user.username
    selected_g = call.data

    # Update user's gender in the database
    user_ref = users_collection.document(str(user_id))
    user_ref.set({'username': username, 'gender': selected_g, 'status': 'looking'}, merge=True)
    bot.send_message(user_id, f"သင်၏လိင်အမျိုးအစားမှာ {selected_g} ဖြစ်ပါသည်။", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ရှေ့ဆက်သွားမယ်", callback_data="Next")))



 # Define age options
age_options = [
    "18", "19", "20", "21", "22", "23", "24", "25",
    "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40","41"
]

# Create inline keyboard for age selection
def create_age_keyboard():
    age_buttons = [InlineKeyboardButton(text=age, callback_data=age) for age in age_options]
    age_markup = InlineKeyboardMarkup()
    age_markup.add(*age_buttons)
    return age_markup

# Handle age input
@bot.callback_query_handler(func=lambda call: call.data.startswith("Next"))
def set_age(call):
    bot.send_message(call.message.chat.id, "သင့်ရဲ့အသက်အမှန်ကိုရွေးပေးပါ🙄🙄🙄(မှန်မှန်ကန်ကန်ရွေး၊စောက်တလွဲလုပ်လို့ရည်းစားမရရင်ငါ့အပစ်မဟုတ်ဘူးနော်🙂)။အသက်မပြည့်တာတို့‌ေကျာ်‌ေနတာတို့ဆိုရင်‌ေတာ့  ‌ေဂျာင်းးးး🤨😎", reply_markup=create_age_keyboard())

# Handle callback query from age selection
@bot.callback_query_handler(func=lambda call: call.data in age_options)
def process_age_selection(call):
    user_id = call.from_user.id
    selected_age = call.data

    # Update user's age in the database (you can replace this with your own logic)
    user_ref = users_collection.document(str(user_id))
    if user_ref.get().exists:
        user_ref.update({'age': int(selected_age)})
        bot.send_message(user_id, f"သင့်အသက်ကို {selected_age} အဖြစ်သတ်မှတ်ပြီးပါပြီ။အမှန်မဟုတ်ဘူးဆိုတာသိခဲ့ရင်banပစ်မယ်🙄🙂။", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ရှေ့ဆက်သွားမယ်", callback_data="pp")))
    else:
        bot.send_message(user_id, "Please start with /start command and set your gender.")


# Handle set profile picture
@bot.callback_query_handler(func=lambda call: call.data.startswith("pp"))
def set_profile_picture(call):
    user_id = call.message.chat.id

    try:
        # Get user profile photos
        profile_photos = bot.get_user_profile_photos(user_id)

        if profile_photos.total_count > 0:
            # Get the most recent profile photo
            photo = profile_photos.photos[0][-1]

            user_ref = users_collection.document(str(user_id))

            if user_ref.get().exists:
                user_ref.update({'profile_picture': photo.file_id})

                bot.send_message(call.message.chat.id, "သင် Acc မှ Profile Photo ကိုယူလိုက်ပါပြီ🤭။ ⬇️⬇️  ‌ေအာက်ကခလုပ်‌ေလးနှိပ်ပြီး ️⬇️⬇️သင့်တွက်partnerကိုရှာဖွေလိုက်ပါ🤭။", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ကဲဒီကိုနှိပ်၍လက်တွဲဖော်(partner)ကိုစရှာလို့ရပါပြီ", callback_data="find_pt")))
            else:
                bot.send_message(call.message.chat.id, "Please start with /start command and set your gender.")
        else:
            bot.send_message(user_id, "Profile ပုံတောင်တင်မထားရင်မလာနဲ့။နွား။‌ေစာက်‌ေတာသား🥲။ဒီပုံစံတိုင်းဆိုတစ်သက်လုံးရည်စားရမှာမဟုတ်ဘူး။စောက်ရူး😝")
    except Exception as e:
        bot.send_message(user_id, "An error occurred: {}".format(str(e)))


# Handle button press to find a partner
@bot.callback_query_handler(func=lambda call: call.data.startswith("find_pt"))
def find_partner(call):
    user_id = call.message.chat.id
    user_doc = users_collection.document(str(user_id)).get()
    if not user_doc.exists:
        bot.send_message(user_id, "ကြာတယ်ကွာပြန်စလိုက်🙂 /start ကိုပြန်နှိပ်👍")
        return

    user_data = user_doc.to_dict()
    gender = user_data['gender']
    opposite_gender = 'female' if gender == 'male' else 'male'

    # Find potential partners
    potential_partners = users_collection.where('gender', '==', opposite_gender).where('status', '==', 'looking').stream()
    partners_list = [
        partner for partner in potential_partners
        if partner.id != str(user_id)
    ]

    if partners_list:
        for partner in partners_list:
            partner_data = partner.to_dict()
            partner_id = partner.id
            partner_username = partner_data['username']
            partner_age = partner_data.get('age', 'Unknown')
            partner_profile_pic = partner_data.get('profile_picture')

            caption = f"{partner_username}, age {partner_age}"
            callback_data = f"select_partner:{partner_id}"

            if partner_profile_pic:
                bot.send_photo(user_id, partner_profile_pic, caption=caption, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ကြိုက်ရင်ဒီကိုနှိပ်", callback_data=callback_data)))
            else:
                bot.send_message(user_id, caption, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ကြိုက်ရင်ဒီကိုနှိပ်", callback_data=callback_data)))

    else:
        bot.send_message(user_id, "ငါ့ဆီမှာ Single တွေမရှိသေးပါဘူး။ရှိပြီးသားလူတွေကငါချိတ်ပေးထားလို့အစဉ်ပြေနေသူတွေချည်းပါပဲ။အဲ့တာကြောင့်သင့်အတွက်ချိတ်ဆက်ပေးဖို့ Singleမရှိတော့ပါ။ ဒီ Bot ကိုလူများများထပ်လာသုံးအောင် share ပေးပါ။ဒါမှလူသစ်တွေဝင်လာရင်သင့်အတွက်ချည်းပဲမို့ရဲရဲသာ Shareလိုက်။Singleအသစ်များထပ်ဝင်ရောက်လာရင်သင့်ဆီအကြောင်းကြားပါ့မယ်။ကျေးဇူးတင်ပါတယ်🥰")

# Handle partner selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_partner:"))
def select_partner(call):
    user_id = call.from_user.id
    partner_id = call.data.split(":")[1]

    user_ref = users_collection.document(str(user_id))
    partner_ref = users_collection.document(str(partner_id))

    user_data = user_ref.get().to_dict()
    partner_data = partner_ref.get().to_dict()

    user_ref.update({'status': 'paired'})
    partner_ref.update({'status': 'paired'})

    pairs_collection.add({'user_id': user_id, 'partner_id': partner_id})
    pairs_collection.add({'user_id': partner_id, 'partner_id': user_id})

    bot.send_message(user_id, f"သင်သဘောကျ၍ရွေးချယ်လိုက်သူနှင့်ချိတ်ဆက်ပေးလိုက်ပါပြီ {partner_data['username']}, age {partner_data['age']}! နှင့်စကားပြောလို့ရပါပြီ။ခုသင်စာတစ်‌ေကြာင်းပို့လျှင်သင်နှင့်ချိတ်ဆက်ထားသူဆီ‌ေရာက်ပါလိမ့်မည်။Hi,စားpplလောက်ပဲတတ်တယ်ဆိုရင်တော့ကျွန်တော်ချိတ်ပေးတာကအကျိုးမရှိသလိုဖြစ်နေပါလိမ့်မယ်🥲")
    bot.send_message(partner_id, f"သင့်ကိုသဘောကျနေသူနှင့်ချိတ်ဆက်လိုက်ပါပြီ {user_data['username']}, age {user_data['age']}! နှင့်စကားပြောလို့ရပါပြီ။ခုသင်စာတစ်‌ေကြာင်းပို့လျှင်သင်နှင့်ချိတ်ဆက်ထားသူဆီ‌ေရာက်ပါလိမ့်မည်။Hi,စားpplလောက်ပဲတတ်တယ်ဆိုရင်တော့ကျွန်တော်ချိတ်ပေးတာကအကျိုးမရှိသလိုဖြစ်နေပါလိမ့်မယ်🥲")

    if partner_data.get('profile_picture'):
        bot.send_photo(user_id, partner_data['profile_picture'], caption=f"သင်သဘောကျ၍ရွေးချယ်လိုက်သူနှင့်ချိတ်ဆက်ပေးလိုက်ပါပြီ{partner_data['username']}, age {partner_data['age']}! နှင့်စကားပြောလို့ရပါပြီ။ခုသင်စာတစ်‌ေကြာင်းပို့လျှင်သင်နှင့်ချိတ်ဆက်ထားသူဆီ‌ေရာက်ပါလိမ့်မည်။Hi,စားpplလောက်ပဲတတ်တယ်ဆိုရင်တော့ကျွန်တော်ချိတ်ပေးတာကအကျိုးမရှိသလိုဖြစ်နေပါလိမ့်မယ်🥲")
        bot.send_photo(partner_id, user_data['profile_picture'], caption=f"သင့်ကိုသဘောကျနေသူနှင့်ချိတ်ဆက်လိုက်ပါပြီ  {user_data['username']}, age {user_data['age']}! နှင့်စကားပြောလို့ရပါပြီ။ခုသင်စာတစ်‌ေကြာင်းပို့လျှင်သင်နှင့်ချိတ်ဆက်ထားသူဆီ‌ေရာက်ပါလိမ့်မည်။Hi,စားpplလောက်ပဲတတ်တယ်ဆိုရင်တော့ကျွန်တော်ချိတ်ပေးတာကအကျိုးမရှိသလိုဖြစ်နေပါလိမ့်မယ်🥲")
    else:
        bot.send_message(user_id, f"သင်သဘောကျ၍ရွေးချယ်လိုက်သူနှင့်ချိတ်ဆက်ပေးလိုက်ပါပြီ {partner_data['username']}, age {partner_data['age']}! နှင့်စကားပြောလို့ရပါပြီ။ခုသင်စာတစ်‌ေကြာင်းပို့လျှင်သင်နှင့်ချိတ်ဆက်ထားသူဆီ‌ေရာက်ပါလိမ့်မည်။Hi,စားpplလောက်ပဲတတ်တယ်ဆိုရင်တော့ကျွန်တော်ချိတ်ပေးတာကအကျိုးမရှိသလိုဖြစ်နေပါလိမ့်မယ်🥲")
        bot.send_message(partner_id, f"သင့်ကိုသဘောကျနေသူနှင့်ချိတ်ဆက်လိုက်ပါပြီ  {user_data['username']}, age {user_data['age']}! နှင့်စကားပြောလို့ရပါပြီ။ခုသင်စာတစ်‌ေကြာင်းပို့လျှင်သင်နှင့်ချိတ်ဆက်ထားသူဆီ‌ေရာက်ပါလိမ့်မည်။Hi,စားpplလောက်ပဲတတ်တယ်ဆိုရင်တော့ကျွန်တော်ချိတ်ပေးတာကအကျိုးမရှိသလိုဖြစ်နေပါလိမ့်မယ်🥲")

# Message forwarding
@bot.message_handler(func=lambda message: any(pair.get().exists for pair in pairs_collection.where('user_id', '==', message.chat.id).stream()))
def forward_message(message):
    pairs = pairs_collection.where('user_id', '==', message.chat.id).stream()
    for pair in pairs:
        partner_id = pair.to_dict()['partner_id']
        bot.send_message(partner_id, f"{message.from_user.username}: {message.text}")

# Unpairing command
@bot.message_handler(commands=['stop'])
def unpair(message):
    user_id = message.chat.id

#user is looking status
    user_doc = users_collection.document(str(user_id)).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        status = user_data.get('status', 'looking')
        if status == 'looking':
            bot.send_message(user_id, "စောက်ပေါ၊ဘာတွေလျှောက်နှိပ်၊မြန်မာလိုရေးပေးထားတယ်၊သေချာဖတ်၊ Partner မချိတ်ရသေးပဲလျှောက်နှိပ်မနေနဲ့၊စောက်ရူး၊ရည်းစားမရတာလဲမပြောနဲ့🤭🤭🤭။မသိရင် /help လို့ရိုက်လိုက်။‌ေတာသား🥲")
            return

#user is pairing status
    pairs = pairs_collection.where('user_id', '==', user_id).stream()
    for pair in pairs:
        partner_id = pair.to_dict()['partner_id']
        bot.send_message(user_id, "သင်တို့ရဲ့ချိတ်ဆက်မှုကိုဖြုတ်လိုက်ပါပြီ🥲။ကျေးဇူးပါ")
        bot.send_message(partner_id, "ချိတ်ဆက်မှုဖြုတ်သွားပါပြီ။🙂သင့်ရဲ့ Partner သည်စကားပြောသည့်နေရာမှထွက်ခွာသွားပါပြီ။🥲ကျေးဇူးတင်ပါတယ်။")

        pairs_collection.document(pair.id).delete()
        partner_pair = pairs_collection.where('user_id', '==', partner_id).get()
        if partner_pair:
            partner_pair[0].reference.delete()

    users_collection.document(str(user_id)).update({'status': 'looking'})
    users_collection.document(str(partner_id)).update({'status': 'looking'})

# Help command
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "**🌟Help Information🌟**\n\n"
        "- /start ဖြင့် Botကိုစတင်နိုင်သလို့၊အသံုးပြု‌ေနရင်းအစကပြန်စချင်တဲ့အခါမျိုးမှာလဲသံုးလို့ရပါတယ်။\n\n"
        "-  /stop ကိုတော့Botမှချိတ်ဆက်‌ေပးတဲ့ partner ကိုပြန်ဖြုတ်ချင်တဲ့အခါမှာသုံးရမှာပါ။မချိတ်ထားပဲသံုးလို့မရပါဘူး။\n\n\n"
        "-  /about ကတော့ဒီ Bot ကိုဖန်တီးလိုက်တဲ့ Creator ရဲ့အသေးစိတ်အချက်အလက်တွေကိုသိချင်တဲ့အခါသံုးလို့ရပါတယ်။Bot ကိုသုံးနေရင်းError‌ေတွ့ခဲ့ရင်လဲဆက်သွယ်ပြီးပြုပြင်ဖို့‌ေပြာလို့ရတာ‌ေပါ့။\n\n"
        "👉👉👉အရာအားလံုးအလကားအသံုးပြုခွင့်‌ေပးထားပါတယ်။နောက်ထပ်အကူအညီလိုရင် ဆက်သွယ်လိုက်ပါ👈👈👈။"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# About Developer command
@bot.message_handler(commands=['about'])
def send_about_developer(message):
    about_text = (
        "**🤍About the Developer🤍** \n\n\n\n"
        "This bot was developed by [Ye Yint], a passionate developer\n\n "
        "who loves creating innovative solutions. For more information or "
        "to contact the developer,\n\n visit [https://yeyint899.github.io/YeYint899/].🤍"
    )
    # Replace [Your Name], [Your Website], and [Your Email] with your actual details.
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')

# Make sure to include these handlers before the bot.polling() line.


bot.polling()

                         
