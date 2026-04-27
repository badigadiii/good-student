# Good Student

`Good Student` - это FastAPI-сервис для запуска ботов-слушателей, которые автоматически заходят на онлайн-лекцию в BigBlueButton, пишут приветствие, следят за чатом и выходят из встречи, когда лекция закончилась.

Проект полезен как backend-обёртка над браузерной автоматизацией: ботами можно управлять через HTTP API, а сама работа внутри лекции выполняется через Playwright.

## Что умеет проект

- создаёт бота по HTTP-запросу;
- открывает браузер Chromium через Playwright;
- заходит по ссылке на лекцию под указанным именем;
- подключается в режиме `Listen only`;
- отправляет приветственное сообщение в чат;
- периодически читает чат и ищет фразы, указывающие на окончание лекции;
- может завершать работу также по времени `lecture_end`;
- отправляет прощальное сообщение и выходит из конференции;
- позволяет получить список активных/завершённых ботов и остановить бота вручную.

## Стек технологий

- Python `3.13+` - основной язык проекта
- FastAPI - HTTP API и lifecycle приложения
- Uvicorn - ASGI-сервер
- Pydantic / pydantic-settings - схемы запросов и конфигурация через переменные окружения
- Playwright - управление браузером Chromium
- Ruff - линтер и форматирование
- Pytest / pytest-playwright - подготовка окружения для тестирования

## Как работает проект

Основной сценарий такой:

1. Клиент отправляет `POST /bots` с параметрами лекции и сообщениями бота.
2. `BotManager` создаёт экземпляр `LectureBot` и отдельную `asyncio`-задачу.
3. Для бота поднимается Playwright-клиент `BBBPlaywrightClient`.
4. Бот при необходимости ждёт `lecture_start`.
5. Бот открывает страницу лекции, вводит имя, нажимает `Join`, затем `Listen only`.
6. После входа бот отправляет приветствие.
7. Дальше он циклически читает чат и проверяет:
   - встретились ли ключевые фразы окончания лекции;
   - наступило ли время `lecture_end`.
8. Когда условие завершения выполнено, бот отправляет прощание и выходит из встречи.
9. При остановке сервиса или удалении бота задача отменяется, браузер закрывается.

## Архитектура

Проект разделён на слои:

- `app/api` - HTTP-роуты и Pydantic-схемы
- `app/application` - orchestration-логика и менеджер ботов
- `app/domain` - доменные модели, интерфейсы и поведение `LectureBot`
- `app/infrastructure` - реализация клиента для BigBlueButton через Playwright
- `app/core` - конфигурация, фабрики, исключения

Такое разделение упрощает замену инфраструктуры. Например, вместо `BBBPlaywrightClient` можно реализовать другой `LectureClient`, не меняя логику `LectureBot`.

## Структура проекта

```text
.
├── app/
│   ├── api/
│   │   ├── routes.py              # REST API для управления ботами
│   │   └── schemas.py             # схемы запросов и ответов
│   ├── application/
│   │   └── bot_manager.py         # создание, хранение и остановка ботов
│   ├── core/
│   │   ├── config.py              # настройки из env
│   │   ├── exceptions.py          # доменные исключения
│   │   └── factories.py           # фабрика Playwright-клиента
│   ├── domain/
│   │   ├── interfaces.py          # абстракции LectureClient
│   │   ├── lecture_bot.py         # сценарий поведения бота
│   │   └── models.py              # LectureConfig, ChatMessage
│   ├── infrastructure/
│   │   ├── bbb_playwright_client.py  # интеграция с BigBlueButton
│   │   └── selectors.py              # CSS-селекторы элементов страницы
│   └── main.py                    # создание FastAPI-приложения
├── main.py                        # локальная точка входа для запуска uvicorn
├── pyproject.toml                 # зависимости и настройки инструментов
└── pytest.ini                     # базовая конфигурация pytest
```

## Требования

- Python `3.13+`
- установленный браузер Chromium для Playwright
- доступ к странице BigBlueButton, совместимой с селекторами из `app/infrastructure/selectors.py`

Важно: интеграция жёстко завязана на текущую HTML-разметку BigBlueButton. Если селекторы или UI платформы изменятся, бот перестанет корректно входить в лекцию, читать чат или выходить из неё.

## Установка и запуск

### 1. Создать виртуальное окружение

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### 2. Установить зависимости

```bash
pip install -e .
```

### 3. Установить браузер для Playwright

```bash
playwright install chromium
```

### 4. Запустить сервис

Вариант через корневую точку входа:

```bash
python main.py
```

Или напрямую через Uvicorn:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

