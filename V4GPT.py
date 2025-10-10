import os
import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# --- Загрузка окружения ---
load_dotenv()

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SCHEDULE_URL = os.getenv("SCHEDULE_URL")
SITE_URL = os.getenv("SITE_URL")
COLLEGE_NAME = os.getenv("COLLEGE_NAME", "Қарағанды технология және сервис колледжі")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Словарь сессий пользователей ---
user_languages = {}

# --- Клавиатура выбора языка ---
def get_language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇰🇿 Қазақша"), KeyboardButton(text="🇷🇺 Русский")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Тілді таңдаңыз / Выберите язык"
    )

# --- Основное меню на двух языках ---
def get_main_keyboard(lang: str):
    if lang == "kk":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Сабақ кестесі"), KeyboardButton(text="🎓 Қабылдау комиссиясы")],
                [KeyboardButton(text="📞 Байланыс"), KeyboardButton(text="⏰ Қоңырау кестесі")],
            ],
            resize_keyboard=True,
            input_field_placeholder="Бөлімді таңдаңыз..."
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🎓 Приёмная комиссия")],
                [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="⏰ Расписание звонков")],
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите раздел..."
        )

# --- Генерация ответа через OpenRouter ---
async def generate_reply(prompt: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [{"role": "user", "content": prompt}],
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code != 200:
            return "⚠️ OpenRouter серверімен байланыс қатесі. Кейінірек қайталап көріңіз."

        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return "😔 Сервермен байланыс кезінде қате пайда болды."

# --- Команда /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🎓 Сәлеметсіз бе! / Здравствуйте!\n\n"
        "Тілді таңдаңыз / Выберите язык 👇",
        reply_markup=get_language_keyboard()
    )

# --- Выбор языка ---
@dp.message(F.text.in_(["🇰🇿 Қазақша", "🇷🇺 Русский"]))
async def set_language(message: Message):
    user_id = message.from_user.id
    if "Қазақша" in message.text:
        user_languages[user_id] = "kk"
        await message.answer(
            f"✅ Тіл таңдалды: <b>Қазақ тілі</b>\n\n"
            f"Сәлем, <b>{message.from_user.first_name}</b>!\n"
            f"Мен — {COLLEGE_NAME} ресми ботымын.\nТөменнен қажетті бөлімді таңдаңыз 👇",
            reply_markup=get_main_keyboard("kk")
        )
    else:
        user_languages[user_id] = "ru"
        await message.answer(
            f"✅ Язык выбран: <b>Русский</b>\n\n"
            f"Здравствуйте, <b>{message.from_user.first_name}</b>!\n"
            f"Я — официальный бот колледжа.\nВыберите нужный раздел 👇",
            reply_markup=get_main_keyboard("ru")
        )

