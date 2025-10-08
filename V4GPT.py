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
SCHEDULE_URL = os.getenv("SCHEDULE_URL", "https://docs.google.com/spreadsheets/...")
SITE_URL = os.getenv("SITE_URL", "https://kktis.kz")

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

# --- Главное меню ---
def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🎓 Приёмная комиссия")],
            [KeyboardButton(text="📞 Контакты")],
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
            "HTTP-Referer": "https://t.me/your_bot_username",  # ⚠️ Замени на @username твоего бота
            "X-Title": "KKTiS College Bot"
        }

        data = {
            "model": "deepseek/deepseek-chat-v3-0324:free",  # ✅ бесплатная и стабильная модель
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

        if response.status_code != 200:
            logger.error(f"❌ Ошибка OpenRouter ({response.status_code}): {response.text}")
            return "⚠️ Ошибка при обращении к OpenRouter API. Проверь ключ или попробуй позже."

        rj = response.json()
        return rj["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "⏳ Сервер OpenRouter не ответил вовремя. Попробуй позже."
    except Exception as e:
        logger.error(f"❌ Ошибка при работе с OpenRouter: {e}")
        return "😔 Не удалось получить ответ от модели. Попробуй позже."

# --- Команда /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f"🎓 <b>{COLLEGE_NAME}</b>\n\n"
        f"👋 Здравствуйте, <b>{message.from_user.first_name}</b>!\n\n"
        f"Я — официальный бот колледжа. Выберите нужный раздел 👇"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# --- Раздел «Расписание» ---
@dp.message(F.text == "📅 Расписание")
async def show_schedule(message: Message):
    await message.answer(
        f"📅 <b>Расписание занятий:</b>\n\n"
        f"🔗 <a href='{SCHEDULE_URL}'>Открыть расписание</a>\n\n"
        f"🌐 {SITE_URL}",
        disable_web_page_preview=True
    )

# --- Раздел «Контакты» ---
@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    await message.answer(
        "📞 <b>Контакты:</b>\n"
        "📍 Караганда, ул. Затаевича, 75\n"
        "☎️ 8-7212-37-58-44\n"
        "✉️ krg-koll-7092@bilim09.kzu.kz",
    )

# --- Раздел «Приёмная комиссия» ---
@dp.message(F.text == "🎓 Приёмная комиссия")
async def show_admission(message: Message):
    await message.answer(
        "🎓 <b>Приёмная комиссия</b>\n\n"
        "Список специальностей и документы для поступления доступны на сайте колледжа.",
    )

# --- Чат-режим ---
@dp.message()
async def chat(message: Message):
    prompt = message.text
    reply = await generate_reply(prompt)
    await message.answer(reply)

# --- Запуск бота ---
async def main():
    logger.info("✅ Бот запущен и готов к работе через OpenRouter!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
