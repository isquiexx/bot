# keep_alive.py
from flask import Flask
from threading import Thread
import time
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот активен! 🐶"

def ping_self():
    """Пинг самого себя каждые 10 минут"""
    while True:
        try:
            # Замените на ваш URL
            requests.get('https://bot-schedule-bjo3.onrender.com')
            print("Пинг отправлен для поддержания активности")
        except:
            print("Ошибка пинга")
        time.sleep(600)  # 10 минут

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Запускает веб-сервер и пинг в отдельных потоках"""
    server_thread = Thread(target=run)
    server_thread.daemon = True
    server_thread.start()
    
    ping_thread = Thread(target=ping_self)
    ping_thread.daemon = True
    ping_thread.start()
