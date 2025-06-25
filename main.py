import os
import random
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OCR_API_KEY = os.getenv('OCR_API_KEY')
ADMIN_ID = 6905227976

user_history = {}
user_stats = {}

LANGUAGES = {
    'English': 'en', 'Russian': 'ru', 'Uzbek': 'uz', 'Korean': 'ko', 'French': 'fr',
    'German': 'de', 'Chinese': 'zh', 'Japanese': 'ja', 'Spanish': 'es', 'Arabic': 'ar',
    'Turkish': 'tr', 'Italian': 'it', 'Hindi': 'hi', 'Kazakh': 'kk', 'Kyrgyz': 'ky'
}

motivatsiyalar = [
    "Har bir yangi so‘z – bu yangi imkoniyat!",
    "Har kuni 10 ta so‘z o‘rgan, 1 yilda 3650 ta so‘z bilasan!",
    "Tilingni mashq qilmasang, u qotib qoladi!",
    "Til o‘rganish – sabr va izchillik san’atidir!",
    "Bugun bir so‘z o‘rgansang, ertaga gapira boshlaysan!",
    "Til bilgan – dunyoni biladi!",
    "Hech narsa o‘z-o‘zidan bo‘lmaydi – harakat qil!",
    "Bugun qilgan kichik mashqing, ertaga katta natija beradi!",
    "Inglizcha 'never give up' degani – hech qachon taslim bo‘lma!",
    "Qiyin – vaqtincha, bilim – abadiy!",
    "Til – bu qurol. Uni o‘rgansang, dunyo seniki!",
    "Bir so‘z – bir eshik. Ko‘proq eshik och!",
    "Mashq – bilim onasi!",
    "Tilni yaxshi bilgan odam – yaxshi imkoniyatlarga ega!",
    "Har kuni 5 daqiqa til mashqi qil!",
    "Qiziqish bo‘lsa, til oson o‘rganiladi!",
    "Ertalabki 10 daqiqa tilga bag‘ishla – kun samarali bo‘ladi!",
    "Bugun boshlamasang, ertaga kech bo‘ladi!",
    "Biror narsa o‘rganmasang, yo‘qotasan!",
    "Til – bu sarmoya. Har kuni unga sarmoya qil!"
]

main_keyboard = ReplyKeyboardMarkup(
    [
        ['🌍 Til tanlash', '🔄 Auto Detect'],
        ['📖 Tarjima tarixi', '🗑 Tarixni tozalash'],
        ['📊 Statistika', '💡 Til motivatsiyasi']
    ],
    resize_keyboard=True
)

lang_keyboard = ReplyKeyboardMarkup(
    [[lang] for lang in LANGUAGES.keys()],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tilni tanlang yoki matn yuboring:", reply_markup=main_keyboard)

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

    if user_text == '💡 Til motivatsiyasi':
        motivatsiya = random.choice(motivatsiyalar)
        await update.message.reply_text(f"{motivatsiya}", reply_markup=main_keyboard)
        return

    target_lang = context.user_data.get('target_lang', 'en')
    try:
        result = GoogleTranslator(source='auto', target=target_lang).translate(user_text)
        user_history[user_id].append({'input': user_text, 'output': result})
        user_stats[user_id] += 1
        await update.message.reply_text(f"Tarjima ({target_lang}): {result}", reply_markup=main_keyboard)
    except Exception as e:
        await update.message.reply_text(f"Xatolik: {e}", reply_markup=main_keyboard)

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

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
