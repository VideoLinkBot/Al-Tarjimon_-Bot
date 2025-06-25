import os
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OCR_API_KEY = os.getenv('OCR_API_KEY')
ADMIN_ID = 6905227976  # Sizning Telegram ID'ingiz

# Tarjima tarixi va statistika
user_history = {}
user_stats = {}

# Tillar
LANGUAGES = {
    'English': 'en', 'Russian': 'ru', 'Uzbek': 'uz', 'Korean': 'ko',
    'French': 'fr', 'German': 'de', 'Chinese': 'zh', 'Japanese': 'ja',
    'Spanish': 'es', 'Arabic': 'ar', 'Turkish': 'tr', 'Italian': 'it',
    'Hindi': 'hi', 'Kazakh': 'kk', 'Kyrgyz': 'ky'
}

# Tugmalar
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

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Tilni tanlang yoki Auto detect rejimda matn yuboring:",
        reply_markup=main_keyboard
    )

# Matnli xabarlar bilan ishlash
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
        await update.message.reply_text(f"{user_text} tili tanlandi. Endi matn yuboring.", reply_markup=main_keyboard)
        return

    if user_text == '🔄 Auto Detect':
        context.user_data['target_lang'] = 'en'
        await update.message.reply_text("Auto detect tanlandi. Matn yuboring.", reply_markup=main_keyboard)
        return

    if user_text == '📖 Tarjima tarixi':
        history = user_history.get(user_id, [])
        if not history:
            await update.message.reply_text("Sizda tarix yo‘q.", reply_markup=main_keyboard)
        else:
            text = "\n\n".join([f"👤 {h['input']}\n➡️ {h['output']}" for h in history[-5:]])
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
                f"📊 Statistika:\n👥 Foydalanuvchilar: {total_users}\n🔤 Tarjimalar: {total_translations}",
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

# 🖼 OCR: Rasm orqali matn o‘qish va tarjima
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    target_lang = context.user_data.get('target_lang', 'en')

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_url = file.file_path

    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            data={"apikey": OCR_API_KEY, "url": image_url, "language": "eng"}
        )
        result = response.json()
        text = result['ParsedResults'][0]['ParsedText']

        if not text.strip():
            await update.message.reply_text("❌ Rasmda matn topilmadi.")
            return

        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        await update.message.reply_text(f"📷 Matn:\n{text}\n\n🔤 Tarjima:\n{translated}")

    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}")

# Botni ishga tushirish
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
