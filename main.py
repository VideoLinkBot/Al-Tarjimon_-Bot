import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from googletrans import Translator

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

translator = Translator()

SUPPORTED_LANGUAGES = ['uz', 'ru', 'en', 'ko', 'de', 'fr', 'es', 'tr', 'ar', 'zh-cn']

def choose_target_lang(detected_lang):
    for lang in SUPPORTED_LANGUAGES:
        if lang != detected_lang:
            return lang
    return 'en'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Matn yuboring va men uni tarjima qilaman.")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    detection = translator.detect(text)
    detected_lang = detection.lang

    if detected_lang not in SUPPORTED_LANGUAGES:
        await update.message.reply_text("Kechirasiz, bu til hozircha qo'llab-quvvatlanmaydi.")
        return

    target_lang = choose_target_lang(detected_lang)
    translated = translator.translate(text, dest=target_lang)

    response = (f"🔍 Aniqlangan til: {detected_lang}\n"
                f"🎯 Tarjima ({target_lang}): {translated.text}")
    await update.message.reply_text(response)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
