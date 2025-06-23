import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from deep_translator import GoogleTranslator

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Tanlangan tilni saqlash uchun (foydalanuvchi uchun)
user_lang = {}

# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Ingliz tili 🇬🇧", callback_data='en')],
        [InlineKeyboardButton("Rus tili 🇷🇺", callback_data='ru')],
        [InlineKeyboardButton("Koreys tili 🇰🇷", callback_data='ko')],
        [InlineKeyboardButton("Fransuz tili 🇫🇷", callback_data='fr')],
        [InlineKeyboardButton("Nemis tili 🇩🇪", callback_data='de')],
        [InlineKeyboardButton("Italya tili 🇮🇹", callback_data='it')],
        [InlineKeyboardButton("Yapon tili 🇯🇵", callback_data='ja')],
        [InlineKeyboardButton("Xitoy tili 🇨🇳", callback_data='zh-CN')],
        [InlineKeyboardButton("Ispan tili 🇪🇸", callback_data='es')],
        [InlineKeyboardButton("Arab tili 🇸🇦", callback_data='ar')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Tarjima tilini tanlang:', reply_markup=reply_markup)

# Tugma bosilganda
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_lang[query.from_user.id] = query.data
    await query.edit_message_text(text=f"Tanlangan til kodi: {query.data}. Endi xabar yuboring.")

# Matn kelganda
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    target_lang = user_lang.get(user_id)

    if not target_lang:
        await update.message.reply_text("Iltimos, /start buyrug'ini bosib til tanlang.")
        return

    text = update.message.text
    translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
    await update.message.reply_text(f"Tarjima: {translated}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    app.run_polling()

if __name__ == '__main__':
    main()
