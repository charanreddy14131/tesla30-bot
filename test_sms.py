<<<<<<< HEAD
import asyncio
from telegram import Bot

# Hardcoded config (you can also use dotenv if needed)
cfg = {
    "TELEGRAM_BOT_TOKEN": "7905608996:AAHluhNj0xFma8NM0A7jqxlC9IZtVCpmKcg",
    "TELEGRAM_CHAT_ID": "5461738520"
}

async def send_telegram(text: str):
    bot = Bot(token=cfg["TELEGRAM_BOT_TOKEN"])
    await bot.send_message(chat_id=cfg["TELEGRAM_CHAT_ID"], text=text)

# Run the async function
asyncio.run(send_telegram("✅ Telegram connection successful from VS Code!"))
print("Message sent!")
=======
import asyncio
from telegram import Bot

# Hardcoded config (you can also use dotenv if needed)
cfg = {
    "TELEGRAM_BOT_TOKEN": "7905608996:AAHluhNj0xFma8NM0A7jqxlC9IZtVCpmKcg",
    "TELEGRAM_CHAT_ID": "5461738520"
}

async def send_telegram(text: str):
    bot = Bot(token=cfg["TELEGRAM_BOT_TOKEN"])
    await bot.send_message(chat_id=cfg["TELEGRAM_CHAT_ID"], text=text)

# Run the async function
asyncio.run(send_telegram("✅ Telegram connection successful from VS Code!"))
print("Message sent!")
>>>>>>> 5cde3a973f012585fa013d34f109ea456d8ac0de
