from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Войти в аккаунты", callback_data="login")
    kb.button(text="Добавить канал", callback_data="add_channel")
    kb.adjust(1)
    return kb.as_markup()


def login_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Инстаграм", callback_data="login_instagram")
    kb.button(text="Твиттер", callback_data="login_twitter")
    kb.button(text="Назад", callback_data="back_to_start")
    kb.adjust(1)
    return kb.as_markup()


def add_channel_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Телеграм", callback_data="add_channel_telegram")
    kb.button(text="Инстаграм", callback_data="add_channel_instagram")
    kb.button(text="Твиттер", callback_data="add_channel_twitter")
    kb.button(text="Назад", callback_data="back_to_start")
    kb.adjust(1)
    return kb.as_markup()

def public_post_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Опубликовать", callback_data="public_post")
    kb.button(text="Редактировать", callback_data="edit_post")
    kb.button(text="Отложить", callback_data="delay_post")
    kb.adjust(1)
    return kb.as_markup()



