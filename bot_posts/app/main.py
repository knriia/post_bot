from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from handlers import handle_callback, handle_credentials, handle_invalid_command
from comands import start, login, get_posts
from config import settings


def main():
    """Главная функция бота"""
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('login', login))
    app.add_handler(CommandHandler('posts', lambda u, c: get_posts(u, c, page=0)))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
    app.add_handler(MessageHandler(filters.COMMAND, handle_invalid_command))
    app.run_polling()


if __name__ == '__main__':
    main()