# --- Кнопки ---
@dp.message(F.text.in_(["📅 Сабақ кестесі", "📅 Расписание"]))
async def show_schedule(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "kk":
        text = f"📅 <b>Сабақ кестесі:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Кестені ашу</a>\n\n🌐 {SITE_URL}"
    else:
        text = f"📅 <b>Расписание занятий:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Открыть расписание</a>\n\n🌐 {SITE_URL}"
    await message.answer(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@dp.message(F.text.in_(["📞 Байланыс", "📞 Контакты"]))
async def show_contacts(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "kk":
        text = (
            "📞 <b>Байланыс:</b>\n"
            "Қарағанды қ., Затаевич көш., 75\n"
            "☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kzu.kz"
        )
    else:
        text = (
            "📞 <b>Контакты:</b>\n"
            "Караганда, ул. Затаевича, 75\n"
            "☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kzu.kz"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(F.text.in_(["🎓 Қабылдау комиссиясы", "🎓 Приёмная комиссия"]))
async def show_admission(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "kk":
        text = (
            "🎓 <b>ҚАБЫЛДАУ КОМИССИЯСЫ</b>\n\n"
            "Қарағанды технология және сервис колледжі келесі мамандықтар бойынша қабылдау жүргізеді:\n\n"
            "📘 <b>Мамандықтар:</b>\n"
            "• 💻 <b>Цифрлық техника</b> — 11 сынып негізінде — 10 ай\n"
            "• ✂️ <b>Шаштараз өнері</b> — 9 сынып — 2 ж. 10 ай / ТжКБ — 10 ай\n"
            "• 👗 <b>Тігін өндірісі және киім үлгілеу</b> — 9 сынып — 2 ж. 10 ай / ТжКБ — 10 ай\n"
            "• 🧵 <b>Тігінші</b> — 9 сынып — 2 ж. 10 ай\n"
            "• 👞 <b>Аяқ киім ісі</b> — ТжКБ — 10 ай\n"
            "• 💼 <b>Офис-менеджер</b> — 11 сынып — 10 ай\n\n"
            "📋 <b>Қажетті құжаттар:</b>\n"
            "1️⃣ Өтініш\n"
            "2️⃣ Білім туралы құжат (аттестат, диплом)\n"
            "3️⃣ Фото 3×4 — 4 дана\n"
            "4️⃣ №075-У медициналық анықтама\n\n"
            "📤 <b>Құжаттарды тапсыру тәсілдері:</b>\n"
            "• Колледжге келіп тапсыру — Қарағанды қ., Затаевич көш., 75\n"
            "• www.egov.kz порталы арқылы\n"
            "• My College платформасы арқылы\n\n"
            "📞 <b>Қабылдау комиссиясының байланысы:</b>\n"
            "👤 Әмірханова М.А. — ☎️ 8-701-842-25-36\n"
            "👤 Искакова Г.К. — ☎️ 8-700-145-45-36\n"
            "⏰ Дс–Жм: 08:00–17:00\n\n"
            "💙 <b>Біз сізді колледжімізде күтеміз!</b>"
        )
    else:
        text = (
            "🎓 <b>ПРИЁМНАЯ КОМИССИЯ</b>\n\n"
            "КГКП «Карагандинский колледж технологии и сервиса» приглашает абитуриентов на обучение:\n\n"
            "📘 <b>Специальности:</b>\n"
            "• 💻 <b>Цифровая техника</b> — 10 мес.\n"
            "• ✂️ <b>Парикмахерское искусство</b> — 2 г. 10 мес. / 10 мес.\n"
            "• 👗 <b>Швейное производство</b> — 2 г. 10 мес. / 10 мес.\n"
            "• 🧵 <b>Портной</b> — 2 г. 10 мес.\n"
            "• 👞 <b>Обувное дело</b> — 10 мес.\n"
            "• 💼 <b>Офис-менеджер</b> — 10 мес.\n\n"
            "📋 Документы: заявление, аттестат, фото 3×4 (4 шт), мед. справка №075-У\n\n"
            "📤 Подача: лично, через www.egov.kz или My College\n\n"
            "📞 Әмірханова М.А. — 8-701-842-25-36\n"
            "📞 Искакова Г.К. — 8-700-145-45-36\n"
            "🕒 Пн–Пт: 08:00–17:00\n\n"
            "💙 Мы ждём вас в ККТиС!"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)

@dp.message(F.text.in_(["⏰ Қоңырау кестесі", "⏰ Расписание звонков"]))
async def show_bell_schedule(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "kk":
        text = (
            "⏰ <b>Қоңырау кестесі</b>\n\n"
            "<b>Дүйсенбі:</b>\n"
            "1-сабақ — 09:00 – 09:45\n"
            "Үзіліс — 5 мин\n"
            "2-сабақ — 09:50 – 11:20\n\n"
            "Түскі ас (1-ағын) — 20 мин\n"
            "3-сабақ — 11:40 – 13:10\n\n"
            "Түскі ас (2-ағын) — 20 мин\n"
            "4-сабақ — 13:30 – 15:00\n\n"
            "——————————————\n"
            "<b>Сейсенбі – Жұма:</b>\n"
            "1-сабақ — 09:00 – 10:30\n"
            "Үзіліс — 10 мин\n"
            "2-сабақ — 10:40 – 12:10\n\n"
            "Түскі ас (1-ағын) — 20 мин\n"
            "3-сабақ — 12:30 – 14:00\n\n"
            "Түскі ас (2-ағын) — 20 мин\n"
            "4-сабақ — 14:20 – 15:50"
        )
    else:
        text = (
            "⏰ <b>Расписание звонков</b>\n\n"
            "<b>Понедельник:</b>\n"
            "1 пара — 09:00 – 09:45\n"
            "Перемена — 5 мин\n"
            "2 пара — 09:50 – 11:20\n\n"
            "Обед (1-й поток) — 20 мин\n"
            "3 пара — 11:40 – 13:10\n\n"
            "Обед (2-й поток) — 20 мин\n"
            "4 пара — 13:30 – 15:00\n\n"
            "——————————————\n"
            "<b>Вторник – Пятница:</b>\n"
            "1 пара — 09:00 – 10:30\n"
            "Перемена — 10 мин\n"
            "2 пара — 10:40 – 12:10\n\n"
            "Обед (1-й поток) — 20 мин\n"
            "3 пара — 12:30 – 14:00\n\n"
            "Обед (2-й поток) — 20 мин\n"
            "4 пара — 14:20 – 15:50"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)

# --- Чат-режим ---
@dp.message()
async def chat(message: Message):
    reply = await generate_reply(message.text)
    await message.answer(reply)

# --- Запуск ---
async def main():
    logger.info("✅ Бот с поддержкой казахского языка запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
