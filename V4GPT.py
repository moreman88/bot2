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
from bs4 import BeautifulSoup

# --- Загружаем переменные окружения ---
load_dotenv()

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SCHEDULE_URL = os.getenv("SCHEDULE_URL")
SITE_URL = os.getenv("SITE_URL", "https://kktis.kz/")

COLLEGE_NAME_RU = "Карагандинский колледж технологии и сервиса"
COLLEGE_NAME_KZ = "Қарағанды технология және сервис колледжі КМҚК"

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Кэш информации с сайта ---
website_cache = {"last_update": None, "content": ""}

# --- Функция для парсинга сайта колледжа ---
def fetch_website_info():
    """Получает информацию с официального сайта колледжа"""
    try:
        response = requests.get(SITE_URL, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Извлекаем текстовый контент (можно настроить под структуру сайта)
            text_content = soup.get_text(separator=' ', strip=True)
            return text_content[:3000]  # Ограничиваем размер
        return ""
    except Exception as e:
        logger.error(f"Ошибка при парсинге сайта: {e}")
        return ""

# --- База знаний колледжа ---
COLLEGE_KNOWLEDGE_BASE_RU = """
КОНТАКТНАЯ ИНФОРМАЦИЯ:
📍 Адрес: Караганда, ул. Затаевича, 75
☎️ Телефон: 8-7212-37-58-44
✉️ Email: krg-koll-7092@bilim09.kz
🌐 Официальный сайт: https://kktis.kz/

ПРИЁМНАЯ КОМИССИЯ:
📞 Әмірханова М.А. — 8-701-842-25-36
📞 Искакова Г.К. — 8-700-145-45-36
⏰ График работы: Понедельник–Пятница: 08:00–17:00

СПЕЦИАЛЬНОСТИ:
💻 Цифровая техника — на базе 11 класса, 10 месяцев
✂️ Парикмахерское искусство — на базе 9 класса, 2 года 10 месяцев
👗 Швейное производство и моделирование одежды — на базе 9 класса, 2 года 10 месяцев
🧵 Портной — на базе 9 класса, 2 года 10 месяцев
👞 Обувное дело — на базе ТиПО, 10 месяцев
💼 Офис-менеджер — на базе 11 класса, 10 месяцев

ДОКУМЕНТЫ ДЛЯ ПОСТУПЛЕНИЯ:
1️⃣ Заявление
2️⃣ Документ об образовании
3️⃣ Фото 3×4 (4 шт.)
4️⃣ Медицинская справка 075У

РАСПИСАНИЕ ЗВОНКОВ:
Понедельник:
- Кураторский час: 09:00–09:45
- 1 пара: 09:50–11:20
- 2 пара: 11:40–13:10
- 3 пара: 13:30–15:00

Вторник–Пятница:
- 1 пара: 09:00–10:30
- 2 пара: 10:40–12:10
- 3 пара: 12:30–14:00
- 4 пара: 14:20–15:50
"""

COLLEGE_KNOWLEDGE_BASE_KZ = """
БАЙЛАНЫС АҚПАРАТЫ:
📍 Мекенжайы: Қарағанды қ., Затаевич к., 75
☎️ Телефон: 8-7212-37-58-44
✉️ Email: krg-koll-7092@bilim09.kz
🌐 Ресми сайт: https://kktis.kz/

ҚАБЫЛДАУ КОМИССИЯСЫ:
📞 Әмірханова М.А. — 8-701-842-25-36
📞 Искакова Г.К. — 8-700-145-45-36
⏰ Жұмыс кестесі: Дүйсенбі–Жұма: 08:00–17:00

МАМАНДЫҚТАР:
💻 Цифрлық техника — 11 сынып негізінде, 10 ай
✂️ Шаштараз өнері — 9 сынып негізінде, 2 жыл 10 ай
👗 Киім өндірісі және үлгілеу — 9 сынып негізінде, 2 жыл 10 ай
🧵 Тігінші — 9 сынып негізінде, 2 жыл 10 ай
👞 Аяқ киім ісі — ТиПО негізінде, 10 ай
💼 Офис-менеджер — 11 сынып негізінде, 10 ай

ТҮСУ ҮШІН ҚАЖЕТТІ ҚҰЖАТТАР:
1️⃣ Өтініш
2️⃣ Білім туралы құжат
3️⃣ 3x4 фото (4 дана)
4️⃣ 075У мед. анықтама

ҚОҢЫРАУ КЕСТЕСІ:
Дүйсенбі:
- Кураторлық сағат: 09:00–09:45
- 1-пара: 09:50–11:20
- 2-пара: 11:40–13:10
- 3-пара: 13:30–15:00

Сейсенбі–Жұма:
- 1-пара: 09:00–10:30
- 2-пара: 10:40–12:10
- 3-пара: 12:30–14:00
- 4-пара: 14:20–15:50
"""

# --- Системные инструкции (Prompt для ИИ) ---
def get_system_prompt(lang: str) -> str:
    knowledge_base = COLLEGE_KNOWLEDGE_BASE_KZ if lang == "kz" else COLLEGE_KNOWLEDGE_BASE_RU
    
    if lang == "kz":
        return f"""Сен — Қарағанды технология және сервис колледжінің виртуалды көмекшісісің.

МАҢЫЗДЫ ЕРЕЖЕЛЕР:
1. Тек колледжге қатысты сұрақтарға жауап бер (оқу, қабылдау, сабақ кестесі, мамандықтар, байланыс, студенттік өмір)
2. Егер сұрақ колледжге қатысы болмаса, былай жауап бер: «Кешіріңіз, мен тек колледжге қатысты сұрақтарға жауап бере аламын.»
3. МІНДЕТТІ ТҮРДЕ төмендегі ресми ақпаратты пайдалан
4. Ақпарат болмаса, ойдан шығарма. «Бұл туралы нақты мәлімет жоқ, байланыс телефондары арқылы анықтауға болады» деп жауап бер

РЕСМИ АҚПАРАТ:
{knowledge_base}

Ресми сайт: {SITE_URL}
Сабақ кестесі: {SCHEDULE_URL}

Жауаптарыңды қысқа, нақты және пайдалы етіп бер. Байланыс ақпаратын дұрыс көрсет."""
    else:
        return f"""Ты — виртуальный помощник Карагандинского колледжа технологии и сервиса (ККТиС).

ВАЖНЫЕ ПРАВИЛА:
1. Отвечай ТОЛЬКО на вопросы о колледже (образование, приём, расписание, специальности, контакты, студенческая жизнь)
2. Если вопрос не касается колледжа, вежливо откажись: «Извините, я могу отвечать только на вопросы о нашем колледже.»
3. ОБЯЗАТЕЛЬНО используй официальную информацию ниже
4. Не придумывай ответы! Если информации нет, скажи: «По этому вопросу нет точной информации, рекомендую уточнить по контактным телефонам»

ОФИЦИАЛЬНАЯ ИНФОРМАЦИЯ:
{knowledge_base}

Официальный сайт: {SITE_URL}
Расписание занятий: {SCHEDULE_URL}

Давай короткие, точные и полезные ответы. Всегда указывай правильные контактные данные."""

# --- Состояние языка ---
user_lang = {}

# --- Главная клавиатура ---
def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "kz":
        buttons = [
            [KeyboardButton(text="📅 Сабақ кестесі"), KeyboardButton(text="🎓 Қабылдау комиссиясы")],
            [KeyboardButton(text="📞 Байланыс"), KeyboardButton(text="⏰ Қоңырау кестесі")],
            [KeyboardButton(text="🌐 Тілді ауыстыру")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🎓 Приёмная комиссия")],
            [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="⏰ Расписание звонков")],
            [KeyboardButton(text="🌐 Сменить язык")],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- Кнопка назад ---
def get_back_keyboard(lang: str) -> ReplyKeyboardMarkup:
    if lang == "kz":
        button = KeyboardButton(text="🔙 Артқа")
    else:
        button = KeyboardButton(text="🔙 Назад")
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)

# --- Генерация ответа через OpenRouter ---
async def generate_reply(prompt: str, lang: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "X-Title": "KKTiS College Bot"
        }
        
        system_prompt = get_system_prompt(lang)
        
        data = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code}")
            return "⚠️ Сервер уақытша қол жетімсіз." if lang == "kz" else "⚠️ Ошибка при обращении к API."
        
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error in generate_reply: {e}")
        return "Қате орын алды." if lang == "kz" else "Произошла ошибка."

