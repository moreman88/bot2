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

# --- Загружаем .env ---
load_dotenv()

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

COLLEGE_NAME_RU = os.getenv("COLLEGE_NAME_RU", "Карагандинский колледж технологии и сервиса")
COLLEGE_NAME_KK = os.getenv("COLLEGE_NAME_KK", "«Қарағанды технология және сервис колледжі»")

SCHEDULE_URL = os.getenv("SCHEDULE_URL", "https://kkts.edu.kz/raspisanie")
SITE_URL = os.getenv("SITE_URL", "https://kkts.edu.kz")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Хранилище языков пользователей ---
user_languages = {}

# --- Клавиатуры ---
def get_main_keyboard(lang="ru") -> ReplyKeyboardMarkup:
    if lang == "kk":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Сабақ кестесі"), KeyboardButton(text="🎓 Қабылдау комиссиясы")],
                [KeyboardButton(text="📞 Байланыс"), KeyboardButton(text="⏰ Қоңырау кестесі")],
                [KeyboardButton(text="🌐 Тілді өзгерту")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Бөлімді таңдаңыз..."
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🎓 Приёмная комиссия")],
                [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="⏰ Расписание звонков")],
                [KeyboardButton(text="🌐 Сменить язык")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите раздел..."
        )


def get_back_keyboard(lang="ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад" if lang == "ru" else "🔙 Артқа")]
        ],
        resize_keyboard=True
    )

