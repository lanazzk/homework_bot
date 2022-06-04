import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
shandler = logging.StreamHandler(stream=sys.stdout)
fhandler = logging.FileHandler('main.log', 'w', encoding='UTF-8')
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
shandler.setFormatter(formatter)
fhandler.setFormatter(formatter)
logger.addHandler(shandler)
logger.addHandler(fhandler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение в телеграм."""
    logger.info('Начало отправки сообщения.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise error(f'Cбой при отправке сообщения в Telegram. {error}')
    else:
        logger.info(f'Бот отправил сообщение {message}')


def get_api_answer(current_timestamp):
    """Делаем GET-запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise exceptions.HTTPErrorException('Страница недоступна')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Oтвет API не является словарем')

    elif 'homeworks' not in response:
        raise IndexError('В ответе API отсутствует необходимый атрибут')

    homeworks = response.get('homeworks')
    if not homeworks:
        logger.debug('Статус домашней работы не изменился')

    elif not isinstance(homeworks, list):
        raise TypeError('Домашняя работа пришла не ввиде списка')
    return homeworks


def parse_status(homework):
    """Извлекает статус работы."""
    if 'homework_name' and 'status' in homework:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    else:
        raise KeyError('Отсутствуют ожидаемые ключи в ответе API')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        raise KeyError('Отсутствуют ожидаемые ключи в словаре')
    else:
        if verdict not in HOMEWORK_STATUSES.values():
            raise ValueError('Недокументированный статус домашней работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    check = check_tokens()
    if not check:
        logger.critical('Отсутствует переменная')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    send_message_count = 0

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)

        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            if send_message_count == 0:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                send_message_count = 1

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