После запуска API будет доступно по адресу:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Конфигурация

Настройки читаются из переменных окружения с префиксом `LECTURE_BOT_`.

### Основные переменные

- `LECTURE_BOT_HEADLESS=true|false` - запуск браузера в headless-режиме
- `LECTURE_BOT_CHAT_POLL_INTERVAL_MS=3000` - интервал чтения чата
- `LECTURE_BOT_LECTURE_START_POLL_INTERVAL_MS=3000` - интервал ожидания времени старта
- `LECTURE_BOT_POST_JOIN_DELAY_MS=1000` - пауза после входа перед приветствием
- `LECTURE_BOT_PRE_GOODBYE_DELAY_MS=1000` - пауза перед прощальным сообщением
- `LECTURE_BOT_PRE_LEAVE_DELAY_MS=1000` - пауза после прощания перед выходом
- `LECTURE_BOT_PAGE_TIMEOUT_MS=15000` - timeout Playwright для элементов страницы
- `LECTURE_BOT_BROWSER_SLOW_MO_MS=0` - замедление действий браузера для отладки
- `LECTURE_BOT_KEYPHRASE_MATCH_THRESHOLD=3` - сколько совпадений по ключевым фразам считать окончанием лекции
- `LECTURE_BOT_RECENT_MESSAGES_LIMIT=10` - сколько последних сообщений анализировать

Пример:

```bash
export LECTURE_BOT_HEADLESS=false
export LECTURE_BOT_BROWSER_SLOW_MO_MS=300
uvicorn app.main:app --reload
```

## HTTP API

### Создать бота

`POST /bots`

Пример тела запроса:

```json
{
  "lecture_url": "https://bbb.example.com/rooms/lecture-1/join",
  "student_name": "Иван Иванов",
  "greetings_message": "Здравствуйте! Я подключился.",
  "goodbye_message": "Спасибо за лекцию, до свидания!",
  "lecture_start": "2026-04-27T09:00:00+04:00",
  "lecture_end": "2026-04-27T10:30:00+04:00",
  "keyphrase_lecture_over": [
    "до свидания",
    "спасибо за лекцию",
    "на сегодня всё"
  ]
}
```

Что важно:

- `lecture_url`, `student_name`, `greetings_message`, `goodbye_message` обязательны;
- `lecture_start` и `lecture_end` должны быть timezone-aware datetime;
- если переданы обе даты, `lecture_end` должна быть позже `lecture_start`;
- `keyphrase_lecture_over` нормализуется: пустые и повторяющиеся фразы удаляются.

Пример запроса:

```bash
curl -X POST "http://127.0.0.1:8000/bots" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_url": "https://bbb.example.com/rooms/lecture-1/join",
    "student_name": "Иван Иванов",
    "greetings_message": "Здравствуйте! Я подключился.",
    "goodbye_message": "Спасибо за лекцию, до свидания!"
  }'
```

### Получить список ботов

`GET /bots`

Возвращает массив с краткой информацией:

- `id`
- `student_name`
- `lecture_url`
- `status`
- `created_at`

### Получить бота по ID

`GET /bots/{bot_id}`

Возвращает расширенную информацию о конкретном боте.

### Остановить и удалить бота

`DELETE /bots/{bot_id}`

Поведение:

- отменяет `asyncio`-задачу бота;
- закрывает браузер;
- удаляет бота из `BotManager`;
- возвращает `204 No Content`.

## Статусы ботов

Статус вычисляется по состоянию асинхронной задачи:

- `running` - бот работает
- `finished` - бот завершился без ошибки
- `failed` - бот завершился с исключением
- `cancelled` - задача была отменена

## Особенности и ограничения

- Сейчас поддерживается только сценарий входа в BigBlueButton через конкретные CSS-селекторы.
- Бот работает через реальный браузер Chromium, поэтому на сервере должны быть доступны зависимости Playwright.
- В проекте нет постоянного хранилища: список ботов живёт в памяти процесса.
- После перезапуска приложения информация о ранее созданных ботах теряется.
- Если бот завершился, запись остаётся в памяти менеджера до ручного удаления или завершения приложения.
- Значение `wait_time_till_lecture_start_in_seconds` в модели `LectureConfig` фактически используется как timeout ожидания кнопки `Listen only`; по текущему коду это миллисекунды, несмотря на имя поля.

## Разработка

Линтер:

```bash
ruff check .
```

Форматирование:

```bash
ruff format .
```

Тесты:

```bash
pytest
```

На текущий момент в репозитории практически нет собственных тестов приложения, поэтому основной способ проверки - локальный запуск API и ручная проверка сценария входа в BigBlueButton.