# --- Генерация ответа от OpenRouter (если потребуется) ---
async def generate_reply(prompt: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "X-Title": "KKTiS College Bot"
        }

        data = {
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [
                {"role": "system", "content": "Отвечай как виртуальный помощник колледжа."},
                {"role": "user", "content": prompt},
            ],
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if response.status_code != 200:
            return f"⚠️ Ошибка: {response.text}"

        rj = response.json()
        return rj["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Ошибка при подключении: {e}"

# --- /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_languages[message.from_user.id] = "ru"  # язык по умолчанию
    await message.answer(
        f"🎓 <b>{COLLEGE_NAME_RU}</b>\n\n"
        f"👋 Здравствуйте, <b>{message.from_user.first_name}</b>!\n\n"
        f"Я — официальный бот колледжа. Выберите нужный раздел 👇",
        reply_markup=get_main_keyboard("ru")
    )

# --- Смена языка ---
@dp.message(F.text.in_(["🌐 Сменить язык", "🌐 Тілді өзгерту"]))
async def change_language(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    new_lang = "kk" if lang == "ru" else "ru"
    user_languages[message.from_user.id] = new_lang

    if new_lang == "kk":
        await message.answer(
            f"🇰🇿 Тіл қазақ тіліне ауыстырылды!\n\n🎓 <b>{COLLEGE_NAME_KK}</b>",
            reply_markup=get_main_keyboard("kk")
        )
    else:
        await message.answer(
            f"🇷🇺 Язык изменён на русский!\n\n🎓 <b>{COLLEGE_NAME_RU}</b>",
            reply_markup=get_main_keyboard("ru")
        )

# --- Назад ---
@dp.message(F.text.in_(["🔙 Назад", "🔙 Артқа"]))
async def go_back(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    await message.answer(
        "🔽 Главное меню:" if lang == "ru" else "🔽 Басты мәзір:",
        reply_markup=get_main_keyboard(lang)
    )

# --- Расписание ---
@dp.message(F.text.in_(["📅 Расписание", "📅 Сабақ кестесі"]))
async def show_schedule(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "kk":
        await message.answer(
            f"📅 <b>Сабақ кестесі:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Кестені ашу</a>\n\n🌐 {SITE_URL}",
            disable_web_page_preview=True
        )
    else:
        await message.answer(
            f"📅 <b>Расписание занятий:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Открыть расписание</a>\n\n🌐 {SITE_URL}",
            disable_web_page_preview=True
        )

# --- Контакты ---
@dp.message(F.text.in_(["📞 Контакты", "📞 Байланыс"]))
async def show_contacts(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "kk":
        await message.answer(
            "📞 <b>Байланыс:</b>\nҚарағанды, Затаевич көш., 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz"
        )
    else:
        await message.answer(
            "📞 <b>Контакты:</b>\nКараганда, ул. Затаевича, 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz"
        )

# --- Приёмная комиссия ---
@dp.message(F.text.in_(["🎓 Приёмная комиссия", "🎓 Қабылдау комиссиясы"]))
async def show_admission(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")

    if lang == "kk":
        text = (
            "🎓 <b>ҚАБЫЛДАУ КОМИССИЯСЫ</b>\n\n"
            "«Қарағанды технология және сервис колледжі» КМҚК келесі мамандықтар бойынша қабылдау жүргізеді:\n\n"
            "💻 <b>Цифрлық техника</b> — 11 сынып негізінде (10 ай)\n"
            "✂️ <b>Шаштараз өнері</b> — 9 сынып (2 ж. 10 ай) / ТжКБ (10 ай)\n"
            "👗 <b>Тігін өндірісі және киім үлгілеу</b> — 9 сынып (2 ж. 10 ай) / ТжКБ (10 ай)\n"
            "🧵 <b>Тігінші</b> — 9 сынып (2 ж. 10 ай)\n"
            "👞 <b>Аяқ киім ісі</b> — ТжКБ (10 ай)\n"
            "💼 <b>Офис-менеджер</b> — 11 сынып (10 ай)\n\n"
            "📋 <b>Құжаттар:</b>\n"
            "1️⃣ Өтініш\n2️⃣ Білім туралы құжат\n3️⃣ Фото 3×4 (4 дана)\n4️⃣ №075-У медициналық анықтама\n\n"
            "📤 <b>Құжат тапсыру тәсілдері:</b>\n1️⃣ Колледжге келіп тапсыру\n2️⃣ www.egov.kz арқылы\n3️⃣ My College платформасы\n\n"
            "📞 <b>Байланыс:</b>\n"
            "Әмірханова М.А. — ☎️ 8-701-842-25-36\n"
            "Искакова Г.К. — ☎️ 8-700-145-45-36\n"
            "⏰ Дс–Жм: 08:00–17:00\n\n"
            "💙 Біз сізді колледжімізде күтеміз!"
        )
    else:
        text = (
            "🎓 <b>ПРИЁМНАЯ КОМИССИЯ ККТиС</b>\n\n"
            "КГКП «Карагандинский колледж технологии и сервиса» приглашает абитуриентов по направлениям:\n\n"
            "💻 <b>Цифровая техника</b> — 11 кл. (10 мес)\n"
            "✂️ <b>Парикмахерское искусство</b> — 9 кл. (2г.10мес) / ТиПО (10 мес)\n"
            "👗 <b>Швейное производство и моделирование одежды</b> — 9 кл. (2г.10мес) / ТиПО (10 мес)\n"
            "🧵 <b>Портной</b> — 9 кл. (2г.10мес)\n"
            "👞 <b>Обувное дело</b> — ТиПО (10 мес)\n"
            "💼 <b>Офис-менеджер</b> — 11 кл. (10 мес)\n\n"
            "📋 <b>Документы:</b>\n"
            "1️⃣ Заявление\n2️⃣ Документ об образовании\n3️⃣ Фото 3×4 (4 шт)\n4️⃣ Медсправка №075-У\n\n"
            "📤 <b>Подача документов:</b>\n1️⃣ Лично в колледже\n2️⃣ Через www.egov.kz\n3️⃣ Через My College\n\n"
            "📞 <b>Контакты:</b>\n"
            "Әмірханова М.А. — ☎️ 8-701-842-25-36\n"
            "Искакова Г.К. — ☎️ 8-700-145-45-36\n"
            "⏰ Пн–Пт: 08:00–17:00\n\n"
            "💙 Мы ждём вас в нашем колледже!"
        )

    await message.answer(text, reply_markup=get_back_keyboard(lang))

# --- Расписание звонков ---
@dp.message(F.text.in_(["⏰ Расписание звонков", "⏰ Қоңырау кестесі"]))
async def show_bell_schedule(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")

    if lang == "ru":
        text = (
            "<b>⏰ Расписание звонков</b>\n\n"
            "📅 <b>Понедельник:</b>\n"
            "09:00–09:45 — Кураторский час\n"
            "09:50–11:20 — 1 пара 🎓\n\n"
            "🍽 Обед (1 поток) — 11:20–11:40\n"
            "11:40–13:10 — 2 пара 🎓\n\n"
            "🍽 Обед (2 поток) — 13:10–13:30\n"
            "13:30–15:00 — 3 пара 🎓\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📅 <b>Вторник–Пятница:</b>\n"
            "09:00–10:30 — 1 пара 🎓\n"
            "10:40–12:10 — 2 пара 🎓\n\n"
            "🍽 Обед (1 поток) — 12:10–12:30\n"
            "12:30–14:00 — 3 пара 🎓\n\n"
            "🍽 Обед (2 поток) — 14:00–14:20\n"
            "14:20–15:50 — 4 пара 🎓"
        )
    else:
        text = (
            "<b>⏰ Қоңырау кестесі</b>\n\n"
            "📅 <b>Дүйсенбі:</b>\n"
            "09:00–09:45 — Тәрбие сағаты\n"
            "09:50–11:20 — 1 сабақ 🎓\n\n"
            "🍽 Түскі ас (1 ағым) — 11:20–11:40\n"
            "11:40–13:10 — 2 сабақ 🎓\n\n"
            "🍽 Түскі ас (2 ағым) — 13:10–13:30\n"
            "13:30–15:00 — 3 сабақ 🎓\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📅 <b>Сейсенбі–Жұма:</b>\n"
            "09:00–10:30 — 1 сабақ 🎓\n"
            "10:40–12:10 — 2 сабақ 🎓\n\n"
            "🍽 Түскі ас (1 ағым) — 12:10–12:30\n"
            "12:30–14:00 — 3 сабақ 🎓\n\n"
            "🍽 Түскі ас (2 ағым) — 14:00–14:20\n"
            "14:20–15:50 — 4 сабақ 🎓"
        )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Основной запуск ---
async def main():
    logger.info("✅ Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

