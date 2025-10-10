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
COLLEGE_NAME_RU = os.getenv("COLLEGE_NAME", "Карагандинский колледж технологии и сервиса")
COLLEGE_NAME_KZ = "Қарағанды технология және сервис колледжі»"
SCHEDULE_URL = os.getenv("SCHEDULE_URL")
SITE_URL = os.getenv("SITE_URL")

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

# --- Словарь языков пользователей ---
user_languages = {}

# --- Клавиатуры ---
def get_main_keyboard(lang="ru") -> ReplyKeyboardMarkup:
    if lang == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🎓 Приёмная комиссия")],
                [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="⏰ Расписание звонков")],
                [KeyboardButton(text="🌐 Сменить язык")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите раздел..."
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Сабақ кестесі"), KeyboardButton(text="🎓 Қабылдау комиссиясы")],
                [KeyboardButton(text="📞 Байланыс"), KeyboardButton(text="⏰ Қоңырау кестесі")],
                [KeyboardButton(text="🌐 Тілді өзгерту")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Бөлімді таңдаңыз..."
        )

def get_back_keyboard(lang="ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад" if lang == "ru" else "🔙 Артқа")]],
        resize_keyboard=True
    )

# --- OpenRouter API ---
async def generate_reply(prompt: str, lang="ru") -> str:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "X-Title": "KKTiS College Bot"
        }

        system_msg = COLLEGE_RULES_RU if lang == "ru" else COLLEGE_RULES_KZ

        data = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:
            logger.error(f"Ошибка OpenRouter: {response.status_code} - {response.text}")
            return f"⚠️ Ошибка OpenRouter ({response.status_code}):\n{response.text}"

        rj = response.json()
        return rj["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.error(f"Ошибка OpenRouter: {e}")
        return f"⚠️ Не удалось получить ответ: {e}"

# --- /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_languages[user_id] = "ru"
    await message.answer(
        f"🎓 <b>{COLLEGE_NAME_RU}</b>\n\n👋 Здравствуйте, <b>{message.from_user.first_name}</b>!\n\n"
        f"Я — виртуальный помощник колледжа. Выберите раздел 👇",
        reply_markup=get_main_keyboard("ru")
    )

# --- Смена языка ---
@dp.message(F.text.in_(["🌐 Сменить язык", "🌐 Тілді өзгерту"]))
async def change_language(message: Message):
    user_id = message.from_user.id
    current_lang = user_languages.get(user_id, "ru")
    new_lang = "kk" if current_lang == "ru" else "ru"
    user_languages[user_id] = new_lang

    if new_lang == "kk":
        text = f"🎓 <b>{COLLEGE_NAME_KZ}</b>\n\nСәлем, <b>{message.from_user.first_name}</b>!\nТілді қазақшаға ауыстырдыңыз 🇰🇿"
    else:
        text = f"🎓 <b>{COLLEGE_NAME_RU}</b>\n\nЗдравствуйте, <b>{message.from_user.first_name}</b>!\nВы переключились на русский язык 🇷🇺"

    await message.answer(text, reply_markup=get_main_keyboard(new_lang))

# --- Расписание ---
@dp.message(F.text.in_(["📅 Расписание", "📅 Сабақ кестесі"]))
async def show_schedule(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "ru":
        await message.answer(
            f"📅 <b>Расписание занятий:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Открыть расписание</a>\n\n🌐 {SITE_URL}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_back_keyboard("ru")
        )
    else:
        await message.answer(
            f"📅 <b>Сабақ кестесі:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Кестені ашу</a>\n\n🌐 {SITE_URL}",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=get_back_keyboard("kk")
        )

# --- Контакты ---
@dp.message(F.text.in_(["📞 Контакты", "📞 Байланыс"]))
async def show_contacts(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    text = (
        "📞 <b>Контакты:</b>\nКараганда, ул. Затаевича, 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz"
        if lang == "ru" else
        "📞 <b>Байланыс:</b>\nҚарағанды, Затаевич к., 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Расписание звонков ---
@dp.message(F.text.in_(["⏰ Расписание звонков", "⏰ Қоңырау кестесі"]))
async def show_bell_schedule(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")

    if lang == "ru":
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
    else:
        text = (
            "<b>⏰ Қоңырау кестесі</b>\n\n"
            "<b>Дүйсенбі:</b>\n"
            "Кураторлық сағат — 09:00 – 09:45\n"
            "Үзіліс — 5 мин\n"
            "1 сабақ — 09:50 – 11:20\n\n"
            "Түскі ас (1-ағын) — 20 мин\n"
            "2 сабақ — 11:40 – 13:10\n\n"
            "Түскі ас (2-ағын) — 20 мин\n"
            "3 сабақ — 13:30 – 15:00\n\n"
            "——————————————\n"
            "<b>Сейсенбі – Жұма:</b>\n"
            "1 сабақ — 09:00 – 10:30\n"
            "Үзіліс — 10 мин\n"
            "2 сабақ — 10:40 – 12:10\n\n"
            "Түскі ас (1-ағын) — 20 мин\n"
            "3 сабақ — 12:30 – 14:00\n\n"
            "Түскі ас (2-ағын) — 20 мин\n"
            "4 сабақ — 14:20 – 15:50"
        )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Приёмная комиссия ---
@dp.message(F.text.in_(["🎓 Приёмная комиссия", "🎓 Қабылдау комиссиясы"]))
async def show_admission(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")

    if lang == "ru":
        text = (
            "🎓 <b>ПРИЁМНАЯ КОМИССИЯ ККТиС</b>\n\n"
            "📘 <b>Специальности:</b>\n"
            "• 💻 Цифровая техника (11 кл. — 10 мес.)\n"
            "• ✂️ Парикмахерское искусство (9 кл. — 2 г. 10 мес.)\n"
            "• 👗 Швейное производство и моделирование одежды (9 кл. — 2 г. 10 мес.)\n"
            "• 🧵 Портной (9 кл. — 2 г. 10 мес.)\n"
            "• 👞 Обувное дело (ТиПО — 10 мес.)\n"
            "• 💼 Офис-менеджер (11 кл. — 10 мес.)\n\n"
            "📋 <b>Документы:</b>\n"
            "Заявление, аттестат/диплом, 4 фото 3×4, мед. справка №075-У\n\n"
            "📍 Караганда, ул. Затаевича, 75\n"
            "📞 8-701-842-25-36, 8-700-145-45-36\n"
            "🕒 Пн–Пт: 08:00–17:00\n\n"
            "💙 Добро пожаловать в наш колледж!"
        )
    else:
        text = (
            "🎓 <b>ҚАБЫЛДАУ КОМИССИЯСЫ</b>\n\n"
            "📘 <b>Мамандықтар:</b>\n"
            "• 💻 Цифрлық техника (11 сынып — 10 ай)\n"
            "• ✂️ Шаштараз өнері (9 сынып — 2 ж. 10 ай)\n"
            "• 👗 Тігін өндірісі және киім үлгілеу (9 сынып — 2 ж. 10 ай)\n"
            "• 🧵 Тігінші (9 сынып — 2 ж. 10 ай)\n"
            "• 👞 Аяқ киім ісі (ТжКБ — 10 ай)\n"
            "• 💼 Офис-менеджер (11 сынып — 10 ай)\n\n"
            "📋 <b>Құжаттар:</b>\n"
            "Өтініш, аттестат/диплом, 3×4 сурет (4 дана), №075-У мед. анықтама\n\n"
            "📍 Қарағанды, Затаевич к., 75\n"
            "📞 8-701-842-25-36, 8-700-145-45-36\n"
            "🕒 Дс–Жм: 08:00–17:00\n\n"
            "💙 Колледжімізге қош келдіңіз!"
        )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Назад ---
@dp.message(F.text.in_(["🔙 Назад", "🔙 Артқа"]))
async def go_back(message: Message):
    lang = user_languages.get(message.from_user.id, "ru")
    await message.answer("🏠 Главное меню" if lang == "ru" else "🏠 Басты мәзір", reply_markup=get_main_keyboard(lang))

# --- Чат с ИИ ---
@dp.message()
async def handle_ai_message(message: Message):
    if message.text in [
        "📅 Расписание", "🎓 Приёмная комиссия", "📞 Контакты", "⏰ Расписание звонков",
        "📅 Сабақ кестесі", "🎓 Қабылдау комиссиясы", "📞 Байланыс", "⏰ Қоңырау кестесі",
        "🔙 Назад", "🔙 Артқа", "🌐 Сменить язык", "🌐 Тілді өзгерту"
    ]:
        return

    user_id = message.from_user.id
    lang = user_languages.get(user_id, "ru")
    prompt = message.text.strip()

    await message.answer("⏳ Думаю..." if lang == "ru" else "⏳ Ойланып жатырмын...")
    reply = await generate_reply(prompt, lang)

    if not reply or "error" in reply.lower():
        reply = "⚠️ Не удалось получить ответ от ИИ." if lang == "ru" else "⚠️ ЖИ жауап бере алмады."

    await message.answer(reply)

# --- Запуск ---
async def main():
    logger.info("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