# --- /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "👋 Сәлеметсіз бе! / Здравствуйте!\n\n"
        "Пожалуйста, выберите язык общения / Тілді таңдаңыз 👇"
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇰🇿 Қазақ тілі")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=keyboard)

# --- Выбор языка ---
@dp.message(F.text.in_(["🇷🇺 Русский", "🇰🇿 Қазақ тілі"]))
async def select_language(message: Message):
    if message.text == "🇰🇿 Қазақ тілі":
        user_lang[message.from_user.id] = "kz"
        text = f"🇰🇿 Тіл қазақ тіліне ауыстырылды.\n\n🎓 <b>{COLLEGE_NAME_KZ}</b>\nТөменнен қажетті бөлімді таңдаңыз немесе сұрақ қойыңыз 👇"
    else:
        user_lang[message.from_user.id] = "ru"
        text = f"🇷🇺 Язык изменён на русский.\n\n🎓 <b>{COLLEGE_NAME_RU}</b>\nВыберите раздел или задайте вопрос 👇"
    await message.answer(text, reply_markup=get_main_keyboard(user_lang[message.from_user.id]))

# --- Смена языка ---
@dp.message(F.text.in_(["🌐 Сменить язык", "🌐 Тілді ауыстыру"]))
async def change_language(message: Message):
    current_lang = user_lang.get(message.from_user.id, "ru")
    new_lang = "kz" if current_lang == "ru" else "ru"
    user_lang[message.from_user.id] = new_lang
    text = (
        f"🇰🇿 Тіл қазақ тіліне ауыстырылды.\n\n🎓 <b>{COLLEGE_NAME_KZ}</b>\nТөменнен қажетті бөлімді таңдаңыз 👇"
        if new_lang == "kz"
        else f"🇷🇺 Язык изменён на русский.\n\n🎓 <b>{COLLEGE_NAME_RU}</b>\nВыберите нужный раздел 👇"
    )
    await message.answer(text, reply_markup=get_main_keyboard(new_lang))

