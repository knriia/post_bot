from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import httpx

from config import settings
from consts import (
    WELCOME_MESSAGE,
    CREDENTIALS_ENTRY_MESSAGE,
    USE_COMMAND_LOGIN_MESSAGE,
    GET_POSTS_ERROR_MESSAGE,
)


API_URL = settings.API_URL
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Оброботчик команды /start

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    """
    user_id = update.message.from_user.id
    await update.message.reply_text(WELCOME_MESSAGE)


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Оброботчик команды /login

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    """
    user_id = update.message.from_user.id
    await update.message.reply_text(CREDENTIALS_ENTRY_MESSAGE)
    user_sessions[user_id] = {'awaiting_credentials': True}


async def get_posts(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """
    Оброботчик команды /login

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    :param page: Номер страницы
    """
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    user_data = user_sessions.get(user_id, {})

    if not user_data.get('authenticated'):
        if update.callback_query:
            await update.callback_query.answer(USE_COMMAND_LOGIN_MESSAGE, show_alert=True)
        else:
            await update.message.reply_text(USE_COMMAND_LOGIN_MESSAGE)
        return

    limit = 5
    token = user_data['token']

    headers = {'Authorization': f'Bearer {token}'}

    async with httpx.AsyncClient() as client:
        try:
            posts_response = await client.get(
                f'{API_URL}/posts/read_all?skip={page * limit}&limit={limit}',
                headers=headers
            )
            posts = posts_response.json()
            count_response = await client.get(
                f'{API_URL}/posts/count',
                headers=headers
            )
            total_posts = count_response.json()['total']
        except Exception as e:
            await update.message.reply_text(GET_POSTS_ERROR_MESSAGE.format(str(e)))
            return

    keyboard = [
        [InlineKeyboardButton(post['title'], callback_data=f'post_{post['id']}')]
        for post in posts
    ]

    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton('⬅️ Назад', callback_data=f'page_{page - 1}')
        )
    if (page + 1) * limit < total_posts:
        pagination_buttons.append(
            InlineKeyboardButton('Вперед ➡️', callback_data=f'page_{page + 1}')
        )

    if pagination_buttons:
        keyboard.append(pagination_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = 'У вас нет опубликованных постов!'
    if total_posts > 0:
        message_text = (
            f'Страница {page + 1}\n'
            f'Показано {len(posts)} из {total_posts} постов\n\n'
            'Выберите пост:'
        )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )
