import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Tuple, Dict

def escape_markdown(text: str) -> str:
    """Удаляет спецсимволы Markdown"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Просто удаляем все спецсимволы
    return ''.join(char for char in text if char not in escape_chars)

def get_time_mapping():
    return {
        '1': '8:15-9:15',
        '2': '9:25-10:25',
        '3': '10:35-11:35',
        '4': '12:15-13:15',
        '5': '13:25-14:25',
        '6': '14:35-15:35',
        '7': '16:05-17:05',
        '8': '17:15-18:15',
        '9': '18:25-19:25'
    }

def parse_all_dates(url: str) -> Dict[str, List[Dict]]:
    """Парсит все даты из расписания и возвращает словарь {дата: расписание}"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        time_mapping = get_time_mapping()
        
        all_schedules = {}
        
        # Находим все ячейки с датами
        date_cells = []
        all_cells = soup.find_all('td', class_='hd')

        for cell in all_cells:
            if cell.get('rowspan') and re.search(r'\d{2}\.\d{2}\.\d{4}', cell.text):
                date_cells.append(cell)

        if not date_cells:
            return {}

        # Находим все строки таблицы
        all_rows = soup.find_all('tr')
        
        for date_cell in date_cells:
            date_text = date_cell.get_text(separator=' ', strip=True).split(' ')[0]
            
            # Находим строку с датой
            date_row = date_cell.find_parent('tr')
            if not date_row:
                continue
                
            # Определяем границы дня через rowspan
            rowspan = int(date_cell.get('rowspan', 1))
            date_row_index = all_rows.index(date_row)
            
            # Собираем пары для этого дня
            schedule_data = []
            
            for i in range(date_row_index, date_row_index + rowspan):
                if i >= len(all_rows):
                    break

                current_row = all_rows[i]
                cells = current_row.find_all('td')

                # Пропускаем строку, если она содержит только дату
                if len(cells) == 1 and cells[0].get('rowspan'):
                    continue

                # Ищем номер пары в строке
                for j, cell in enumerate(cells):
                    if ('hd' in cell.get('class', []) and
                            cell.text.strip().isdigit() and
                            not cell.get('rowspan')):

                        pair_number = cell.text.strip()
                        pair_time = time_mapping.get(pair_number, 'Время не указано')

                        # Ищем ячейку с информацией о паре
                        if j + 1 < len(cells):
                            info_cell = cells[j + 1]
                            if 'ur' in info_cell.get('class', []):
                                subject_tag = info_cell.find('a', class_='z1')
                                subject = subject_tag.text.strip() if subject_tag else 'Предмет не указан'

                                room_tag = info_cell.find('a', class_='z2')
                                room = room_tag.text.strip() if room_tag else 'Аудитория не указана'

                                teacher_tag = info_cell.find('a', class_='z3')
                                teacher = teacher_tag.text.strip() if teacher_tag else 'Преподаватель не указан'

                                schedule_entry = {
                                    'number': pair_number,
                                    'time': pair_time,
                                    'subject': subject,
                                    'teacher': teacher,
                                    'room': room
                                }
                                schedule_data.append(schedule_entry)
            
            if schedule_data:
                schedule_data.sort(key=lambda x: int(x['number']))
                all_schedules[date_text] = schedule_data
        
        return all_schedules
        
    except Exception as e:
        print(f"Ошибка при парсинге всех дат: {e}")
        return {}

def get_nearest_schedule(url: str) -> Tuple[str, str]:
    """
    Получает расписание на ближайшую дату
    Возвращает: (отформатированное расписание, дата)
    """
    try:
        all_schedules = parse_all_dates(url)
        if not all_schedules:
            return "❌ Не удалось загрузить расписание", ""
        
        # Берем первую (ближайшую) дату
        nearest_date = list(all_schedules.keys())[0]
        schedule_data = all_schedules[nearest_date]
        
        schedule_text = format_daily_schedule(nearest_date, schedule_data)
        return schedule_text, nearest_date
        
    except Exception as e:
        return f"❌ Ошибка при получении расписания: {e}", ""

def get_schedule_for_date(url: str, date_str: str) -> str:
    """
    Получает расписание для конкретной даты
    """
    try:
        all_schedules = parse_all_dates(url)
        if not all_schedules:
            return "❌ Не удалось загрузить расписание"
        
        if date_str not in all_schedules:
            return f"❌ Расписание на {date_str} не найдено"
        
        schedule_data = all_schedules[date_str]
        return format_daily_schedule(date_str, schedule_data)
        
    except Exception as e:
        return f"❌ Ошибка: {e}"

