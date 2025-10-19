import os
import json
from uuid import uuid4
from dotenv import load_dotenv
import fitz  # PyMuPDF
from telegram import Update, ReplyKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters, InlineQueryHandler
)
from deep_translator import GoogleTranslator

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6905227976

LANGUAGES = {
    'English': 'en', 'Russian': 'ru', 'Uzbek': 'uz', 'Korean': 'ko', 'French': 'fr',
    'German': 'de', 'Chinese': 'zh', 'Japanese': 'ja', 'Spanish': 'es', 'Arabic': 'ar',
    'Turkish': 'tr', 'Italian': 'it', 'Hindi': 'hi', 'Kazakh': 'kk', 'Kyrgyz': 'ky'
}

user_history = {}

def load_user_stats():
    try:
        with open("user_stats.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_stats(stats):
    with open("user_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False)

user_stats = load_user_stats()

# Klaviatura
main_keyboard = ReplyKeyboardMarkup(
    [
        ['🌍 Til tanlash', '🔄 Auto Detect'],
        ['📄 PDF tarjima qilish'],
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
    await update.message.reply_text("Tilni tanlang yoki matn yuboring:", reply_markup=main_keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 Al Tarjimon Bot yordam:\n\n"
        "📌 Yuboring:\n"
        "— Oddiy matn: avtomatik tarjima bo‘ladi\n"
        "— PDF fayl: matnni chiqarib tarjima qiladi\n"
        "— Inline qidiruv: @AlTarjimonBot so‘z\n\n"
        "🛠 Tugmalar:\n"
        "🌍 Til tanlash – tarjima tilini tanlash\n"
        "🔄 Auto Detect – avtomatik aniqlash\n"
        "📖 Tarjima tarixi – oxirgi 5 ta tarjima\n"
        "📄 PDF tarjima qilish – fayl yuboring\n"
        "📊 Statistika – umumiy foydalanuvchilar soni\n\n"
        "👨‍💻 Yaratuvchi: @Ziyqulov_Behruz"
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_text = update.message.text
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
        if int(user_id) != ADMIN_ID:
            await update.message.reply_text("❌ Bu bo‘lim faqat admin uchun!", reply_markup=main_keyboard)
            return

        total_users = len(user_stats)
        total_translations = sum(user_stats.values())

        await update.message.reply_text(
            f"📊 Statistika (Admin):\n"
            f"👥 Umumiy foydalanuvchilar: {total_users}\n"
            f"🔤 Tarjimalar soni: {total_translations}",
            reply_markup=main_keyboard
        )
        return

    target_lang = context.user_data.get('target_lang', 'en')
    try:
        result = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        user_history[user_id].append({'input': user_text, 'output': result})

        user_stats[user_id] = user_stats.get(user_id, 0) + 1
        save_user_stats(user_stats)

        await update.message.reply_text(f"Tarjima ({target_lang}): {result}", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}", reply_markup=main_keyboard)

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    if not document.file_name.endswith('.pdf'):
        await update.message.reply_text("❌ Iltimos, faqat PDF fayl yuboring.")
        return

    file = await context.bot.get_file(document.file_id)
    file_path = f"{document.file_unique_id}.pdf"
    await file.download_to_drive(file_path)

    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()

    if not text.strip():
        await update.message.reply_text("❌ PDF ichida matn topilmadi.")
        return

    try:
        translated = GoogleTranslator(source='auto', target='uz').translate(text)
        await update.message.reply_text(f"📄 PDF tarjima natijasi:\n\n{translated[:4000]}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Tarjimada xatolik: {e}")

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
        except:
            continue

    await update.inline_query.answer(results, cache_time=60)

async def update_bot_description(app):
    desc = "Al Tarjimon Bot — oyda taxminan 12K+ foydalanuvchi 🇺🇿🌍"
    bot: Bot = app.bot
    try:
        await bot.set_my_description(description=desc)
        print(f"Bot tavsifi yangilandi: {desc}")
    except Exception as e:
        print(f"Tavsiya yangilanishida xatolik: {e}")

# ✅ To‘g‘rilangan qism
def main():
    async def on_startup(app):
        await update_bot_description(app)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(InlineQueryHandler(inline_query_handler))

    print("Bot ishga tushdi...")

    async def run():
        await on_startup(app)
        await app.run_polling()

    import asyncio
    asyncio.run(run())

if __name__ == "__main__":
    main()
