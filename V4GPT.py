import os
import logging
import asyncio
import requests
import google.generativeai as genai
from openai import OpenAI
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
            [KeyboardButton(text="📞 Контакты")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел..."
    )

# --- Генерация ответа через OpenRouter с автоматическим fallback ---
async def generate_reply(prompt: str) -> str:
    # 1️⃣ Попытка — OpenRouter
    try:
        logger.info("🧠 Попытка: OpenRouter (deepseek-chat-v3-0324:free)")

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

        if response.status_code == 200:
            rj = response.json()
            logger.info("✅ Используется OpenRouter (deepseek-chat)")
            return rj["choices"][0]["message"]["content"].strip()
        else:
            raise Exception(response.text)

    except Exception as e1:
        logger.warning(f"⚠️ OpenRouter недоступен: {e1}")

    # 2️⃣ Попытка — OpenAI
    try:
        if OPENAI_API_KEY:
            logger.info("🔄 Переключение на OpenAI (gpt-4o-mini)...")
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": COLLEGE_RULES},
                    {"role": "user", "content": prompt}
                ],
            )
            logger.info("✅ Используется OpenAI (gpt-4o-mini)")
            return response.choices[0].message.content.strip()
    except Exception as e2:
        logger.warning(f"⚠️ Ошибка OpenAI: {e2}")

    # 3️⃣ Попытка — Gemini
    try:
        if GEMINI_API_KEY:
            logger.info("🔄 Переключение на Gemini (1.5-flash)...")
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            reply = model.generate_content(f"{COLLEGE_RULES}\n\nПользователь: {prompt}")
            logger.info("✅ Используется Gemini (1.5-flash)")
            return reply.text.strip()
    except Exception as e3:
        logger.error(f"❌ Все модели недоступны: {e3}")

    # 4️⃣ Ничего не сработало
    return "😔 Все модели сейчас недоступны. Попробуй позже."

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

@dp.message(F.text == "🎓 Приёмная комиссия")
async def show_admission(message: Message):
    await message.answer(
        "🎓 <b>Приёмная комиссия</b>\n\nСписок специальностей и документы для поступления доступны на сайте колледжа.",
        parse_mode=ParseMode.HTML
    )

# --- Чат-режим ---
@dp.message()
async def chat(message: Message):
    prompt = message.text
    reply = await generate_reply(prompt)
    await message.answer(reply)

# --- Основной запуск ---
async def main():
    logger.info("✅ Бот запущен и готов к работе (OpenRouter + резерв OpenAI/Gemini)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