# --- Назад ---
@dp.message(F.text.in_(["🔙 Назад", "🔙 Артқа"]))
async def go_back(message: Message):
    lang = user_lang.get(message.from_user.id, "ru")
    if lang == "kz":
        text = f"🎓 <b>{COLLEGE_NAME_KZ}</b>\nТөменнен қажетті бөлімді таңдаңыз 👇"
    else:
        text = f"🎓 <b>{COLLEGE_NAME_RU}</b>\nВыберите нужный раздел 👇"
    await message.answer(text, reply_markup=get_main_keyboard(lang))

# --- Расписание ---
@dp.message(F.text.in_(["📅 Расписание", "📅 Сабақ кестесі"]))
async def show_schedule(message: Message):
    lang = user_lang.get(message.from_user.id, "ru")
    text = (
        f"📅 <b>Сабақ кестесі</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Кестені ашу</a>\n\n🌐 {SITE_URL}"
        if lang == "kz"
        else f"📅 <b>Расписание занятий</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Открыть расписание</a>\n\n🌐 {SITE_URL}"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Контакты ---
@dp.message(F.text.in_(["📞 Контакты", "📞 Байланыс"]))
async def show_contacts(message: Message):
    lang = user_lang.get(message.from_user.id, "ru")
    text = (
        "📞 <b>Байланыс:</b>\n📍 Қарағанды, Затаевич к., 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz\n🌐 https://kktis.kz/"
        if lang == "kz"
        else "📞 <b>Контакты:</b>\n📍 Караганда, ул. Затаевича, 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kz\n🌐 https://kktis.kz/"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Приёмная комиссия ---
@dp.message(F.text.in_(["🎓 Приёмная комиссия", "🎓 Қабылдау комиссиясы"]))
async def show_admission(message: Message):
    lang = user_lang.get(message.from_user.id, "ru")
    text = (
        "🎓 <b>ҚАБЫЛДАУ КОМИССИЯСЫ</b>\n\nҚарағанды технология және сервис колледжі келесі мамандықтар бойынша оқуға шақырады:\n\n"
        "💻 Цифрлық техника — 11 сынып негізінде, 10 ай\n✂️ Шаштараз өнері — 9 сынып негізінде, 2 жыл 10 ай\n"
        "👗 Киім өндірісі және үлгілеу — 9 сынып негізінде, 2 жыл 10 ай\n🧵 Тігінші — 9 сынып негізінде, 2 жыл 10 ай\n"
        "👞 Аяқ киім ісі — ТиПО негізінде, 10 ай\n💼 Офис-менеджер — 11 сынып негізінде, 10 ай\n\n"
        "📋 Қажетті құжаттар:\n1️⃣ Өтініш\n2️⃣ Білім туралы құжат\n3️⃣ 3x4 фото (4 дана)\n4️⃣ 075У мед. анықтама\n\n"
        "📍 Мекенжайы: Қарағанды қ., Затаевич к., 75\n"
        "📞 Әмірханова М.А. — 8-701-842-25-36\n📞 Искакова Г.К. — 8-700-145-45-36\n⏰ Дс–Жм: 08:00–17:00"
        if lang == "kz"
        else
        "🎓 <b>ПРИЁМНАЯ КОМИССИЯ</b>\n\nКарагандинский колледж технологии и сервиса приглашает абитуриентов:\n\n"
        "💻 Цифровая техника — 11 кл., 10 мес.\n✂️ Парикмахерское искусство — 9 кл., 2 г. 10 мес.\n"
        "👗 Швейное производство и моделирование одежды — 9 кл., 2 г. 10 мес.\n🧵 Портной — 9 кл., 2 г. 10 мес.\n"
        "👞 Обувное дело — 10 мес.\n💼 Офис-менеджер — 11 кл., 10 мес.\n\n"
        "📋 Документы:\n1️⃣ Заявление\n2️⃣ Документ об образовании\n3️⃣ Фото 3×4 (4 шт.)\n4️⃣ Медсправка 075У\n\n"
        "📍 Адрес: Караганда, ул. Затаевича, 75\n📞 Әмірханова М.А. — 8-701-842-25-36\n📞 Искакова Г.К. — 8-700-145-45-36\n⏰ Пн–Пт: 08:00–17:00"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Расписание звонков ---
@dp.message(F.text.in_(["⏰ Расписание звонков", "⏰ Қоңырау кестесі"]))
async def show_bell_schedule(message: Message):
    lang = user_lang.get(message.from_user.id, "ru")
    if lang == "kz":
        text = (
            "<b>⏰ Қоңырау кестесі</b>\n\n<b>Дүйсенбі:</b>\nКураторлық сағат — 09:00 – 09:45\n"
            "Үзіліс — 5 мин\n1-пара — 09:50 – 11:20\n\nТүскі ас (1-ағын) — 20 мин\n2-пара — 11:40 – 13:10\n\n"
            "Түскі ас (2-ағын) — 20 мин\n3-пара — 13:30 – 15:00\n\n——————————————\n<b>Сейсенбі – Жұма:</b>\n"
            "1-пара — 09:00 – 10:30\nҮзіліс — 10 мин\n2-пара — 10:40 – 12:10\n\nТүскі ас (1-ағын) — 20 мин\n"
            "3-пара — 12:30 – 14:00\n\nТүскі ас (2-ағын) — 20 мин\n4-пара — 14:20 – 15:50"
        )
    else:
        text = (
            "<b>⏰ Расписание звонков</b>\n\n<b>Понедельник:</b>\nКураторский час — 09:00 – 09:45\n"
            "Перемена — 5 мин\n1 пара — 09:50 – 11:20\n\nОбед (1-й поток) — 20 мин\n2 пара — 11:40 – 13:10\n\n"
            "Обед (2-й поток) — 20 мин\n3 пара — 13:30 – 15:00\n\n——————————————\n<b>Вторник – Пятница:</b>\n"
            "1 пара — 09:00 – 10:30\nПеремена — 10 мин\n2 пара — 10:40 – 12:10\n\nОбед (1-й поток) — 20 мин\n"
            "3 пара — 12:30 – 14:00\n\nОбед (2-й поток) — 20 мин\n4 пара — 14:20 – 15:50"
        )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_back_keyboard(lang))

# --- Чат с ИИ ---
@dp.message()
async def chat(message: Message):
    lang = user_lang.get(message.from_user.id, "ru")
    prompt = message.text
    
    # Отправляем индикатор набора текста
    await bot.send_chat_action(message.chat.id, "typing")
    
    reply = await generate_reply(prompt, lang)
    await message.answer(reply)

# --- Основной запуск ---
async def main():
    logger.info("✅ Бот запущен и готов к работе!")
    logger.info(f"📍 Официальный сайт: {SITE_URL}")
    
    # Опционально: загрузка информации с сайта при старте
    # website_info = fetch_website_info()
    # if website_info:
    #     logger.info("📄 Информация с сайта загружена")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
