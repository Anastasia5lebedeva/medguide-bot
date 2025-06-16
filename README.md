# medguide-bot
# Установка
Клонировать:
bash
git clone https://github.com/Anastasia5lebedeva/medguide-bot.git
cd medguide-bot
pip install -r requirements.txt
# Запуск компонентов:
uvicorn bot.api:app --reload Документация Swagger будет доступна по адресу:http://127.0.0.1:8000/docs
Telegram-бот:
python bot/telegram_bot.py
# Зависимости
Python 3.12+
FastAPI
aiogram
sqlite3
uvicorn
# Команды бота:
/mkb <код> — получить рекомендации по коду заболевания
(например: /mkb J18)
