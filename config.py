# config.py
# Конфигурационные настройки бота

BOT_TOKEN = '8195556704:AAH_NJg4IYKVEuoUqsyooGyV6io3yNCSn2k'
SCHEDULE_URL = 'https://www.chtotib.ru/schedule_gl/cg47.htm'

# ID чатов для уведомлений (можно оставить пустым или добавить ID групп)
# Чтобы получить ID группы:
# 1. Добавьте бота в группу
# 2. Отправьте в группе любое сообщение
# 3. Перейдите по ссылке: https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
# 4. Найдите "chat": {"id": -1001234567890}
NOTIFICATION_CHATS = [
    875854768
    # Пример для группы: -1001234567890
    # Пример для ЛС: 123456789
]

# Стикеры с мопсиками
MOPSCI_STICKERS = [
    "CAACAgIAAxkBAAEPZJ5oysVnreu1rJUWe-YRNGa3TVD1CAACXlIAAndDAUqaNc5zJVTa1zYE",
    "CAACAgIAAxkBAAEPZKBoysYIh0Ham6AzGc_6ag6m3Qq8GAACv0sAArsaCUqAyi0j_Q_BKTYE",
    "CAACAgIAAxkBAAEPZKJoysY0wYyYDMvnMBTxmgv2Mex8jQACm0YAAmOfCUpIzgYFw3ipwjYE",
    "CAACAgIAAxkBAAEPZKRoysY6neNMFhUECDLyTaOue-1YPgACRE8AAvLFCEqHung_cXAAEw7QY",
    "CAACAgIAAxkBAAEPZKZoysZGXOswRSdfJhaDdz8R1ONJ7AACCEsAAhtiCUrJpyWSCn7XYzYE",
    "CAACAgIAAxkBAAEQQkdpa14NXqbSN4e3gLksSW_IeZ_8nQACfUcAAmX-AAFKZZ83UB7GffQ4BA",
    "CAACAgIAAxkBAAEQQklpa14Wd3WZd5pwyZFZNrsj3qW5SgAC2kUAAguECUrsSHjB0sL15TgE",
    "CAACAgIAAxkBAAEQQktpa14btYzndJoQrFr_CJ4Uj9reYAACgUIAAgSOCEqgW2ADY1FzUDgE",
    "CAACAgIAAxkBAAEQQk1pa14n6aiaTikMEb3EaPxOoYlxXAAC6oUAAiG-YEphLN3pdVxB6zgE"
]