# scheduler.py
import asyncio
import logging
from datetime import datetime
from typing import List
from parser import get_nearest_schedule
import pytz
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduleChecker:
    def __init__(self, schedule_url: str, bot, chat_ids: List[int]):
        self.schedule_url = schedule_url
        self.bot = bot
        self.chat_ids = chat_ids
        self.last_schedule = None
        self.last_date = None
        self.is_running = False
        self.moscow_tz = pytz.timezone('Europe/Moscow')

        # Варианты текста для уведомлений
        self.notification_templates = [
            {
                "title": "⚠️ Срочное сообщение от ботан-штаба! Расписание получено:",
                "button": "📋 Показать приказ"
            },
            {
                "title": "📢 Объявление всему учебному составу! Сегодня в программе:",
                "button": "👀 Узнать подробности"
            },
            {
                "title": "🚨 Тревога! Обнаружено расписание высокой важности:",
                "button": "🔍 Изучить данные"
            },
            {
                "title": "🔔 Внимание всем студентам! Транслирую расписание:",
                "button": "📡 Принять сигнал"
            },
            {
                "title": "📡 Экстренный эфир от ботан-радио! Передаю расписание:",
                "button": "📻 Настроиться на волну"
            },
            {
                "title": "⚡ Молния! Поступило новое расписание:",
                "button": "⚡ Открыть срочное"
            },
            {
                "title": "🎯 Цель обнаружена! Координаты расписания:",
                "button": "🎯 Взять на прицел"
            },
            {
                "title": "🆕 Поступило обновление от ботан-командования:",
                "button": "🔄 Загрузить апдейт"
            }
        ]

    def get_random_notification(self) -> dict:
        """Возвращает случайный шаблон уведомления"""
        return random.choice(self.notification_templates)

    async def check_schedule_update(self):
        """Проверяет, обновилось ли расписание"""
        try:
            current_schedule, current_date = get_nearest_schedule(self.schedule_url)

            # Если это первая проверка
            if self.last_schedule is None:
                self.last_schedule = current_schedule
                self.last_date = current_date
                logger.info(f"Первая проверка расписания: {current_date}")
                return False

            # Проверяем, изменилось ли расписание
            schedule_changed = False

            # Сравниваем даты
            if current_date != self.last_date:
                logger.info(f"Обнаружена новая дата: {current_date} (было: {self.last_date})")
                schedule_changed = True

            # Сравниваем содержимое расписания
            elif current_schedule != self.last_schedule:
                logger.info(f"Расписание на {current_date} изменилось")
                schedule_changed = True

            if schedule_changed:
                # Отправляем уведомление всем чатам
                await self.send_notifications(current_schedule, current_date)

                # Обновляем сохраненное расписание
                self.last_schedule = current_schedule
                self.last_date = current_date

            return schedule_changed

        except Exception as e:
            logger.error(f"Ошибка при проверке расписания: {e}")
            return False

    async def send_notifications(self, schedule_text: str, date: str):
        """Отправляет уведомления об обновлении расписания"""
        try:
            # Получаем случайный шаблон уведомления
            template = self.get_random_notification()

            # Форматируем дату на русском
            formatted_date = self.format_date_for_display(date)

            notification_text = (
                f"{template['title']}\n\n"
                f"📅 *{formatted_date}*\n\n"
                f"👇 {template['button'].lower()}"
            )

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            for chat_id in self.chat_ids:
                try:
                    # Создаем кнопку для просмотра расписания
                    keyboard = [[InlineKeyboardButton(template['button'], callback_data=f"notify_{date}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=notification_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    logger.info(f"✅ Уведомление отправлено в чат {chat_id} (шаблон: {template['title'][:20]}...)")

                except Exception as e:
                    logger.error(f"❌ Ошибка отправки уведомления в чат {chat_id}: {e}")

        except Exception as e:
            logger.error(f"❌ Критическая ошибка при отправке уведомлений: {e}")

    def format_date_for_display(self, date_str: str) -> str:
        """Форматирует дату для отображения на русском"""
        try:
            from datetime import datetime

            date_obj = datetime.strptime(date_str, "%d.%m.%Y")

            # Русские названия месяцев
            months_ru = {
                1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
            }

            # Русские названия дней недели
            days_ru = {
                0: 'Понедельник', 1: 'Вторник', 2: 'Среда',
                3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
            }

            day = date_obj.day
            month = months_ru.get(date_obj.month, '')
            weekday = days_ru.get(date_obj.weekday(), '')

            return f"{day} {month} ({weekday})"

        except:
            return date_str

    async def start_checking(self, interval_minutes: int = 30):
        """Запускает периодическую проверку расписания"""
        self.is_running = True
        logger.info(f"🚀 Запуск проверки расписания с интервалом {interval_minutes} минут")

        # Сначала делаем одну проверку сразу при запуске
        logger.info("🔍 Первоначальная проверка расписания...")
        await self.check_schedule_update()

        while self.is_running:
            try:
                # Проверяем текущее время (только в рабочее время)
                now = datetime.now(self.moscow_tz)
                current_hour = now.hour

                # Проверяем только в рабочее время (с 6 утра до 22 вечера)
                if 6 <= current_hour < 22:
                    logger.info(f"🕐 Проверка расписания в {now.strftime('%H:%M:%S')}")
                    await self.check_schedule_update()
                else:
                    if current_hour == 22 or current_hour < 6:
                        logger.info(f"🌙 Нерабочее время ({current_hour}:{now.minute:02d}), пропускаем проверку")

                # Ждем указанный интервал
                await asyncio.sleep(interval_minutes * 60)

            except asyncio.CancelledError:
                logger.info("⏹️ Проверка расписания остановлена")
                break
            except Exception as e:
                logger.error(f"⚠️ Ошибка в цикле проверки: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке

    def stop_checking(self):
        """Останавливает проверку расписания"""
        self.is_running = False
        logger.info("🛑 Проверка расписания остановлена")


# Глобальный инстанс для доступа из других файлов
schedule_checker = None


def init_scheduler(schedule_url: str, bot, chat_ids: List[int]):
    """Инициализирует планировщик"""
    global schedule_checker
    schedule_checker = ScheduleChecker(schedule_url, bot, chat_ids)
    return schedule_checker