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
COLLEGE_NAME = os.getenv("COLLEGE_NAME", "Карагандинский колледж технологий и сервиса")
SCHEDULE_URL = os.getenv("SCHEDULE_URL")
SITE_URL = os.getenv("SITE_URL")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Системная инструкция ---
COLLEGE_RULES = (
    "Ты — виртуальный помощник Карагандинского колледжа технологий и сервиса (ККТиС). "
    "Отвечай только на вопросы, связанные с колледжем, образованием, приёмом, расписанием, "
    "специальностями, контактами и студенческой жизнью. "
    "Если вопрос не касается колледжа или образования — вежливо откажись отвечать, "
    "например: «Извините, я могу отвечать только на вопросы, связанные с колледжем ККТиС.» "
    "Отвечай дружелюбно, кратко и информативно."
)

# --- Клавиатура ---
def get_main_keyboard() -> ReplyKeyboardMarkup:
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
        logger.info("🧠 Отправка запроса в OpenRouter...")

        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "X-Title": "KKTiS College Bot"
        }

        data = {
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [
                {"role": "system", "content": COLLEGE_RULES},
                {"role": "user", "content": prompt},
            ],
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
    welcome_text = (
        f"🎓 <b>{COLLEGE_NAME}</b>\n\n"
        f"👋 Здравствуйте, <b>{message.from_user.first_name}</b>!\n\n"
        f"Я — официальный бот колледжа. Выберите нужный раздел 👇"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# --- Кнопки ---
@dp.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    await message.answer(
        f"📅 <b>Расписание занятий:</b>\n\n🔗 <a href='{SCHEDULE_URL}'>Открыть расписание</a>\n\n🌐 {SITE_URL}",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    await message.answer(
        "📞 <b>Контакты:</b>\nКараганда, ул. Затаевича, 75\n☎️ 8-7212-37-58-44\n✉️ krg-koll-7092@bilim09.kzu.kz",
        parse_mode=ParseMode.HTML
    )

```python
@dp.message(F.text == "🎓 Приёмная комиссия")
async def show_admission(message: Message):
    """
    Обработчик кнопки "Приёмная комиссия"
    Отправляет всю информацию одним сообщением
    """
    admission_text = (
        f"╔═══════════════════════╗\n"
        f"   🎓 <b>ПРИЁМНАЯ КОМИССИЯ</b>\n"
        f"╚═══════════════════════╝\n\n"
        f"<b>КГКП «Карагандинский колледж технологии и сервиса» осуществляет набор студентов на новый учебный год по следующим специальностям:</b>\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ 💻 <b>ЦИФРОВАЯ ТЕХНИКА</b>\n"
        f"┃    (целевая группа)\n"
        f"┃    • На базе 11 кл. — 10 мес.\n"
        f"┃\n"
        f"┃ ✂️ <b>ПАРИКМАХЕРСКОЕ ИСКУССТВО</b>\n"
        f"┃    • На базе 9 кл. — 2 г. 10 мес.\n"
        f"┃    • На базе ТиПО — 10 мес.\n"
        f"┃\n"
        f"┃ 👗 <b>ШВЕЙНОЕ ПРОИЗВОДСТВО И МОДЕЛИРОВАНИЕ ОДЕЖДЫ</b>\n"
        f"┃    • На базе 9 кл. — 2 г. 10 мес.\n"
        f"┃    • На базе ТиПО — 10 мес.\n"
        f"┃\n"
        f"┃ 🧵 <b>ПОРТНОЙ</b>\n"
        f"┃    • На базе 9 кл. — 2 г. 10 мес.\n"
        f"┃\n"
        f"┃ 👞 <b>ОБУВНОЕ ДЕЛО</b>\n"
        f"┃    • На базе ТиПО — 10 мес.\n"
        f"┃\n"
        f"┃ 💼 <b>ОФИС-МЕНЕДЖЕР</b>\n"
        f"┃    • На базе 11 кл. — 10 мес.\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"╔═══════════════════════╗\n"
        f"   📋 <b>ДОКУМЕНТЫ ДЛЯ ПОСТУПЛЕНИЯ</b>\n"
        f"╚═══════════════════════╝\n\n"
        f"1️⃣ Заявление о приёме документов\n"
        f"2️⃣ Подлинник документа об образовании (аттестат, диплом)\n"
        f"3️⃣ Фотографии 3×4 см — 4 шт.\n"
        f"4️⃣ Медицинская справка формы № 075У\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ 🌍 <b>Для иностранных граждан и лиц без гражданства:</b>\n"
        f"┃ • Вид на жительство\n"
        f"┃ • Удостоверение лица без гражданства\n"
        f"┃ • Удостоверение беженца\n"
        f"┃ • Удостоверение кандаса\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"╔═══════════════════════╗\n"
        f"   📤 <b>СПОСОБЫ ПОДАЧИ ДОКУМЕНТОВ</b>\n"
        f"╚═══════════════════════╝\n\n"
        f"1️⃣ Лично в колледже\n"
        f"   📍 г. Караганда, ул. Затаевича, 75\n\n"
        f"2️⃣ Через портал электронного правительства 🌐 <b>www.egov.kz</b>\n\n"
        f"3️⃣ Через платформу <b>My College</b>\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ 📞 <b>ПРИЁМНАЯ КОМИССИЯ</b>\n"
        f"┃ 👤 Әмірханова М.А. — ☎️ 8-701-842-25-36\n"
        f"┃ 👤 Искакова Г.К. — ☎️ 8-700-145-45-36\n"
        f"┃ ⏰ Пн–Пт: 8:00–17:00\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"✅ <b>Результат:</b> Расписка о приёме документов\n\n"
        f"📚 <b>Мы ждём вас в нашем колледже!</b>"
    )

    await message.answer(admission_text, parse_mode=ParseMode.HTML)
```


# --- Новая кнопка: Расписание звонков ---
@dp.message(F.text == "⏰ Расписание звонков")
async def show_bell_schedule(message: Message):
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

# --- Чат-режим ---
@dp.message()
async def chat(message: Message):
    prompt = message.text
    reply = await generate_reply(prompt)
    await message.answer(reply)

# --- Основной запуск ---
async def main():
    logger.info("✅ Бот запущен и готов к работе через OpenRouter!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


