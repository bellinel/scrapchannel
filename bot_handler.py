from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from yt_dlp import re
from kb import *
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from telethon_bot import add_channel_by_link
from db import save_instagram_profile, save_twitter_profile 
from inst_parse import login_instagram
from parse_twitter import login_twitter
import os
from dotenv import load_dotenv
import asyncio
from utils import add_to_forward_queue
load_dotenv()

bot_router = Router()

TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")



class AddChannel(StatesGroup):
    channel_name = State()
    channel_name = State()
    
class LoginInstagram(StatesGroup):
    login = State()
    password = State()

class LoginTwitter(StatesGroup):
    login = State()
    password = State()
    user_name = State()

class EditPost(StatesGroup):
    wait_text = State()

@bot_router.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Я бот для парсинга каналов", reply_markup=start_kb())
    
@bot_router.callback_query(F.data == "login")
async def login(callback: CallbackQuery):
    await callback.message.edit_text("Выберите платформу для входа", reply_markup=login_kb())
    

@bot_router.callback_query(F.data == "add_channel")
async def add_channel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите платформу для добавления канала", reply_markup=add_channel_kb())
    await state.set_state(AddChannel.channel_name)
    
@bot_router.callback_query(F.data.startswith("add_channel_"))
async def add_channel_name(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split("_")[2]
    await state.set_state(AddChannel.channel_name)
    await callback.message.edit_text("Введите ссылку на канал")
    await state.update_data(platform=platform)
    
@bot_router.message(AddChannel.channel_name)
async def add_channel_name(message: Message, state: FSMContext):
    channel_url = message.text
    data = await state.get_data()
    platform = data.get("platform")
    if platform == "telegram":
        result = await add_channel_by_link(channel_url)
        if result:
            await message.answer(f"Канал  добавлен")
        else:
            await message.answer("Канал уже добавлен")
    if platform == "instagram":
        result = await save_instagram_profile(channel_url)
        if result:
            await message.answer(f"Канал  добавлен")
        else:
            await message.answer("Канал уже добавлен")
    if platform == "twitter":
        result = await save_twitter_profile(channel_url)
        if result:
            await message.answer(f"Канал добавлен")
        else:
            await message.answer("Канал уже добавлен")
    await state.clear()
    
@bot_router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text("Привет! Я бот для парсинга каналов", reply_markup=start_kb())
    await callback.answer()

@bot_router.callback_query(F.data.startswith("login_"))
async def login(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split("_")[1]
    if platform == "instagram":
        await callback.message.edit_text("Введите логин Instagram")
        await state.set_state(LoginInstagram.login)
    if platform == "twitter":
        await callback.message.edit_text("Введите логин Twitter")
        await state.set_state(LoginTwitter.login)

@bot_router.message(LoginInstagram.login)
async def login_instagram_username(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(LoginInstagram.password)
    await message.answer("Введите пароль Instagram")

@bot_router.message(LoginInstagram.password)
async def login_instagram_password(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    login = data.get("login")
    password = message.text
    
    await message.answer("Вход в аккаунт Instagram...")
    success = await login_instagram(login, password, bot)
    if success:
        await message.answer("Успешный вход!")
    else:
        await message.answer("Ошибка авторизации")

@bot_router.message(LoginTwitter.login)
async def login_twitter_username(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(LoginTwitter.user_name)
    await message.answer("Введите имя пользователя Twitter")

@bot_router.message(LoginTwitter.user_name)
async def login_twitter_user_name(message: Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await state.set_state(LoginTwitter.password)
    await message.answer("Введите пароль Twitter")
    
@bot_router.message(LoginTwitter.password)
async def login_twitter_password(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    login = data.get("login")
    user_name = data.get("user_name")
    password = message.text
    
    await message.answer("Вход в аккаунт Twitter...")
    success = await login_twitter(login, user_name, password, bot)
    if success:
        await message.answer("Успешный вход!")
    else:
        await message.answer("Ошибка авторизации")
        
        

        
@bot_router.callback_query(F.data == "public_post")
async def public_post(callback: CallbackQuery, bot : Bot):
    message_id = callback.message.message_id
    
    await add_to_forward_queue(bot, callback.message.chat.id, message_id)
    await callback.answer('Пост cкоро будет опубликован')
    
@bot_router.callback_query(F.data == "delay_post")
async def delay_post(callback: CallbackQuery, bot : Bot):
    message_id = callback.message.message_id
    await bot.delete_message(callback.message.chat.id, message_id)
    await callback.answer('Пост отложен')
    
    
@bot_router.callback_query(F.data == "edit_post")
async def edit_post(callback: CallbackQuery,  state: FSMContext):
    message_id = callback.message.message_id
    await state.update_data(message_id=message_id)
    await state.set_state(EditPost.wait_text)
    await callback.message.answer("Введите текст для поста")
    
@bot_router.message(EditPost.wait_text)
async def edit_post_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    message_id = data.get("message_id")
    await state.clear()
    
    try:
        await bot.edit_message_text(message_id=message_id, chat_id=message.chat.id, text=message.text)
    except:
        await bot.edit_message_caption(message_id=message_id, chat_id=message.chat.id, caption=message.text)
    
    await bot.copy_message(chat_id = message.chat.id, from_chat_id=message.chat.id, message_id=message_id, reply_markup=public_post_kb())
    await bot.delete_message(message.chat.id, message_id)
    await message.answer('Пост отредактирован')

  

