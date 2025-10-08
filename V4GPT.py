import os
import logging
import asyncio
import requests
import google.generativeai as genai
from openai import OpenAI
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# 🔧 --- НАСТРОЙКИ ---
BOT_TOKEN = "8407576281:AAF0lofeJQxBxsxEoYrMimB4ACAtVVyHN9w"
OPENAI_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyBSeT4fCI0wphjsujGkfFJ9VkexhUiKveE"
OPENROUTER_KEY = "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"

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Инициализация бота ---
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# --- Инициализация OpenAI клиента ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- СИСТЕМНАЯ ИНСТРУКЦИЯ ДЛЯ ИИ ---
COLLEGE_RULES = (
    "Ты — виртуальный помощник Карагандинского колледжа технологий и сервиса (ККТиС). "
    "Отвечай только на вопросы, связанные с колледжем, образованием, приёмом, расписанием, "
    "специальностями, контактами и студенческой жизнью. "
    "Если вопрос не касается колледжа или образования — вежливо откажись отвечать, "
    "например: «Извините, я могу отвечать только на вопросы, связанные с колледжем ККТиС.» "
    "Отвечай дружелюбно, кратко и информативно."
)


async def generate_reply(prompt: str) -> str:
    """
    Универсальная функция генерации текста.
    Пытается использовать OpenAI → Gemini → OpenRouter.
    Ограничена только тематикой ККТиС.
    """
    try:
        logger.info("🧠 Используется OpenAI (GPT-4o-mini)")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": COLLEGE_RULES},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        err = str(e)
        logger.warning(f"⚠️ Ошибка OpenAI: {err}")

        if "insufficient_quota" in err or "429" in err:
            # Пробуем Gemini
            try:
                logger.info("🔄 Переключение на Gemini...")
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                reply = model.generate_content(f"{COLLEGE_RULES}\n\nПользователь: {prompt}")
                return reply.text.strip()
            except Exception as e2:
                logger.warning(f"⚠️ Ошибка Gemini: {e2}")

                # Пробуем OpenRouter
                try:
                    logger.info("🔄 Переключение на OpenRouter...")
                    headers = {
                        "Authorization": f"Bearer {OPENROUTER_KEY}",
                        "Content-Type": "application/json",
                    }
                    data = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": COLLEGE_RULES},
                            {"role": "user", "content": prompt}
                        ],
                    }
                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=60
                    )
                    rj = resp.json()
                    return rj["choices"][0]["message"]["content"].strip()
                except Exception as e3:
                    logger.error(f"❌ Все провайдеры недоступны: {e3}")
                    return "😔 Все модели сейчас недоступны. Попробуй позже."
        else:
            return f"⚠️ Ошибка: {err}"


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет! Я виртуальный помощник Карагандинского колледжа технологий и сервиса (ККТиС). "
        "Задайте вопрос о поступлении, расписании или студенческой жизни."
    )


@dp.message()
async def chat(message: Message):
    prompt = message.text
    reply = await generate_reply(prompt)
    await message.answer(reply)


async def main():
    logger.info("✅ Бот запущен и готов к работе! Только по тематике ККТиС.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

