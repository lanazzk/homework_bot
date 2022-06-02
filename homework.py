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
sys.stdout = open('main.log', 'a', encoding="UTF-8")
handler = logging.StreamHandler(stream=sys.stdout)

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


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
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Cбой при отправке сообщения в Telegram. {error}')
    else:
        logger.info(f'Бот отправил сообщение {message}')


def get_api_answer(current_timestamp):
    """Делаем GET-запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise exceptions.HTTPErrorException('Страница недоступна')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logger.error('Oтвет API не является словарем')
        raise TypeError('Oтвет API не является словарем')

    elif not isinstance(response['homeworks'], list):
        logger.error('Домашняя работа пришла не ввиде списка')
        raise TypeError('Домашняя работа пришла не ввиде списка')
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        logger.error('Отсутствуют ожидаемые ключи в ответе API ')
    else:
        if verdict not in HOMEWORK_STATUSES.values():
            logger.error('Недокументированный статус домашней работы')
            raise ValueError('Недокументированный статус домашней работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    vnames = {PRACTICUM_TOKEN: "PRACTICUM_TOKEN", TELEGRAM_TOKEN:
              "TELEGRAM_TOKEN", TELEGRAM_CHAT_ID: "TELEGRAM_CHAT_ID"}
    for variable in vnames:
        if not variable:
            return False
    return True


def main():
    """Основная логика работы бота."""
    check = check_tokens()
    if not check:
        logger.critical('Отсутствует переменная')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    old_status = None

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            bot.send_message(TELEGRAM_CHAT_ID, message)
            time.sleep(RETRY_TIME)
        else:
            homeworks = check_response(response)
            for homework in homeworks:
                if homework['status'] != old_status:
                    message = parse_status(homework)
                    send_message(bot, message)
                    old_status = homework['status']
                else:
                    logger.debug('Статус работы не изменился')


if __name__ == '__main__':
    main()
