# bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, SCHEDULE_URL, MOPSCI_STICKERS
from parser import get_nearest_schedule
import random
import os
import asyncio


async def send_mopsci_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайный стикер с мопсиком"""
    if MOPSCI_STICKERS:
        try:
            sticker_id = random.choice(MOPSCI_STICKERS)
            await update.message.reply_sticker(sticker_id)
        except Exception as e:
            print(f"Ошибка отправки стикера: {e}")
    else:
        # Запасной вариант если стикеры не настроены
        await update.message.reply_text("🐶 Мопсик одобряет твое расписание!")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на сегодня/ближайший день со стикером"""
    schedule_text = get_nearest_schedule(SCHEDULE_URL)
    await update.message.reply_text(schedule_text)
    await send_mopsci_sticker(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех сообщений - реагирует на 'ботан' или 'бот' в любом контексте"""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.lower()
    bot_username = context.bot.username.lower()

    # Проверяем, есть ли упоминание бота
    has_mention = f"@{bot_username}" in message_text

    # Проверяем, есть ли слова "ботан" или "бот" в любом месте сообщения
    has_botan = any(word in message_text for word in ["ботан", "бот"])

    # Активируем бота если:
    # 1. Есть прямое упоминание @username
    # 2. Или есть слова "ботан" или "бот" в любом контексте
    if has_mention or has_botan:
        # Добавляем небольшую задержку для естественности
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        schedule_text = get_nearest_schedule(SCHEDULE_URL)
        await update.message.reply_text(schedule_text)
        await send_mopsci_sticker(update, context)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда старт с инструкцией"""
    welcome_text = (
        "Привет! Я бот-расписание 🤓\n\n"
        "Просто напиши мне в любом чате:\n"
        "• 'Ботан' - и я пришлю расписание\n"
        "• 'Привет, ботан!'\n"
        "• 'Эй ботан, как дела?'\n"
        "• 'Бот, помоги с расписанием'\n"
        "• Или используй /today\n\n"
        "Главное - скажи 'ботан' или 'бот' 😉\n"
        "И получишь милого мопсика в подарок! 🐶"
    )
    await update.message.reply_text(welcome_text)
    await send_mopsci_sticker(update, context)


async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение при добавлении в группу"""
    for member in update.message.new_chat_members:
        if member.username == context.bot.username:
            welcome_text = (
                f"Привет! Я бот-расписание 🤓\n\n"
                f"Просто напишите в чат:\n"
                f"• 'Ботан' - и я пришлю расписание\n"
                f"• 'Ботан, какие пары?'\n"
                f"• Или упомяните меня @{context.bot.username}\n\n"
                f"Рад помогать с расписанием! 📚\n"
                f"И да, у меня есть мопсики! 🐶"
            )
            await update.message.reply_text(welcome_text)
            await send_mopsci_sticker(update, context)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("today", today_command))

    # Обработчик добавления в группу
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))

    # Обработчик всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Проверяем, работаем ли на Render (есть ли переменная PORT)
    if 'RENDER' in os.environ or 'PORT' in os.environ:
        # Используем вебхуки для Render
        port = int(os.environ.get('PORT', 8443))
        webhook_url = f"https://bot-schedule-bjo3.onrender.com/{BOT_TOKEN}"
        
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url
        )
        print(f"🟢 Бот запущен на Render с вебхуком: {webhook_url}")
    else:
        # Локальная разработка с поллингом
        application.run_polling()
        print("🟢 Бот запущен локально с поллингом...")


if __name__ == '__main__':
    main()
