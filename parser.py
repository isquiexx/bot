import requests
import re
from bs4 import BeautifulSoup

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



def get_nearest_schedule(url):
    """
    Получает расписание на ближайшую дату с использованием rowspan для определения границ
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        time_mapping = get_time_mapping()

        # 1. Находим все ячейки с датами
        date_cells = []
        all_cells = soup.find_all('td', class_='hd')

        for cell in all_cells:
            if cell.get('rowspan') and re.search(r'\d{2}\.\d{2}\.\d{4}', cell.text):
                date_cells.append(cell)

        if not date_cells:
            return "Не удалось найти даты в расписании"

        # 2. Берем первую (ближайшую) дату
        first_date_cell = date_cells[0]
        date_text = first_date_cell.get_text(separator=' ', strip=True).split(' ')[0]

        # 3. Находим все строки таблицы
        all_rows = soup.find_all('tr')
        date_row = first_date_cell.find_parent('tr')

        if not date_row:
            return "Ошибка: не удалось найти строку с датой"

        # 4. Определяем границы дня через rowspan
        rowspan = int(first_date_cell.get('rowspan', 1))
        date_row_index = all_rows.index(date_row)

        # 5. Собираем пары только для этого дня
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

                    # Ищем ячейку с информацией о паре (следующая ячейка)
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

        return format_nearest_schedule(date_text, schedule_data)

    except Exception as e:
        return f"Ошибка при получении расписания: {e}"


def format_nearest_schedule(date_text, pairs):
    """
    Форматирует расписание на ближайшую дату с перерывами
    """
    if not pairs:
        return f"📅 {date_text}\n\nПар нет! 🎉"

    # Сортируем пары по номеру
    pairs.sort(key=lambda x: int(x['number']))

    # Случайные приветствия
    greetings = [
        "Я твой ботаник! 🤓 Вот расписание:",
        "Держи расписание, студент! 📚",
        "Бот-ботаник к вашим услугам! 🧪",
        "Расписание готово, профессор! 🔬"
    ]

    import random
    greeting = random.choice(greetings)

    result = [f"{greeting}\n📅 {date_text}\n"]

    for i, pair in enumerate(pairs):
        # Добавляем пару
        result.append(
            f"🔹 {pair['number']} пара ({pair['time']})\n"
            f"📚 {pair['subject']}\n"
            f"👨‍🏫 {pair['teacher']}\n"
            f"🚪 Кабинет {pair['room']}\n"
        )

        # Добавляем перерыв после 3-й пары (если есть 4-я пара)
        if pair['number'] == '3' and i + 1 < len(pairs) and pairs[i + 1]['number'] == '4':
            result.append("⏰ Обеденный перерыв: 11:35-12:15 🍔\n")

        # Добавляем перерыв после 6-й пары (если есть 7-я пара)
        elif pair['number'] == '6' and i + 1 < len(pairs) and pairs[i + 1]['number'] == '7':
            result.append("⏰ Вечерний перерыв: 15:35-16:05 ☕\n")

    return "\n".join(result)