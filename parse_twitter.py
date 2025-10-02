from aiogram.types import FSInputFile
from playwright.async_api import async_playwright
from kb import public_post_kb
import asyncio
import re
import yt_dlp
import os
from aiogram import Bot
from dotenv import load_dotenv
from db import save_tweet, tweet_exists, get_twitter_profile


load_dotenv()

SAVE_FOLDER = "tweets_media"
ADMIN_ID = os.getenv("ADMIN_ID")
os.makedirs(SAVE_FOLDER, exist_ok=True)


async def login_twitter(login, user_name, password, bot: Bot):
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="X_profile",
                headless=False # видимый браузер, чтобы можно было авторизоваться вручную
            )
            page = await context.new_page()
            await page.goto("https://x.com/?logout=1759150059393")
            await page.get_by_test_id("loginButton").click()
            await page.locator('input[autocomplete="username"]').type(login, delay=100)
            
            await page.get_by_role("button", name=re.compile("Next|Далее")).click()
            try:
                user_input = await page.wait_for_selector('[data-testid="ocfEnterTextTextInput"]', timeout=5000)
                if user_input:
                    await user_input.click()
                    await user_input.type(user_name, delay=100)
                    next_btn = await page.wait_for_selector('[data-testid="ocfEnterTextNextButton"]', timeout=5000)
                    if next_btn:
                        await next_btn.click()
            except Exception as e:
                print(f"⚠️ Не удалось найти поле ввода имени пользователя: {e}")
            
            await page.locator('input[autocomplete="current-password"]').type(password, delay=100)
            await page.get_by_test_id("LoginForm_Login_Button").click() 
            await page.wait_for_timeout(5000)
            print("Успешно авторизован")
            await context.close()
            return True
           
        except Exception as e:
            await bot.send_message(int(ADMIN_ID), "Не удалось авторизоваться")
            await context.close()
            os.remove("X_profile")
            return False
        

async def parse_twitter(bot: Bot):
    while True:
        if not os.path.exists("X_profile"):
            await bot.send_message(ADMIN_ID, "❌ Профиль Twitter не найден")
            await asyncio.sleep(30)
            continue
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="X_profile",
                headless=False
            )
            page = await context.new_page()
            
            urls = await get_twitter_profile()
            if not urls:
                await bot.send_message(ADMIN_ID, "❌ Пустой список аккаунтов Twitter")
                await asyncio.sleep(60)
                continue
            for url in urls:
                await page.goto(url)
                await page.wait_for_timeout(5000)
                try:
                    section =  await page.wait_for_selector('section[role="region"]' , timeout=10000)
                    section = await section.query_selector_all("article")
                
                    for post in  section:
                        pinned = await post.query_selector('div[data-testid="socialContext"]')
                        if pinned:
                            print("Сообщение закреплено, пропускаем")
                            continue
                    
                        text_tweet_button = await post.query_selector('div[data-testid="tweetText"]')
                        text_tweet = await text_tweet_button.inner_text()
                        
                        
                        if await tweet_exists(text_tweet):
                            print("Твит уже существует, пропускаем")
                            break
                        await save_tweet(text_tweet)
                        await text_tweet_button.click()
                        await page.wait_for_timeout(3000)
                        
                        get_url = page.url
                        text_tweet = text_tweet.strip()+ "\n"+get_url
                        video_player = await post.query_selector('div[data-testid="videoPlayer"]')
                        img_elem = await post.query_selector('img[src*="pbs.twimg.com/media/"]')
                    
                        if video_player:
                            print("Видео найдено")
                            video_filename = os.path.join(SAVE_FOLDER, "tweet_video.mp4")

                            ydl_opts = {
                                "outtmpl": video_filename,               
                                "merge_output_format": "mp4",
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([get_url])
                            print("Видео сохранено")    
                            file = FSInputFile(os.path.join(SAVE_FOLDER, "tweet_video.mp4"))
                            await bot.send_video(ADMIN_ID, file, caption=text_tweet, reply_markup=public_post_kb())
                            os.remove(os.path.join(SAVE_FOLDER, "tweet_video.mp4"))
                            break
                                
                        if img_elem:
                            img_url = await img_elem.get_attribute("src")
                            import requests
                            response = requests.get(img_url)
                            with open(os.path.join(SAVE_FOLDER, "tweet_image.jpg"), "wb") as f:
                                f.write(response.content)
                            print("Изображение сохранено")
                            file = FSInputFile(os.path.join(SAVE_FOLDER, "tweet_image.jpg"))    
                            await bot.send_photo(ADMIN_ID, file, caption=text_tweet, reply_markup=public_post_kb())
                            os.remove(os.path.join(SAVE_FOLDER, "tweet_image.jpg"))
                            break
                        
                        await bot.send_message(ADMIN_ID, text_tweet, reply_markup=public_post_kb())
                        break
                
                    
                except Exception as e:
                    print(e)
            
        await asyncio.sleep(300)
                
                   
                                
            
        
        



async def main():
    from main import bot
    #await login_twitter()
    await parse_twitter(bot)

if __name__ == "__main__":
    asyncio.run(main())
        