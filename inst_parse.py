from aiogram.types import FSInputFile
from playwright.async_api import async_playwright
import aiohttp
import asyncio
import os
import yt_dlp
from aiogram import Bot
from dotenv import load_dotenv
import os
import re
from db import save_instagram_post, post_exists, get_instagram_profile
from kb import public_post_kb

load_dotenv()

TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

async def login_instagram(username, password, bot: Bot):
    """Авторизация в Instagram"""
    async with async_playwright() as p:
        context  = await p.chromium.launch_persistent_context(
                user_data_dir="inst_profile",
                headless=False # видимый браузер, чтобы можно было авторизоваться вручную
            )
        
        page = await context.new_page()
        try:
            await page.goto('https://www.instagram.com/accounts/login/')
            
            
            await page.fill('input[name="username"]', username)
            await asyncio.sleep(1)
            await page.fill('input[name="password"]', password)
            await asyncio.sleep(1)
            
            await page.click('button[type="submit"]')
            await asyncio.sleep(5)

        
            print("✅ Успешный вход!")
            return True
            
        except Exception as e:
            await bot.send_message(os.getenv("TARGET_CHAT_ID"), "❌ Ошибка авторизации")
            os.remove("inst_profile")
            return False
        finally:
            await context.close()

async def download_instagram_media(url, output_dir="downloads"):
    """Скачивание медиа с Instagram по ссылке"""
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, 'instagram_video.mp4'),
        'format': 'best',
        'noplaylist': True,
    }
    
    try:
        # yt-dlp синхронная, поэтому запускаем в отдельном потоке
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        print(f"✅ Скачано видео")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def inst_parse(bot: Bot):
    """Упрощенная версия для скачивания первого поста и рилса"""
    while True:
     
        if not os.path.exists("inst_profile"):
                await bot.send_message(os.getenv("TARGET_CHAT_ID"), "❌ Профиль Instagram не найден")
                await asyncio.sleep(60)
                continue
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                        user_data_dir="inst_profile",
                        headless=False 
                    )
            page = await context.new_page()
         
            try:
                    
                    os.makedirs('downloads', exist_ok=True)
                    profiles = await get_instagram_profile()
                    print(profiles)
                    if not profiles:
                        await bot.send_message(os.getenv("TARGET_CHAT_ID"), "❌ Пустой список аккаунтов")
                        await asyncio.sleep(60)
                        continue
                    
                    for profile in profiles:
                        await page.goto(profile)
                        await asyncio.sleep(4)
                    
                        # Скачиваем первый пост
                        print("Скачиваем первый пост...")
                        first_post_all = await page.query_selector_all('a.x1i10hfl')
                        
                            
                        if first_post_all:
                            for first_post in first_post_all:
                                if await first_post.query_selector('img.xpdipgo'):
                                    print("Фото профиля")
                                    continue
                                if await first_post.query_selector('svg[aria-label="Значок прикрепленной публикации"], svg[aria-label="Pinned post icon"]'):
                                    print("Закреплено")
                                    continue
                                
                                post_url = await first_post.get_attribute('href')
                                if await post_exists(post_url):
                                    print("Пост уже скачан")
                                    break
                                
                                
                                
                                first_post_reel = await first_post.query_selector('svg[aria-label="Clip"], svg[aria-label="Клип"]')
                                
                            
                                first_post_photo = await first_post.query_selector('img[src*="https://scontent-"]')
                                
                                if first_post_reel:
                                    print("reel")
                                    await first_post_reel.click()
                                    await asyncio.sleep(2)
                                    title = await page.query_selector('._a9zr')
                                    title = await title.query_selector('h1[dir="auto"]')
                                    title = await title.inner_text()
                                    title = title.strip()[:500] + "..."+"\n"+page.url
                                    url = page.url
                                    success = await download_instagram_media(url)
                                    if success:
                                        video_path = 'downloads/instagram_video.mp4'
                                        video = FSInputFile(video_path)
                                        await bot.send_video(chat_id=os.getenv("TARGET_CHAT_ID"), video=video, caption=title, reply_markup=public_post_kb())
                                        await asyncio.sleep(3)
                                        os.remove('downloads/instagram_video.mp4')
                                        await save_instagram_post(post_url)
                                        break
                                
                                
                                
                                if first_post_photo:
                                    print("photo")
                                    url = await first_post_photo.get_attribute('src')
                                    await first_post.click()
                                    title = await page.query_selector('._a9zr')
                                    title = await title.query_selector('h1[dir="auto"]')
                                    title = await title.inner_text()
                                    title = title.strip()[:500] + "..."+"\n"+page.url
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(url) as response:
                                            if response.status == 200:
                                                content = await response.read()
                                                with open('downloads/photo.jpg', 'wb') as f:
                                                    f.write(content)
                                                photo = FSInputFile('downloads/photo.jpg')
                                                await bot.send_photo(chat_id=os.getenv("TARGET_CHAT_ID"), photo=photo, caption=title, reply_markup=public_post_kb())
                                                await asyncio.sleep(3)
                                                await save_instagram_post(post_url)
                                                os.remove('downloads/photo.jpg')
                                    break
                    
                    
                    
            except Exception as e:
                await bot.send_message(os.getenv("TARGET_CHAT_ID"), f"Ошибка: {e}")
        
        await asyncio.sleep(300)
        
        
        
async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    await inst_parse(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
