# EnneAI

EnneAI — Telegram-бот для работы с типологическими моделями через LLM и RAG. Проект объединяет несколько слоёв:

- модуль Наранхо для диалоговой работы с типологией и поиска по источникам;
- модуль Юнга для типирования персонажей, произведений и другого контента;
- RAG-пайплайн на основе Qdrant и эмбеддингов для поиска релевантных фрагментов из книг;
- MongoDB для хранения пользователей, переписок и API-ключей;
- Telegram-интерфейс на aiogram с настройками, историей и админским управлением.

Код проекта расположен в пакете `src/enneai`, а точка входа — `src/enneai/main.py`.

## Что находится в репозитории

```text
.
├── src/
│   └── enneai/
│       ├── main.py                 # запуск Telegram-бота
│       ├── config.py               # чтение env-переменных
│       ├── scraper.py              # scraper для сборки контента
│       ├── ai/
│       │   ├── llm/
│       │   │   └── keys_rotation.py # ротация OpenRouter ключей
│       │   ├── modules/
│       │   │   ├── jung/
│       │   │   └── naranjo/
│       │   └── rag/
│       │       ├── chunker.py
│       │       ├── context.py
│       │       ├── embeddings.py
│       │       ├── ingest.py
│       │       ├── query.py
│       │       ├── reranker.py
│       │       ├── retrieval.py
│       │       └── storage.py
│       ├── db/
│       │   ├── models.py
│       │   ├── mongo.py
│       │   └── repositories/
│       ├── telegram/
│       │   ├── handlers/
│       │   ├── keyboards/
│       │   ├── utils/
│       │   ├── fsm.py
│       │   ├── middlewares.py
│       │   └── stream.py
│       ├── utils/
│       │   ├── encryption.py
│       │   ├── ingest_books.py
│       │   ├── openrouter.py
│       │   ├── reader.py
│       │   └── lang.py
│       └── __init__.py
├── data/
│   ├── ennea/
│   ├── jungian/
│   ├── psychosophy/
│   ├── socio/
│   └── prompts/
├── tests/
│   └── test_rag.py
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── pytest.ini
├── README.md
├── LICENSE
└── .env.example
```

## Основные возможности

- работа с Telegram через `aiogram`;
- два режима: `Naranjo` и `Jung`;
- поиск по книге/контексту через RAG с Qdrant;
- ротация OpenRouter API-ключей;
- хранение пользователей, переписок и настроек в MongoDB;
- подготовка и индексация книг из `data/`;
- поддержка локального запуска и Docker Compose.

## Архитектура

### LLM и типологические модули

- `src/enneai/ai/modules/naranjo/response.py` — диалоговая логика для Наранхо.
- `src/enneai/ai/modules/jung/response.py` — логика Юнга для типирования персонажей и контента.
- `src/enneai/ai/modules/chat.py` — работа с OpenRouter API.

### RAG

- `src/enneai/ai/rag/embeddings.py` — генерация dense и sparse эмбеддингов.
- `src/enneai/ai/rag/storage.py` — хранение чанков и метаданных в Qdrant.
- `src/enneai/ai/rag/retrieval.py` — гибридный поиск по векторному и sparse представлению.
- `src/enneai/ai/rag/query.py` — подготовка и warmup RAG-пайплайна.
- `src/enneai/ai/rag/ingest.py` и `src/enneai/utils/ingest_books.py` — индексация книг.

### Telegram и данные

- `src/enneai/telegram/handlers/user.py` — команды пользователя, режимы, запросы и ключи OpenRouter.
- `src/enneai/telegram/handlers/admin.py` — административные команды и мониторинг.
- `src/enneai/db/models.py` — модели `User`, `UserMessage` и статистика администратора.
- `src/enneai/db/mongo.py` — подключение к MongoDB.

## Требования

- Python 3.14+
- MongoDB
- Qdrant
- OpenRouter API key
- `uv` (рекомендуется) или обычный `pip`

## Настройка окружения

Создайте файл `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_DEBUG_TOKEN=your_debug_bot_token
TELEGRAM_ADMIN_ID=123456789
MONGO_URI=mongodb://localhost:27017
QDRANT_URL=http://localhost:6333
OPENROUTER_API_KEY=your_openrouter_key
ENCRYPTION_KEY=your-long-random-key
```

### Важное

- `config.py` читает переменные через `python-dotenv`.
- `TELEGRAM_DEBUG_TOKEN` используется как токен бота в `src/enneai/main.py`.
- `ENCRYPTION_KEY` используется для шифрования пользовательских API-ключей в MongoDB.
- Для Docker Compose внутри контейнера обычно используются значения:

```env
MONGO_URI=mongodb://mongo:27017
QDRANT_URL=http://qdrant:6333
```

## Локальный запуск

### 1) Установка зависимостей

```bash
uv sync
```

Если `uv` не используется, установите зависимости из `pyproject.toml` через `pip`.

### 2) Запуск бота

```bash
uv run python -m enneai.main
```

или:

```bash
python -m enneai.main
```

## Запуск через Docker

В корне проекта есть `compose.yaml`:

```bash
docker compose up --build
```

Композиция запускает:

- бот `enneai-bot`;
- MongoDB `mongo`;
- Qdrant `qdrant`.

## Индексация RAG

Для наполнения Qdrant данными из `data/` используйте утилиту `enneai.utils.ingest_books`.

```bash
uv run python -m enneai.utils.ingest_books --data-dir data --chunk-size 800 --overlap 100
```

Параметры:

- `--data-dir` — каталог с данными;
- `--chunk-size` — размер чанка;
- `--overlap` — перекрытие чанков;
- `--replace` — заменить существующую индексацию.

## Проверка RAG

В репозитории есть базовые тесты:

```bash
pytest -q
```

айл `tests/test_rag.py` проверяет работу `retrieve()` и фильтрацию по категориям.

## Структура данных

Каталог `data/` содержит наборы по типологиям:

```text
data/
├── ennea/
├── jungian/
├── psychosophy/
├── socio/
├── prompts/
└── ...
```

Обычно там есть:

- `context.txt` — общий контекст;
- `books/metadata.json` — метаданные книг;
- `chunks/` — чанки или подготовленные данные.

## Разработка и отладка

### Запуск тестов

```bash
pytest
```

### Важные моменты кодбазы

- `src/enneai/main.py` подключает Telegram-маршрутизаторы и инициализирует `KeyRotator`.
- `warmup()` из `src/enneai/ai/rag/query.py` подготавливает RAG-сервис.
- `UserMiddleware` в `src/enneai/telegram/middlewares.py` добавляет пользователей в MongoDB и формирует состояние сессии.

## Ограничения и особенности

- проект зависит от внешних сервисов: OpenRouter, Qdrant и MongoDB;
- модели и провайдеры задаются в конфиге и могут меняться;
- RAG-индексация и эмбеддинги могут быть ресурсоёмкими на локальной машине;
- для стабильной эксплуатации лучше держать бота, MongoDB и Qdrant в отдельной инфраструктуре или Docker Compose.

## Полезные ссылки

- OpenRouter: https://openrouter.ai
- Qdrant: https://qdrant.tech
- Telegram Bot API: https://core.telegram.org/bots
- Aiogram: https://docs.aiogram.dev

## Лицензия

MIT
