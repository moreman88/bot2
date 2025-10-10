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

# --- Загружаем переменные окружения ---
load_dotenv()

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

COLLEGE_NAME_RU = "Карагандинский колледж технологии и сервиса"
COLLEGE_NAME_KZ = "Қарағанды технология және сервис колледжі» КМҚК"

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Системные инструкции ---
COLLEGE_RULES_RU = (
    "Ты — виртуальный помощник Карагандинского колледжа технологии и сервиса (ККТиС). "
    "Отвечай только на вопросы, связанные с колледжем, образованием, приёмом, расписанием, "
    "специальностями, контактами и студенческой жизнью. "
    "Если вопрос не касается колледжа — вежливо откажись отвечать."
)
COLLEGE_RULES_KZ = (
    "Сен — Қарағанды технология және сервис колледжінің виртуалды көмекшісісің. "
    "Тек колледжге, оқу процесіне, қабылдауға, кестеге, мамандықтарға, "
    "байланыс пен студенттік өмірге қатысты сұрақтарға жауап бер. "
    "Егер сұрақ колледжге қатысы болмаса — сыпайы түрде жауап беруден бас тарт."
)

# --- Клавиатуры ---
def get_language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇰🇿 Қазақша")]],
        resize_keyboard=True,
        input_field_placeholder="Выберите язык / Тілді таңдаңыз"
    )

def get_main_keyboard(lang="ru") -> ReplyKeyboardMarkup:
    if lang == "kz":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Сабақ кестесі"), KeyboardButton(text="🎓 Қабылдау комиссиясы")],
                [KeyboardButton(text="📞 Байланыс"), KeyboardButton(text="⏰ Қоңырау кестесі")],
                [KeyboardButton(text="🌐 Тілді ауыстыру")]
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

# --- Генерация ответа через OpenRouter ---
async def generate_reply(prompt: str, language: str = "ru") -> str:
    try:
        logger.info("🧠 Отправка запроса в OpenRouter...")

        system_prompt = COLLEGE_RULES_KZ if language == "kz" else COLLEGE_RULES_RU

        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "X-Title": "KKTiS College Bot"
        }

        data = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:
            logger.error(f"❌ Ошибка OpenRouter: {response.status_code} - {response.text}")
            return "⚠️ Ошибка при обращении к OpenRouter API. Попробуйте позже."

        rj = response.json()
        return rj["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⏳ Сервер OpenRouter не ответил вовремя. Попробуйте позже."
    except Exception as e:
        logger.error(f"❌ Ошибка при работе с OpenRouter: {e}")
        return f"😔 Не удалось получить ответ от модели.\n\nОшибка: {e}"

# --- Команда /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🌐 Пожалуйста, выберите язык / Тілді таңдаңыз:",
        reply_markup=get_language_keyboard()
    )

# --- Выбор языка ---
@dp.message(F.text.in_(["🇷🇺 Русский", "🇰🇿 Қазақша", "🌐 Сменить язык", "🌐 Тілді ауыстыру"]))
async def choose_language(message: Message):
    lang = "kz" if "Қазақ" in message.text or "Тілді" in message.text else "ru"
    welcome = (
        f"🎓 <b>{COLLEGE_NAME_KZ}</b>\n\n"
        f"Сәлеметсіз бе, <b>{message.from_user.first_name}</b>!\n\n"
        f"Мен колледждің ресми ботымын. Қажетті бөлімді таңдаңыз 👇"
        if lang == "kz"
        else
        f"🎓 <b>{COLLEGE_NAME_RU}</b>\n\n"
        f"👋 Здравствуйте, <b>{message.from_user.first_name}</b>!\n\n"
        f"Я — официальный бот колледжа. Выберите нужный раздел 👇"
    )
    await message.answer(welcome, reply_markup=get_main_keyboard(lang))
    message.conf["lang"] = lang

