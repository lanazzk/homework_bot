# Telegram-bot for parsing homework status

Telegram bot can:
- At the specified time interval, query the Practicum.Homework service API and check the status of the homework submitted for review;
- When updating the status, analyze the API response and send a corresponding notification to Telegram;
- Log your work and inform you about important issues with a message in Telegram.

Logging examples:

```
2021-10-09 15:34:45,150 [ERROR] Сбой в работе программы: Эндпоинт https://practicum.yandex.ru/api/user_api/homework_statuses/111 недоступен. Код ответа API: 404
2021-10-09 15:34:45,355 [INFO] Бот отправил сообщение "Сбой в работе программы: Эндпоинт [https://practicum.yandex.ru/api/user_api/homework_statuses/](https://practicum.yandex.ru/api/user_api/homework_statuses/) недоступен. Код ответа API: 404"
2021-10-09 16:19:13,149 [CRITICAL] Отсутствует обязательная переменная окружения: 'TELEGRAM_CHAT_ID'
Программа принудительно остановлена.
```
## Technologies
- Python 3.8
- Teleram Bot API
