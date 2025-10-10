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
SCHEDULE_URL = os.getenv("SCHEDULE_URL")
SITE_URL = os.getenv("SITE_URL")

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
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        "Отвечай дружелюбно, кратко и информативно. "
                        "Если вопрос не относится к колледжу, обязательно откажись вежливо."
                    )
                },
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

        print("STATUS:", response.status_code)
        print("BODY:", response.text)

        if response.status_code != 200:
            logger.error(f"❌ Ошибка OpenRouter: {response.status_code} - {response.text}")
            return f"⚠️ Ошибка при обращении к OpenRouter API:\n\n{response.text}"

        rj = response.json()
        return rj["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⏳ Сервер OpenRouter не ответил вовремя. Попробуй позже."
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
    message.conf["lang"] = lang  # сохраняем язык в контексте

# --- Приёмная комиссия ---
@dp.message(F.text.in_(["🎓 Приёмная комиссия", "🎓 Қабылдау комиссиясы"]))
async def show_admission(message: Message):
    lang = "kz" if "Қабылдау" in message.text else "ru"

    if lang == "kz":
        text = (
            "🎓 <b>ҚАБЫЛДАУ КОМИССИЯСЫ</b>\n\n"
            "Қарағанды технология және сервис колледжі келесі мамандықтар бойынша оқуға шақырады:\n\n"
            "📘 <b>Мамандықтар:</b>\n"
            "• 💻 <b>Цифрлық техника</b> — 11 сынып негізінде — 10 ай.\n"
            "• ✂️ <b>Шаштараз өнері</b> — 9 сыныптан кейін — 2 жыл 10 ай / ТжКБ базасында — 10 ай.\n"
            "• 👗 <b>Тігін өндірісі және киім үлгілеу</b> — 9 сыныптан кейін — 2 жыл 10 ай / ТжКБ базасында — 10 ай.\n"
            "• 🧵 <b>Тігінші</b> — 9 сыныптан кейін — 2 жыл 10 ай.\n"
            "• 👞 <b>Аяқ киім ісі</b> — ТжКБ базасында — 10 ай.\n"
            "• 💼 <b>Офис-менеджер</b> — 11 сыныптан кейін — 10 ай.\n\n"
            "📋 <b>Қажетті құжаттар:</b>\n"
            "1️⃣ Өтініш\n"
            "2️⃣ Білім туралы құжат (аттестат, диплом)\n"
            "3️⃣ 3×4 фото — 4 дана\n"
            "4️⃣ №075-У медициналық анықтама\n\n"
            "🌍 <b>Шетел азаматтары үшін:</b> Жеке куәлік немесе тұруға ықтиярхат\n\n"
            "📤 <b>Құжаттарды тапсыру тәсілдері:</b>\n"
            "1️⃣ Колледжге келіп тапсыру — Қарағанды, Затаевич көш., 75\n"
            "2️⃣ 🌐 www.egov.kz арқылы\n"
            "3️⃣ <b>My College</b> платформасы арқылы\n\n"
            "📞 <b>Байланыс:</b>\n"
            "👤 Әмірханова М.А. — ☎️ 8-701-842-25-36\n"
            "👤 Искакова Г.К. — ☎️ 8-700-145-45-36\n"
            "🕒 Дс–Жм: 08:00–17:00\n\n"
            "💙 <b>Біз сізді күтеміз!</b>"
        )
    else:
        text = (
            "🎓 <b>ПРИЁМНАЯ КОМИССИЯ ККТиС</b>\n\n"
            "Карагандинский колледж технологии и сервиса приглашает абитуриентов на обучение по направлениям:\n\n"
            "📘 <b>Специальности:</b>\n"
            "• 💻 <b>Цифровая техника</b> — на базе 11 кл. — 10 мес.\n"
            "• ✂️ <b>Парикмахерское искусство</b> — на базе 9 кл. — 2 г. 10 мес. / ТиПО — 10 мес.\n"
            "• 👗 <b>Швейное производство и моделирование одежды</b> — на базе 9 кл. — 2 г. 10 мес. / ТиПО — 10 мес.\n"
            "• 🧵 <b>Портной</b> — на базе 9 кл. — 2 г. 10 мес.\n"
            "• 👞 <b>Обувное дело</b> — на базе ТиПО — 10 мес.\n"
            "• 💼 <b>Офис-менеджер</b> — на базе 11 кл. — 10 мес.\n\n"
            "📋 <b>Документы для поступления:</b>\n"
            "1️⃣ Заявление о приёме\n"
            "2️⃣ Документ об образовании\n"
            "3️⃣ Фото 3×4 — 4 шт.\n"
            "4️⃣ Медицинская справка №075-У\n\n"
            "🌍 <b>Для иностранных граждан:</b> удостоверение личности / вид на жительство\n\n"
            "📤 <b>Подача документов:</b>\n"
            "1️⃣ В колледже — Караганда, ул. Затаевича, 75\n"
            "2️⃣ Через 🌐 www.egov.kz\n"
            "3️⃣ Через платформу My College\n\n"
            "📞 <b>Контакты:</b>\n"
            "👤 Әмірханова М.А. — ☎️ 8-701-842-25-36\n"
            "👤 Искакова Г.К. — ☎️ 8-700-145-45-36\n"
            "🕒 Пн–Пт: 08:00–17:00\n\n"
            "💙 <b>Ждём вас в Карагандинском колледже технологии и сервиса!</b>"
        )

    await message.answer(text, parse_mode=ParseMode.HTML)

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
            "Үзіліс — 10 мин\n"
            "2-пара — 10:40 – 12:10\n\n"
            "Түскі ас (1-ағын) — 20 мин\n"
            "3-пара — 12:30 – 14:00\n\n"
            "Түскі ас (2-ағын) — 20 мин\n"
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
            "Перемена — 10 мин\n"
            "2 пара — 10:40 – 12:10\n\n"
            "Обед (1-й поток) — 20 мин\n"
            "3 пара — 12:30 – 14:00\n\n"
            "Обед (2-й поток) — 20 мин\n"
            "4 пара — 14:20 – 15:50"
        )
    await message.answer(text, parse_mode=ParseMode.HTML)

# --- Чат (ИИ) ---
@dp.message()
async def chat(message: Message):
    lang = "kz" if any(word in message.text.lower() for word in ["сәлем", "қалай", "колледж"]) else "ru"
    reply = await generate_reply(message.text, language=lang)
    await message.answer(reply)

# --- Основной запуск ---
async def main():
    logger.info("✅ Бот запущен и готов к работе через OpenRouter!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
