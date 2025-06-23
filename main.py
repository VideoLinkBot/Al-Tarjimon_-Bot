import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

# .env fayldan token olish
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Tarjima tarixi
user_history = {}

# Til kodi ro‘yxati
LANGUAGES = {
    'English': 'en',
    'Russian': 'ru',
    'Uzbek': 'uz',
    'Korean': 'ko',
    'French': 'fr',
    'German': 'de',
    'Chinese': 'zh',
    'Japanese': 'ja',
    'Spanish': 'es',
    'Arabic': 'ar',
    'Turkish': 'tr',
    'Italian': 'it',
    'Hindi': 'hi',
    'Kazakh': 'kk',
    'Kyrgyz': 'ky'
}

# Asosiy menyu tugmalari
main_keyboard = ReplyKeyboardMarkup(
    [
        ['🌍 Til tanlash', '🔄 Auto Detect'],
        ['📖 Tarjima tarixi', '🗑 Tarixni tozalash']
    ],
    resize_keyboard=True
)

# Til tanlash menyusi
language_keyboard = ReplyKeyboardMarkup(
    [
        [lang for lang in list(LANGUAGES.keys())[:5]],
        [lang for lang in list(LANGUAGES.keys())[5:10]],
        [lang for lang in list(LANGUAGES.keys())[10:]]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xush kelibsiz! Quyidagilardan birini tanlang:", 
        reply_markup=main_keyboard
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    if user_id not in user_history:
        user_history[user_id] = []

    # Asosiy menyu tanlovi
    if user_text == '🌍 Til tanlash':
        await update.message.reply_text("Tilni tanlang:", reply_markup=language_keyboard)
        return

    if user_text == '🔄 Auto Detect':
        context.user_data['target_lang'] = 'en'
        await update.message.reply_text("Auto detect rejimi tanlandi. Endi matn yuboring.")
        return

    if user_text == '📖 Tarjima tarixi':
        await history(update, context)
        return

    if user_text == '🗑 Tarixni tozalash':
        user_history[user_id] = []
        await update.message.reply_text("Tarix tozalandi.")
        return

    # Til tanlangan bo‘lsa
    if user_text in LANGUAGES:
        context.user_data['target_lang'] = LANGUAGES[user_text]
        await update.message.reply_text(f"Target til: {user_text}. Endi matn yuboring.")
        return

    # Matn tarjima qilish
    target_lang = context.user_data.get('target_lang', 'en')
    try:
        result = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        user_history[user_id].append({'input': user_text, 'output': result})
        await update.message.reply_text(f"Tarjima ({target_lang}): {result}")
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    history_list = user_history.get(user_id, [])

    if not history_list:
        await update.message.reply_text("Sizda tarjima tarixi yo‘q.")
    else:
        text = "\n\n".join([f"👤 {h['input']} \n➡️ {h['output']}" for h in history_list[-5:]])
        await update.message.reply_text(f"Oxirgi tarjimalar:\n{text}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
