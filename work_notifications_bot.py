import logging
import time

import requests
import telegram
from environs import Env
from telegram.utils.request import Request

MIN_RETRY_DELAY = 10
MAX_RETRY_DELAY = 300

logger = logging.getLogger("work_notifications_bot")


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_token, chat_id, proxy_url=None):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = create_bot(tg_token, proxy_url)

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception:
            self.handleError(record)


def create_bot(tg_token, proxy_url=None):
    request = (
        Request(
            proxy_url=proxy_url,
            connect_timeout=20.0,
            read_timeout=20.0,
            urllib3_proxy_kwargs={
                "cert_reqs": "CERT_NONE",
                "assert_hostname": False,
            },
        )
        if proxy_url
        else None
    )
    return telegram.Bot(token=tg_token, request=request)


def get_devman_check(url, headers, timestamp):
    params = {
        "timestamp": timestamp,
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
    lesson_title = attempt["lesson_title"]
    lesson_url = attempt["lesson_url"]
    is_negative = attempt["is_negative"]

    if is_negative:
        text = (
            f'Преподаватель проверил работу "{lesson_title}".\n'
            f"К сожалению в работе нашлись ошибки.\n"
            f"Ссылка на урок: {lesson_url}"
        )
    else:
        text = (
            f'Преподаватель проверил работу "{lesson_title}".\n'
            f"Всё отлично!\n"
            f"Ссылка на урок: {lesson_url}"
        )

    bot.send_message(chat_id=chat_id, text=text)


def run_long_polling(bot, chat_id, devman_url, headers):
    timestamp = None
    retry_delay = MIN_RETRY_DELAY
    logger.info("Запущен long polling Devman bot")
    while True:
        try:
            checks = get_devman_check(devman_url, headers, timestamp)

            if checks.get("status") == "found":
                timestamp = checks.get("last_attempt_timestamp")
                attempt = checks["new_attempts"][0]
                send_check_result(bot, chat_id, attempt)
            else:
                timestamp = checks.get("timestamp_to_request")

            retry_delay = MIN_RETRY_DELAY

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Нарушено соединение с сервером, ожидание ответа, повтор через {retry_delay} c."
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
            continue
        except Exception:
            logger.exception(f"Ошибка в работе бота, повтор через {retry_delay} с")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)


def main():
    env = Env()
    env.read_env()

    devman_auth_token = env.str("DEVMAN_TOKEN")
    tg_token = env.str("TG_TOKEN")
    tg_chat_id = env.str("CHAT_ID")
    proxy_url = env.str("PROXY_SOCKS5", default=None)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(level=logging.INFO, format=log_format, datefmt=log_datefmt)
    logger.setLevel(logging.INFO)

    tg_handler = TelegramLogsHandler(tg_token, tg_chat_id, proxy_url)
    tg_handler.setLevel(logging.WARNING)
    tg_handler.setFormatter(logging.Formatter(log_format, datefmt=log_datefmt))
    logger.addHandler(tg_handler)

    works_checked_url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {devman_auth_token}"}

    retry_delay = MIN_RETRY_DELAY
    while True:
        try:
            bot = create_bot(tg_token, proxy_url)
            logger.info("Старт бота")
            run_long_polling(bot, tg_chat_id, works_checked_url, headers)
        except Exception:
            logger.exception(f"Бот упал, перезапуск через {retry_delay} с")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)


if __name__ == "__main__":
    main()
