from aiogram import Bot, Dispatcher
import asyncio
from dotenv import load_dotenv
import os
from telethon_bot import client, register_telethon_handlers
from bot_handler import bot_router
from parse_twitter import parse_twitter
from inst_parse import inst_parse
from db import init_db
from utils import forward_worker

load_dotenv()

PHONE = os.getenv("PHONE_NUMBER")
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
dp.include_router(bot_router)



async def start_telethon():
    await client.start(phone=PHONE)
    register_telethon_handlers(client, bot)
    await client.run_until_disconnected()
    
async def start_aiogram():
    await dp.start_polling(bot)

async def main():
    print("Бот запущен")
    await init_db()
    
    tasks = [
        asyncio.create_task(start_telethon()),
        asyncio.create_task(start_aiogram()),
        asyncio.create_task(inst_parse(bot)),     
        asyncio.create_task(parse_twitter(bot)),
        asyncio.create_task(forward_worker(bot, os.getenv("TARGET_CHANNEL"))),
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())