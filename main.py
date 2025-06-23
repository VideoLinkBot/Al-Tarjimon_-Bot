import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from googletrans import Translator

# Environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Tarjima tarixi uchun dictionary
user_history = {}

translator = Translator()

# Kerakli 15 ta asosiy tillar
LANGUAGES = {
    'English': 'en',
    'Russian': 'ru',
    'Uzbek': 'uz',
    'Korean': 'ko',
    'French': 'fr',
    'German': 'de',
    'Chinese': 'zh-cn',
    'Japanese': 'ja',
    'Spanish': 'es',
    'Arabic': 'ar',
    'Turkish': 'tr',
    'Italian': 'it',
    'Hindi': 'hi',
    'Kazakh': 'kk',
    'Kyrgyz': 'ky'
}

keyboard = ReplyKeyboardMarkup(
    [[lang for lang in list(LANGUAGES.keys())[:5]],
     [lang for lang in list(LANGUAGES.keys())[5:10]],
     [lang for lang in list(LANGUAGES.keys())[10:]]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tilni tanlang yoki Auto detect rejimda matn yuboring:", reply_markup=keyboard)

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    # Tarjima tarixini tekshirish va yaratish
    if user_id not in user_history:
        user_history[user_id] = []

    # Auto detect rejimi
    if user_text not in LANGUAGES:
        detected = translator.detect(user_text)
        src_lang = detected.lang

        dest_lang = 'en'  # default target: English
        if src_lang == 'en':
            dest_lang = 'uz'  # Ingliz bo‘lsa, o‘zbekka

        translation = translator.translate(user_text, src=src_lang, dest=dest_lang)

        # Tarixga yozish
        user_history[user_id].append({'input': user_text, 'output': translation.text})

        await update.message.reply_text(f"Auto detect:\n{src_lang} -> {dest_lang}\nNatija: {translation.text}")

    # Foydalanuvchi til tanlagan bo‘lsa
    elif user_text in LANGUAGES:
        context.user_data['target_lang'] = LANGUAGES[user_text]
        await update.message.reply_text(f"Target language set to: {user_text}. Endi tarjima qilmoqchi bo‘lgan matningizni yuboring.")

    # Foydalanuvchi matn yuborgan bo‘lsa
    elif 'target_lang' in context.user_data:
        target_lang = context.user_data['target_lang']
        detected = translator.detect(user_text)
        src_lang = detected.lang

        translation = translator.translate(user_text, src=src_lang, dest=target_lang)
        user_history[user_id].append({'input': user_text, 'output': translation.text})

        await update.message.reply_text(f"Auto detect:\n{src_lang} -> {target_lang}\nNatija: {translation.text}")

    else:
        await update.message.reply_text("Iltimos til tanlang yoki matn yuboring.")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    history_list = user_history.get(user_id, [])

    if not history_list:
        await update.message.reply_text("Sizda tarix yo‘q.")
    else:
        text = "\n\n".join([f"👤 {h['input']} \n➡️ {h['output']}" for h in history_list[-5:]])
        await update.message.reply_text(f"Oxirgi tarjimalar:\n{text}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
