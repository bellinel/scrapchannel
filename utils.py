import asyncio
from aiogram import Bot

# Список сообщений, которые будем отправлять
forward_queue = []

async def add_to_forward_queue(bot: Bot, chat_id: int, message_id: int):
    """
    Добавляем сообщение в очередь: удаляем кнопки у оригинала,
    сохраняем ID для пересылки
    """
    try:
        # Удаляем кнопки
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        print(f"🗑 Кнопки удалены у сообщения {message_id}")

        # Добавляем в очередь
        forward_queue.append({
            "chat_id": chat_id,
            "message_id": message_id
        })
    except Exception as e:
        print(f"Ошибка при добавлении в очередь: {e}")


async def forward_worker(bot: Bot, to_chat_id: int):
    """
    Отправляем сообщения из очереди раз в минуту
    """
    while True:
        if forward_queue:
            task = forward_queue.pop(0)  # Берем первое сообщение
            try:
                await bot.forward_message(
                    chat_id=to_chat_id,
                    from_chat_id=task["chat_id"],
                    message_id=task["message_id"]
                )
                await bot.delete_message(task["chat_id"], task["message_id"])
                print(f"✅ Сообщение {task['message_id']} переслано в канал")
            except Exception as e:
                print(f"Ошибка при пересылке: {e}")
        await asyncio.sleep(60)  # ждем минуту перед отправкой следующего
