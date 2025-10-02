import asyncio
from telethon import TelegramClient, events
from aiogram import Bot
import re
import os
from dotenv import load_dotenv
from aiogram.types import InputMediaPhoto, InputMediaVideo, BufferedInputFile
from collections import defaultdict
from db import save_channel, get_channels
from channels import watched_channels


load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")



client = TelegramClient("session_name", API_ID, API_HASH)


async def add_channel_by_link(link: str):
    global watched_channels
    match = re.match(r"(?:https?://)?t\.me/(?:joinchat/)?([a-zA-Z0-9_]+)", link)
    if not match:
        raise ValueError("Неверная ссылка на канал")
    username = match.group(1)

    if username in watched_channels:
        return None

    # сохраняем в базу
    await save_channel(username)

    # добавляем в текущий сет
    watched_channels.add(username)
    
    print(f"Добавлен канал {username}, всего каналов: {len(watched_channels)}")
    return username

def register_telethon_handlers(client, bot: Bot):
    # --- одиночные сообщения ---
    @client.on(events.NewMessage())
    async def handler(event):
        if not event.chat or (
            event.chat.username not in watched_channels
            and str(event.chat_id) not in watched_channels
        ):
            return

        msg = event.message
        if msg.grouped_id:
            return
        # --- Текст ---
        if msg.text and not msg.media:
            await bot.send_message(TARGET_CHAT_ID, msg.text)

        # --- Фото ---
        elif msg.photo:
            data = await msg.download_media(file=bytes)
            photo = BufferedInputFile(data, filename="image.jpg")
            caption = msg.text or ""
            await bot.send_photo(TARGET_CHAT_ID, photo, caption=caption)

        # --- Видео ---
        elif msg.video:
            data = await msg.download_media(file=bytes)
            video = BufferedInputFile(data, filename="video.mp4")
            caption = msg.text or ""
            await bot.send_video(TARGET_CHAT_ID, video, caption=caption)

    # --- альбомы (медиагруппы) ---
    @client.on(events.Album())
    async def album_handler(event):
        if not event.chat or (
            event.chat.username not in watched_channels
            and str(event.chat_id) not in watched_channels
        ):
            return

        media_group = []
        first_caption_added = False

        for m in event.messages:
            caption = None
            if not first_caption_added and m.text:
                caption = m.text
                first_caption_added = True

            if m.photo:
                b = await m.download_media(file=bytes)
                file = BufferedInputFile(b, "photo.jpg")
                media_group.append(InputMediaPhoto(media=file, caption=caption))

            elif m.video:
                b = await m.download_media(file=bytes)
                file = BufferedInputFile(b, "video.mp4")
                media_group.append(InputMediaVideo(media=file, caption=caption))
                
        print(media_group)
        if media_group:
            await bot.send_media_group(TARGET_CHAT_ID, media_group)