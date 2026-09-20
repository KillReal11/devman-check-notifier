# Devman check notifier

Telegram-бот, который уведомляет об изменении статуса проверки работы на [dvmn.org](https://dvmn.org/) через long polling.

### Как установить

1. Скачайте код:
   ```bash
   git clone https://github.com/KillReal11/devman-check-notifier.git
   cd devman-check-notifier
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux / Mac
   venv\Scripts\activate         # Windows
   ```

3. Python3 должен быть уже установлен. 
    Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
    ```bash
    pip install -r requirements.txt
    ```

4. Создайте в корне проекта файл `.env` со своими значениями:
   ```
    TG_TOKEN=1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ1234567abcd
    DEVMAN_TOKEN=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
    CHAT_ID=987654321
   ```
    - **`TG_TOKEN`** — токен Telegram-бота, выдаётся BotFather при создании бота
    - **`DEVMAN_TOKEN`** — токен доступа к API dvmn.org, берётся в настройках профиля на сайте
    - **`CHAT_ID`** — ID чата, куда бот будет отправлять уведомления

## Запуск

```bash
python work_notifications_bot.py
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).