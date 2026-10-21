import json
import os
import sys
import time
import logging

import requests
import telegram
from environs import Env
from telegram.utils.request import Request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_devman_check(url, headers, timestamp):
    params = {
        'timestamp': timestamp,
    }
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=100,
    )
    response.raise_for_status()
    return response.json()


def send_check_result(bot, chat_id, attempt):
    lesson_title = attempt['lesson_title']
    lesson_url = attempt['lesson_url']
    is_negative = attempt['is_negative']

    if is_negative:
        text = (
            f'Преподаватель проверил работу "{lesson_title}".\n'
            f'К сожалению в работе нашлись ошибки.\n'
            f'Ссылка на урок: {lesson_url}'
        )
    else:
        text = (
            f'Преподаватель проверил работу "{lesson_title}".\n'
            f'Всё отлично!\n'
            f'Ссылка на урок: {lesson_url}'
        )

    bot.send_message(chat_id=chat_id, text=text)


def run_long_polling(bot, chat_id, devman_url, headers):
    timestamp = None
    logging.info("Запущен long polling Devman bot")
    while True:
        try:
            checks = get_devman_check(devman_url, headers, timestamp)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            sys.stderr.write('\033[31mНарушено соединение с сервером, ожидание ответа\033[0m\n')
            time.sleep(10)
            continue

        if checks.get('status') == 'found':
            timestamp = checks.get('last_attempt_timestamp')
            attempt = checks['new_attempts'][0]
            send_check_result(bot, chat_id, attempt)
        else:
            timestamp = checks.get('timestamp_to_request')


def main():
    logging.info("Старт бота")
    env = Env()
    env.read_env()

    devman_auth_token = env.str('DEVMAN_TOKEN')
    tg_token = env.str('TG_TOKEN')
    tg_chat_id = env.str('CHAT_ID')
    proxy_url = env.str('PROXY_SOCKS5')
    works_checked_url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {devman_auth_token}'
    }
    request = Request(
        proxy_url=proxy_url,
        connect_timeout=20.0,
        read_timeout=20.0,
        urllib3_proxy_kwargs={
            'cert_reqs': 'CERT_NONE',
            'assert_hostname': False,
        }
    ) if proxy_url else None
    bot = telegram.Bot(token=tg_token, request=request)

    run_long_polling(bot, tg_chat_id, works_checked_url, headers)


if __name__ == '__main__':
    main()
