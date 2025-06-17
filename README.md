# medguide-bot

## Установка

Клонируйте репозиторий и установите зависимости:

```bash
git clone https://github.com/Anastasia5lebedeva/medguide-bot.git
cd medguide-bot
pip install -r requirements.txt
```

## Запуск через Docker

```bash
docker-compose up --build
```

API будет доступен по адресу:  
http://localhost:8000/docs

Telegram-бот запустится автоматически. Токен уже встроен в код.

## Запуск компонентов вручную

### API

```bash
uvicorn bot.api:app --reload
```

Документация Swagger будет доступна по адресу:  
http://127.0.0.1:8000/docs

### Telegram-бот

```bash
python bot/telegram_bot.py
``

## Зависимости

- Python 3.12+
- FastAPI
- aiogram
- sqlite3
- uvicorn

## Команды бота

- `/mkb <код>` — получить рекомендации по коду заболевания  
  Пример: `/mkb J18`

##! Важное: Файл базы данных

Файл `project.db` (размер: ~2 ГБ) **не включён в репозиторий** из-за ограничений GitHub.

🔗 Скачайте его вручную по ссылке:  
https://drive.google.com/file/d/1iLt3lAo_c3qAg00W5oj5fjQaq4gyCePC/view?usp=sharing

📥 После скачивания — положите файл в папку `data/` с именем: project.db


