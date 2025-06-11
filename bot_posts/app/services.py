from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import httpx

from comands import user_sessions
from config import settings
from consts import (
    USE_COMMAND_LOGIN_MESSAGE,
    NOT_FOUND_POST_MESSAGE,
    ERROR_RECEIVING_POST,
)


API_URL = settings.API_URL


async def show_post_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, post_id: int, page: int = 0):
    """
    Отображает фсю информацию о посте

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    :param post_id: id поста
    :param page: Страница пагинации с постом
    """
    user_id = update.callback_query.from_user.id
    user_data = user_sessions.get(user_id, {})

    if not user_data.get('authenticated'):
        await update.callback_query.answer(USE_COMMAND_LOGIN_MESSAGE, show_alert=True)
        return

    token = user_data['token']
    headers = {'Authorization': f'Bearer {token}'}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f'{API_URL}/posts/{post_id}',
                headers=headers
            )
            if response.status_code == 404:
                await update.callback_query.answer(NOT_FOUND_POST_MESSAGE, show_alert=True)
                return
            post = response.json()
        except Exception as e:
            await update.callback_query.answer(ERROR_RECEIVING_POST.format(str(e)), show_alert=True)
            return

    message = (
        f'📌 {post['title']}\n\n'
        f'📝 {post['content']}\n\n'
        f'🕒 {post['created_at']}'
    )

    keyboard = [
        [InlineKeyboardButton('🔙 Назад к списку', callback_data=f'page_{page}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )
