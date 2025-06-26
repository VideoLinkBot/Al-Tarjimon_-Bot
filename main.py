import os
import requests
import fitz  # PyMuPDF
from uuid import uuid4
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, InlineQueryHandler
)
from deep_translator import GoogleTranslator

# .env dan tokenlar
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OCR_API_KEY = os.getenv("OCR_API_KEY")  # OCR.space API kaliti
ADMIN_ID = 6905227976  # Sizning Telegram ID’ingiz

# Tarjima tillari
LANGUAGES = {
    'English': 'en', 'Russian': 'ru', 'Uzbek': 'uz', 'Korean': 'ko', 'French': 'fr',
    'German': 'de', 'Chinese': 'zh', 'Japanese': 'ja', 'Spanish': 'es', 'Arabic': 'ar',
    'Turkish': 'tr', 'Italian': 'it', 'Hindi': 'hi', 'Kazakh': 'kk', 'Kyrgyz': 'ky'
}

# Tarix va statistika
user_history = {}
user_stats = {}

# Tugmalar
main_keyboard = ReplyKeyboardMarkup(
    [
        ['🌍 Til tanlash', '🔄 Auto Detect'],
        ['📖 Tarjima tarixi', '🗑 Tarixni tozalash'],
        ['📊 Statistika', '📄 PDF tarjima qilish']
    ],
    resize_keyboard=True
)

lang_keyboard = ReplyKeyboardMarkup(
    [[lang] for lang in LANGUAGES.keys()],
    resize_keyboard=True
)

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tilni tanlang yoki matn yuboring:", reply_markup=main_keyboard)

# Matndan matnga tarjima
async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    user_stats[user_id] = user_stats.get(user_id, 0)
    user_history.setdefault(user_id, [])

    if user_text == '🌍 Til tanlash':
        await update.message.reply_text("Tilni tanlang:", reply_markup=lang_keyboard)
        return

    if user_text in LANGUAGES:
        context.user_data['target_lang'] = LANGUAGES[user_text]
        await update.message.reply_text(f"{user_text} tili tanlandi. Endi matn yuboring.", reply_markup=main_keyboard)
        return

    if user_text == '🔄 Auto Detect':
        context.user_data['target_lang'] = 'en'
        await update.message.reply_text("Auto detect tanlandi. Endi matn yuboring.", reply_markup=main_keyboard)
        return

    if user_text == '📖 Tarjima tarixi':
        history_list = user_history[user_id]
        if not history_list:
            await update.message.reply_text("Tarjima tarixi yo‘q.", reply_markup=main_keyboard)
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
            await update.message.reply_text(
                f"📊 Statistika:\n👥 Foydalanuvchilar: {len(user_stats)}\n🔤 Tarjimalar soni: {sum(user_stats.values())}",
                reply_markup=main_keyboard
            )
        else:
            await update.message.reply_text("Ushbu bo‘lim faqat admin uchun.", reply_markup=main_keyboard)
        return

    if user_text == '📄 PDF tarjima qilish':
        await update.message.reply_text("📄 Iltimos, tarjima qilmoqchi bo‘lgan PDF faylni yuboring.", reply_markup=main_keyboard)
        return

    target_lang = context.user_data.get('target_lang', 'en')
    try:
        result = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        user_history[user_id].append({'input': user_text, 'output': result})
        user_stats[user_id] += 1
        await update.message.reply_text(f"Tarjima ({target_lang}): {result}", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}", reply_markup=main_keyboard)

# 📷 OCR – rasm matnini tarjima qilish
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"{file.file_unique_id}.jpg"
    await file.download_to_drive(file_path)

    with open(file_path, 'rb') as img:
        files = {'file': img}
        data = {"apikey": OCR_API_KEY, "language": "eng"}
        response = requests.post("https://api.ocr.space/parse/image", files=files, data=data)

    try:
        result = response.json()
        text = result['ParsedResults'][0]['ParsedText']
        target_lang = context.user_data.get('target_lang', 'en')
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        user_stats[user_id] += 1
        user_history.setdefault(user_id, []).append({'input': text, 'output': translated})
        await update.message.reply_text(f"📷 Rasm matni:\n{text}\n\n🔁 Tarjima ({target_lang}):\n{translated}", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"❌ OCR yoki tarjima xatosi: {e}", reply_markup=main_keyboard)

# 📄 PDF fayldan matn o‘qib tarjima qilish
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    document = update.message.document

    if not document.file_name.endswith(".pdf"):
        await update.message.reply_text("❌ Faqat PDF faylni yuboring.")
        return

    file = await document.get_file()
    file_path = f"{file.file_unique_id}.pdf"
    await file.download_to_drive(file_path)

    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()

        if not text.strip():
            await update.message.reply_text("⚠️ PDF faylda matn topilmadi.")
            return

        target_lang = context.user_data.get('target_lang', 'en')
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text[:5000])

        user_stats[user_id] = user_stats.get(user_id, 0) + 1
        user_history.setdefault(user_id, []).append({'input': '[PDF]', 'output': translated})

        await update.message.reply_text(f"📄 PDF tarjimasi ({target_lang}):\n{translated[:4000]}", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"❌ PDF tarjima xatosi: {e}", reply_markup=main_keyboard)

# 🔍 Inline query – faqat 3 asosiy til
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    results = []

    if not query:
        return

    inline_langs = {
        'English 🇬🇧': 'en',
        'Russian 🇷🇺': 'ru',
        'Korean 🇰🇷': 'ko'
    }

    for name, code in inline_langs.items():
        try:
            translated = GoogleTranslator(source='auto', target=code).translate(query)
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=name,
                    input_message_content=InputTextMessageContent(f"{name}:\n{translated}")
                )
            )
        except Exception as e:
            print(f"Xatolik: {e}")
            continue

    await update.inline_query.answer(results, cache_time=60)

# Botni ishga tushurish
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))  # PDF handler
    app.add_handler(InlineQueryHandler(inline_query_handler))
    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
