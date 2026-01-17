# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN, SCHEDULE_URL, MOPSCI_STICKERS
from parser import get_nearest_schedule, get_next_day_schedule, get_week_schedule, get_schedule_for_date
import random
import os
import asyncio
from keep_alive import keep_alive
import re

# Хранилище для истории навигации пользователей
user_navigation = {}

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
    user_id = update.effective_user.id
    schedule_text, date_text = get_nearest_schedule(SCHEDULE_URL)
    
    # Сохраняем текущую дату как начало навигации
    user_navigation[user_id] = {
        'current_date': date_text,
        'prev_date': None  # Предыдущая дата (если перешли на следующий день)
    }
    
    # Проверяем, есть ли следующий день
    next_schedule_text, next_date, has_next = get_next_day_schedule(SCHEDULE_URL, date_text)
    
    # Кнопки навигации - только "Следующий день" если есть
    keyboard = []
    if has_next:
        keyboard.append([InlineKeyboardButton("▶️ Следующий день", callback_data=f"next_{date_text}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(schedule_text, reply_markup=reply_markup, parse_mode='Markdown')
    await send_mopsci_sticker(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех сообщений - реагирует на 'ботан' или 'бот' как отдельные слова"""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.lower()
    bot_username = context.bot.username.lower()

    # Проверяем, есть ли упоминание бота
    has_mention = f"@{bot_username}" in message_text

    # Разбиваем сообщение на слова и проверяем наличие ключевых слов как отдельных слов
    words = re.findall(r'\b\w+\b', message_text)  # Извлекаем отдельные слова
    has_botan = any(word in ["ботан", "бот"] for word in words)

    # Активируем бота если:
    # 1. Есть прямое упоминание @username
    # 2. Или есть слова "ботан" или "бот" как отдельных слова
    if has_mention or has_botan:
        # Добавляем небольшую задержку для естественности
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(1)  # Задержка 1 секунда

        user_id = update.effective_user.id
        schedule_text, date_text = get_nearest_schedule(SCHEDULE_URL)
        
        # Сохраняем текущую дату как начало навигации
        user_navigation[user_id] = {
            'current_date': date_text,
            'prev_date': None
        }
        
        # Проверяем, есть ли следующий день
        next_schedule_text, next_date, has_next = get_next_day_schedule(SCHEDULE_URL, date_text)
        
        # Кнопки навигации - только "Следующий день" если есть
        keyboard = []
        if has_next:
            keyboard.append([InlineKeyboardButton("▶️ Следующий день", callback_data=f"next_{date_text}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(schedule_text, reply_markup=reply_markup, parse_mode='Markdown')
        await send_mopsci_sticker(update, context)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда старт с инструкцией"""
    welcome_text = (
        "Привет! Я бот-расписание 🤓\n\n"
        "📋 *Доступные команды:*\n"
        "• /today - расписание на сегодня\n"
        "• /week - расписание на неделю\n"
        "• Или просто напиши 'ботан' или 'бот'\n\n"
        "🔄 *Навигация:*\n"
        "Можно посмотреть расписание на следующий день и вернуться назад\n\n"
        "🐶 И да, у меня есть мопсики!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    await send_mopsci_sticker(update, context)

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Расписание на текущую неделю"""
    try:
        schedule_text = get_week_schedule(SCHEDULE_URL)
        
        # Отправляем без parse_mode, так как текст уже содержит форматирование
        await update.message.reply_text(schedule_text)
        
        await send_mopsci_sticker(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении недельного расписания: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    if callback_data.startswith('next_'):
        # Переход к следующему дню
        current_date_str = callback_data.split('_')[1]
        
        # Получаем расписание на следующий день
        schedule_text, next_date, has_next = get_next_day_schedule(SCHEDULE_URL, current_date_str)
        
        if not schedule_text:
            await query.edit_message_text("❌ Нет расписания на следующий день")
            return
        
        # Сохраняем предыдущую дату
        if user_id not in user_navigation:
            user_navigation[user_id] = {'current_date': current_date_str, 'prev_date': None}
        
        # Сохраняем текущую дату как предыдущую для следующего дня
        user_navigation[user_id]['prev_date'] = current_date_str
        user_navigation[user_id]['current_date'] = next_date
        
        # Только кнопка "Назад"
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=f"back_{next_date}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=schedule_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    elif callback_data.startswith('back_'):
        # Возврат к предыдущему дню
        current_date_str = callback_data.split('_')[1]
        
        if user_id not in user_navigation or not user_navigation[user_id]['prev_date']:
            # Если нет истории, показываем сегодняшнее расписание
            schedule_text, date_text = get_nearest_schedule(SCHEDULE_URL)
            user_navigation[user_id] = {'current_date': date_text, 'prev_date': None}
            
            # Проверяем, есть ли следующий день
            next_schedule_text, next_date, has_next = get_next_day_schedule(SCHEDULE_URL, date_text)
            
            keyboard = []
            if has_next:
                keyboard.append([InlineKeyboardButton("▶️ Следующий день", callback_data=f"next_{date_text}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            await query.edit_message_text(text=schedule_text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Получаем предыдущую дату
        prev_date = user_navigation[user_id]['prev_date']
        
        # Получаем расписание для предыдущей даты
        schedule_text = get_schedule_for_date(SCHEDULE_URL, prev_date)
        
        # Проверяем, есть ли следующий день от предыдущей даты
        next_schedule_text, next_date, has_next = get_next_day_schedule(SCHEDULE_URL, prev_date)
        
        # Сбрасываем предыдущую дату (возвращаемся в исходное состояние)
        user_navigation[user_id]['prev_date'] = None
        user_navigation[user_id]['current_date'] = prev_date
        
        # Кнопки навигации - только "Следующий день" если есть
        keyboard = []
        if has_next:
            keyboard.append([InlineKeyboardButton("▶️ Следующий день", callback_data=f"next_{prev_date}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await query.edit_message_text(text=schedule_text, reply_markup=reply_markup, parse_mode='Markdown')

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение при добавлении в группу"""
    for member in update.message.new_chat_members:
        if member.username == context.bot.username:
            welcome_text = (
                f"Привет! Я бот-расписание 🤓\n\n"
                f"📋 *Доступные команды:*\n"
                f"• /today - расписание на сегодня\n"
                f"• /week - расписание на неделю\n"
                f"• Или просто напишите 'ботан' или 'бот'\n\n"
                f"🔄 Используйте кнопки для навигации\n"
                f"🐶 И да, у меня есть мопсики!"
            )
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            await send_mopsci_sticker(update, context)

def main():
    keep_alive()

    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("week", week_command))

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

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