# --- Приёмная комиссия ---
@dp.message(F.text.in_(["🎓 Приёмная комиссия", "🎓 Қабылдау комиссиясы"]))
async def show_admission(message: Message):
    lang = "kz" if "Қабылдау" in message.text else "ru"

    if lang == "kz":
        text = (
            "🎓 <b>ҚАБЫЛДАУ КОМИССИЯСЫ</b>\n\n"
            "Қарағанды технология және сервис колледжі келесі мамандықтар бойынша оқуға шақырады...\n\n"
            "📍 Мекенжай: Қарағанды, Затаевич к., 75\n"
            "📞 Әмірханова М.А. — 8-701-842-25-36\n"
            "📞 Искакова Г.К. — 8-700-145-45-36"
        )
    else:
        text = (
            "🎓 <b>ПРИЁМНАЯ КОМИССИЯ</b>\n\n"
            "Карагандинский колледж технологии и сервиса приглашает абитуриентов...\n\n"
            "📍 Адрес: Караганда, ул. Затаевича, 75\n"
            "📞 Әмірханова М.А. — 8-701-842-25-36\n"
            "📞 Искакова Г.К. — 8-700-145-45-36"
        )

    await message.answer(text)

# --- Расписание звонков ---
@dp.message(F.text.in_(["⏰ Расписание звонков", "⏰ Қоңырау кестесі"]))
async def show_bell_schedule(message: Message):
    lang = "kz" if "Қоңырау" in message.text else "ru"
    if lang == "kz":
        text = (
            "<b>⏰ Қоңырау кестесі</b>\n\n"
            "<b>Дүйсенбі:</b>\n"
            "Кураторлық сағат — 09:00 – 09:45\n"
            "Үзіліс — 5 мин\n"
            "1-пара — 09:50 – 11:20\n\n"
            "Түскі ас (1-ағын) — 20 мин\n"
            "2-пара — 11:40 – 13:10\n\n"
            "Түскі ас (2-ағын) — 20 мин\n"
            "3-пара — 13:30 – 15:00\n\n"
            "——————————————\n"
            "<b>Сейсенбі – Жұма:</b>\n"
            "1-пара — 09:00 – 10:30\n"
            "2-пара — 10:40 – 12:10\n"
            "3-пара — 12:30 – 14:00\n"
            "4-пара — 14:20 – 15:50"
        )
    else:
        text = (
            "<b>⏰ Расписание звонков</b>\n\n"
            "<b>Понедельник:</b>\n"
            "Кураторский час — 09:00 – 09:45\n"
            "Перемена — 5 мин\n"
            "1 пара — 09:50 – 11:20\n\n"
            "Обед (1-й поток) — 20 мин\n"
            "2 пара — 11:40 – 13:10\n\n"
            "Обед (2-й поток) — 20 мин\n"
            "3 пара — 13:30 – 15:00\n\n"
            "——————————————\n"
            "<b>Вторник – Пятница:</b>\n"
            "1 пара — 09:00 – 10:30\n"
            "2 пара — 10:40 – 12:10\n"
            "3 пара — 12:30 – 14:00\n"
            "4 пара — 14:20 – 15:50"
        )
    await message.answer(text)

# --- Контакты ---
@dp.message(F.text.in_(["📞 Контакты", "📞 Байланыс"]))
async def show_contacts(message: Message):
    lang = "kz" if "Байланыс" in message.text else "ru"
    text = (
        "📞 <b>Контакты:</b>\nКараганда, ул. Затаевича, 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz"
        if lang == "ru" else
        "📞 <b>Байланыс:</b>\nҚарағанды, Затаевич к., 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz"
    )
    await message.answer(text)

# --- Универсальный обработчик сообщений (ИИ) ---
@dp.message()
async def handle_message(message: Message):
    user_text = message.text.strip().lower()

    predefined_buttons = [
        "📅 расписание", "📞 контакты", "🎓 приёмная комиссия",
        "⏰ расписание звонков", "🌐 сменить язык",
        "📅 сабақ кестесі", "📞 байланыс", "🎓 қабылдау комиссиясы",
        "⏰ қоңырау кестесі", "🌐 тілді ауыстыру"
    ]

    if user_text in [b.lower() for b in predefined_buttons]:
        return  # кнопки обрабатываются отдельными функциями

    lang = "kz" if any(word in user_text for word in ["сәлем", "қалай", "колледж"]) else "ru"
    reply = await generate_reply(message.text, language=lang)
    await message.answer(reply)

# --- Основной запуск ---
async def main():
    logger.info("✅ Бот запущен и готов к работе через OpenRouter!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
