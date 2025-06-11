import re
from telegram import Update
from telegram.ext import ContextTypes
import httpx
from dotenv import load_dotenv

from services import show_post_detail
from comands import user_sessions, get_posts
from config import settings
from consts import (
    AVAILABLE_COMMANDS,
    INCORRECT_FORMAT_CREDENTIALS_MESSAGE,
    INCORRECT_CREDENTIALS_MESSAGE,
    SUCCESSFUL_LOGIN_MESSAGE,
    ERROR_LOGIN_MESSAGE,
    USE_COMMAND_START_MESSAGE,
)


load_dotenv()
API_URL = settings.API_URL


async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрбатывает учетные дынные пользователя

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    """
    user_id = update.message.from_user.id
    user_data = user_sessions.get(user_id, {})
    if user_data.get('awaiting_credentials'):
        text = update.message.text
        if ':' not in text:
            await update.message.reply_text(INCORRECT_FORMAT_CREDENTIALS_MESSAGE)
            return

        username, password = text.split(':', 1)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f'{API_URL}/users/login',
                    data={'username': username, 'password': password}
                )
                if response.status_code == 200:
                    token = response.json().get('access_token')
                    user_sessions[user_id] = {
                        'authenticated': True,
                        'token': token,
                    }
                    await update.message.reply_text(SUCCESSFUL_LOGIN_MESSAGE)
                else:
                    await update.message.reply_text(INCORRECT_CREDENTIALS_MESSAGE)
            except Exception as e:
                await update.message.reply_text(ERROR_LOGIN_MESSAGE.format(str(e)))
    else:
        await handle_text(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы от инлайн-кнопок бота

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith('post_'):
        post_id = int(data.split('_')[1])
        page = 0
        if query.message and query.message.text:
            page_match = re.search(r'Страница (\d+)', query.message.text)
            if page_match:
                page = int(page_match.group(1)) - 1
        await show_post_detail(update, context, post_id, page)
    elif data.startswith('page_'):
        page = int(data.split('_')[1])
        await get_posts(update, context, page)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает произвольный текст

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    """
    await update.message.reply_text(USE_COMMAND_START_MESSAGE)


async def handle_invalid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает несуществующие команды

    :param update: Информация о входящем сообщении
    :param context: Контекст бота
    """
    user_text = update.message.text
    if user_text.startswith('/'):
        commands_text = '\n'.join(
            f'{cmd} - {desc}' for cmd, desc in AVAILABLE_COMMANDS.items()
        )
        await update.message.reply_text(
            f"Команда '{user_text}' не найдена.\n\n"
            f'Список доступных команд: \n\t{commands_text}'
        )
