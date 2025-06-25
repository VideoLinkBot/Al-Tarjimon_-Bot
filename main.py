import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator
from PIL import Image
import pytesseract
from io import BytesIO

# Yuklash
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Admin uchun Telegram ID
ADMIN_ID = 6905227976

# Tarix va statistika
user_history = {}
user_stats = {}

# Til sozlamalari
LANGUAGES = {
    'English': 'en', 'Russian': 'ru', 'Uzbek': 'uz', 'Korean': 'ko', 'French': 'fr',
    'German': 'de', 'Chinese': 'zh', 'Japanese': 'ja', 'Spanish': 'es', 'Arabic': 'ar',
    'Turkish': 'tr', 'Italian': 'it', 'Hindi': 'hi', 'Kazakh': 'kk', 'Kyrgyz': 'ky'
}

main_keyboard = ReplyKeyboardMarkup(
    [
        ['🌍 Til tanlash', '🔄 Auto Detect'],
        ['📖 Tarjima tarixi', '🗑 Tarixni tozalash'],
        ['📊 Statistika']
    ],
    resize_keyboard=True
)

lang_keyboard = ReplyKeyboardMarkup(
    [[lang] for lang in LANGUAGES.keys()],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tilni tanlang yoki Auto detect rejimda matn yuboring:", reply_markup=main_keyboard)

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text

    user_stats[user_id] = user_stats.get(user_id, 0)

    if user_id not in user_history:
        user_history[user_id] = []

    if user_text == '🌍 Til tanlash':
        await update.message.reply_text("Quyidan tilni tanlang:", reply_markup=lang_keyboard)
        return

    if user_text in LANGUAGES:
        context.user_data['target_lang'] = LANGUAGES[user_text]
        await update.message.reply_text(
            f"{user_text} tili tanlandi. Endi matn yuboring.",
            reply_markup=main_keyboard
        )
        return

    if user_text == '🔄 Auto Detect':
        context.user_data['target_lang'] = 'en'
        await update.message.reply_text("Auto detect tanlandi. Endi matn yuboring.", reply_markup=main_keyboard)
        return

    if user_text == '📖 Tarjima tarixi':
        history_list = user_history.get(user_id, [])
        if not history_list:
            await update.message.reply_text("Sizda tarix yo‘q.", reply_markup=main_keyboard)
        else:
            text = "\n\n".join([f"👤 {h['input']} \n➡️ {h['output']}" for h in history_list[-5:]])
            await update.message.reply_text(f"Oxirgi tarjimalar:\n{text}", reply_markup=main_keyboard)
        return

    if user_text == '🗑 Tarixni tozalash':
        user_history[user_id] = []
        await update.message.reply_text("Tarix tozalandi.", reply_markup=main_keyboard)
        return

    if user_text == '📊 Statistika':
        if user_id == ADMIN_ID:
            total_users = len(user_stats)
            total_translations = sum(user_stats.values())
            await update.message.reply_text(
                f"📊 Statistika:\n👥 Foydalanuvchilar: {total_users}\n🔤 Tarjimalar soni: {total_translations}",
                reply_markup=main_keyboard
            )
        else:
            await update.message.reply_text("Ushbu bo‘lim faqat admin uchun.", reply_markup=main_keyboard)
        return

    # Tarjima qilish
    target_lang = context.user_data.get('target_lang', 'en')
    try:
        result = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        user_history[user_id].append({'input': user_text, 'output': result})
        user_stats[user_id] += 1
        await update.message.reply_text(f"Tarjima ({target_lang}): {result}", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}", reply_markup=main_keyboard)

# 📸 RASMNI MATNGA AYLANTRUVCHI FUNKSIYA
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()

    image = Image.open(BytesIO(photo_bytes))

    try:
        text = pytesseract.image_to_string(image, lang='eng+rus+uzb')
        if text.strip():
            user_stats[user_id] = user_stats.get(user_id, 0) + 1
            user_history[user_id] = user_history.get(user_id, []) + [{'input': '📷Rasm', 'output': text}]
            await update.message.reply_text(f"📄 Rasmdagi matn:\n{text}", reply_markup=main_keyboard)
        else:
            await update.message.reply_text("❌ Rasmda matn topilmadi.", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {e}", reply_markup=main_keyboard)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