def get_next_day_schedule(url: str, current_date: str) -> Tuple[str, str, bool]:
    """
    Получает расписание на следующий день
    Возвращает: (расписание, дата следующего дня, есть_ли_следующий_вообще)
    """
    try:
        all_schedules = parse_all_dates(url)
        if not all_schedules:
            return "", "", False
        
        dates = list(all_schedules.keys())
        
        if current_date not in dates:
            return "", "", False
        
        current_index = dates.index(current_date)
        if current_index >= len(dates) - 1:
            return "", "", False
        
        next_date = dates[current_index + 1]
        schedule_data = all_schedules[next_date]
        
        schedule_text = format_daily_schedule(next_date, schedule_data)
        
        return schedule_text, next_date, True
        
    except Exception as e:
        print(f"Ошибка при получении следующего дня: {e}")
        return "", "", False

def get_week_schedule(url: str) -> str:
    """
    Получает расписание на неделю (первые 7 дней)
    """
    try:
        all_schedules = parse_all_dates(url)
        if not all_schedules:
            return "❌ Не удалось загрузить расписание"
        
        dates = list(all_schedules.keys())
        
        # Берем максимум 7 дней
        week_dates = dates[:min(7, len(dates))]
        
        if not week_dates:
            return "📭 Нет данных о расписании"
        
        result = []
        
        for i, date_str in enumerate(week_dates):
            schedule_data = all_schedules[date_str]
            
            # Форматируем дату на русском
            try:
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
                
                display_date = f"{day} {month} ({weekday})"
            except:
                display_date = date_str
            
            # Добавляем разделитель перед каждым днем (кроме первого)
            if i > 0:
                result.append("━━━━━━━━━━━━━━━━━━━━━━")
            
            if not schedule_data:
                result.append(f"📅 {display_date}")
                result.append("")  # Пустая строка между парами
                result.append("🎉 Пар нет!")
            else:
                result.append(f"📅 {display_date}")
                for pair in schedule_data:
                    result.append(f"  {pair['number']} пара ({pair['time']})")
                    result.append(f"  📚 {pair['subject']}")
                    result.append(f"  👨‍🏫 {pair['teacher']}")
                    result.append("")  # Пустая строка между парами
        
        return "\n".join(result)
        
    except Exception as e:
        print(f"Ошибка при получении недельного расписания: {e}")
        return f"❌ Ошибка при получении недельного расписания"

def format_daily_schedule(date_text: str, pairs: List[Dict]) -> str:
    """
    Форматирует расписание на день С Markdown
    """
    if not pairs:
        return f"📅 *{date_text}*\n\n🎉 Пар нет! Отдыхай!"

    # Случайные приветствия
    greetings = [
        "📚 Вот расписание:",
        "🎓 Ботан к вашим услугам:",
        "💯 Стопроцентное расписание, проверено ботан-детектором:",
        "🚨 Внимание! Обнаружено расписание:",
        "🐶 Мопсик-ассистент нашел расписание! Вот оно:",
        "🦴 Мопс принес в зубах ваше расписание:",
        "👃 Мопсик учуял расписание! Подарок от носатого детектива:",
        "💤 Мопсик проснулся специально, чтобы принести вам расписание:",
        "📸 Мопсик сделал фото расписания! Снимок с места событий:",
        "🔎 Следствие ведет мопсик! Результаты оперативной работы:",
        "🏆 Расписание чемпионского уровня, одобрено ботан-комитетом:",
        "🍖 Мопсик променял косточку на расписание! Вот что получил:",
    ]

    import random
    greeting = random.choice(greetings)
    
    # Форматируем дату на русском
    try:
        date_obj = datetime.strptime(date_text, "%d.%m.%Y")
        
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
        
        display_date = f"{day} {month} ({weekday})"
    except:
        display_date = date_text
    
    result = [f"{greeting}\n📅 *{display_date}*\n"]
    
    for i, pair in enumerate(pairs):
        # Экранируем символы Markdown в тексте
        subject = escape_markdown(pair['subject'])
        teacher = escape_markdown(pair['teacher'])
        room = escape_markdown(pair['room'])
        
        # Добавляем пару
        result.append(
            f"🔹 *{pair['number']} пара* ({pair['time']})\n"
            f"📚 {subject}\n"
            f"👨‍🏫 {teacher}\n"
            f"🚪 Кабинет {room}\n"
        )
        
        # Добавляем перерывы
        if pair['number'] == '3' and i + 1 < len(pairs) and pairs[i + 1]['number'] == '4':
            result.append("⏰ *Обеденный перерыв:* 11:35-12:15 🍔\n")
        elif pair['number'] == '6' and i + 1 < len(pairs) and pairs[i + 1]['number'] == '7':
            result.append("⏰ *Вечерний перерыв:* 15:35-16:05 ☕\n")
    
    return "\n".join(result)






