# Dungeon Backend

Backend-сервис для проекта "Dungeon". Использует Python, Docker и современные подходы для обеспечения гибкости и масштабируемости.

---

##  Содержание

- [Описание](#описание)  
- [Структура проекта](#структура-проекта)  
- [Установка](#установка)  
- [Запуск](#запуск)  
- [Конфигурация](#конфигурация)  
- [Документация](#документация)  
- [Миграции](#миграции)  

---

##  Описание

`Dungeon_Backend` — это **backend**-часть проекта "Dungeon". Включает в себя реализацию REST API на Python, взаимодействие с базой данных, логику и служебный код, подготовленный к контейнеризации и масштабированию.  
Основные технологии: Python (FastAPI, возможно), SQLAlchemy, Alembic, Mako для шаблонов и Docker для локального и production-запуска.  

---

##  Структура проекта

```

├── api/                 # REST API - endpoints, роутинг, контроллеры
├── database/            # Конфигурация и подключение к БД
├── logics/              # Основная бизнес-логика приложения
├── migration/           # Скрипты миграций (Alembic)
├── shared/              # Общие утилиты и схемы
├── docker/              # Dockerfile и docker-compose конфиги
├── justfile             # Универсальный файл задач (может быть аналог Makefile)
├── config.yaml          # Конфигурация приложения
├── pyproject.toml       # Зависимости и метаданные проекта
└── requirements.txt     # Список зависимостей

````

---

##  Установка

1. Склонируйте репозиторий:

   ```sh
   git clone https://github.com/Ncesam/Dungeon_Backend.git
   cd Dungeon_Backend
   ```
   
2. Создайте файл конфигурации. Например:
   
   ```sh
   cp example.env .env
   ```

3. Настройте переменные окружения (БД, токены и т.д.)

4. Установите зависимости:

   * При использовании `pip`:

     ```sh
     pip install -r requirements.txt```
   * Или с `pyproject.toml` через Poetry:

     ```sh
     poetry install```

---

## Запуск

### Локально

```sh
uvicorn api.main:app --reload
```

(Зависит от структуры `api/`, имя `main` — пример. Замени на фактическое.)

### Через Docker Compose

```sh
docker-compose up --build
```

Это настроит все сервисы, включая базу данных и backend.

---

## Конфигурация

Конфигурация хранится в `config.yaml` или через `.env` файл:

```properties
DATABASE_URL=postgresql://user:password@localhost:5432/dungeon
SECRET_KEY=your-secret-key
# Другие параметры...
```

---

## Документация API

Если используется FastAPI — документация генерируется автоматически и доступна по:

```
http://<host>:<port>/docs
```

или

```
http://<host>:<port>/redoc
```

---

## Миграции

Проект готов к миграциям с использованием Alembic (если она настроена):

```sh
alembic revision --autogenerate -m "описание"
alembic upgrade head
```
