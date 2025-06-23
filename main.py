import os from dotenv import load_dotenv from telegram import Update, ReplyKeyboardMarkup from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters from deep_translator import GoogleTranslator

load_dotenv() TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

user_history = {}  # Tarjima tarixi user_stats = {'total_translations': 0}  # Statistika uchun

LANGUAGES = { 'English': 'en', 'Russian': 'ru', 'Uzbek': 'uz', 'Korean': 'ko', 'French': 'fr', 'German': 'de', 'Chinese': 'zh', 'Japanese': 'ja', 'Spanish': 'es', 'Arabic': 'ar', 'Turkish': 'tr', 'Italian': 'it', 'Hindi': 'hi', 'Kazakh': 'kk', 'Kyrgyz': 'ky' }

main_keyboard = ReplyKeyboardMarkup( [ ['🌍 Til tanlash', '🔄 Auto Detect'], ['📖 Tarjima tarixi', '🗑 Tarixni tozalash'] ], resize_keyboard=True )

lang_keyboard = ReplyKeyboardMarkup( [[lang] for lang in LANGUAGES.keys()],  # Har til bitta qatorda resize_keyboard=True )

ADMIN_ID = 6905227976  # Behruzning ID si

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id if user_id == ADMIN_ID: stats_text = f"📊 Statistika:\nJami tarjimalar: {user_stats['total_translations']}" await update.message.reply_text(stats_text, reply_markup=main_keyboard) else: await update.message.reply_text("Tilni tanlang yoki Auto detect rejimda matn yuboring:", reply_markup=main_keyboard)

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE): user_id = update.message.from_user.id user_text = update.message.text

if user_id not in user_history:
    user_history[user_id] = []

if user_text == '🌍 Til tanlash':
    await update.message.reply_text("Quyidan tilni tanlang:", reply_markup=lang_keyboard)
    return

if user_text in LANGUAGES:
    context.user_data['target_lang'] = LANGUAGES[user_text]
    await update.message.reply_text(
        f"Target language set to: {user_text}. Endi matn yuboring.",
        reply_markup=main_keyboard
    )
    return

if user_text == '🔄 Auto Detect':
    context.user_data['target_lang'] = 'en'
    await update.message.reply_text("Auto detect rejimi tanlandi. Endi matn yuboring.", reply_markup=main_keyboard)
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

target_lang = context.user_data.get('target_lang', 'en')
try:
    result = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
    user_history[user_id].append({'input': user_text, 'output': result})
    user_stats['total_translations'] += 1  # Statistika uchun
    await update.message.reply_text(f"Tarjima ({target_lang}): {result}", reply_markup=main_keyboard)
except Exception as e:
    await update.message.reply_text(f"Xatolik: {e}", reply_markup=main_keyboard)

def main(): app = ApplicationBuilder().token(TELEGRAM_TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text)) print("Bot ishga tushdi...") app.run_polling()

if name == "main": main()

