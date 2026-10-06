# Kittygram – API для управления котами и заявками на усыновление

Проект Kittygram представляет собой REST API для ведения профилей котов, их достижений, а также для управления процессом усыновления: пользователи могут создавать заявки на понравившихся животных, а сотрудники – изменять статусы заявок и просматривать историю изменений.

## Функционал

### Модуль котов (исходный)
- CRUD операций для котов (только владелец может редактировать / удалять)
- Управление достижениями котов
- Просмотр списка котов (только авторизованные пользователи)

### Модуль заявок на усыновление (новый)
- Создание заявки пользователем (с указанием кота и комментарием)
- Просмотр своих заявок (для обычного пользователя) или всех заявок (для сотрудника)
- Изменение статуса заявки (только для сотрудников: `pending` → `approved` / `rejected` / `completed`)
- Автоматическое логирование всех изменений статуса (кто, когда, старое/новое значение)
- Получение истории статусов по заявке
- Валидации:
  - Нельзя подать повторную заявку на одного кота
  - Нельзя подать заявку на уже усыновлённого кота (есть заявка со статусом `completed`)
  - Минимальная длина комментария – 10 символов
  - Нельзя изменить статус завершённой заявки

## Технологии

- Python 3.10
- Django 3.2
- Django REST Framework
- Djoser (аутентификация)
- JWT (JSON Web Tokens)
- SQLite (по умолчанию, можно заменить на PostgreSQL)
- Docker, Docker Compose

## Требования к окружению

- Установленный Docker и Docker Compose (рекомендуется)
- Или Python 3.10 + pip (для запуска без контейнера)

## Переменные окружения

Перед запуском создайте файл `.env` в корне проекта (скопируйте из `.env.example`):

```ini
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# База данных (SQLite)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=1

Инструкция по запуску (Docker)
Клонируйте репозиторий и перейдите в его папку:

git clone <url-репозитория>
cd kittygram2
Создайте файл .env на основе .env.example:

cp .env.example .env
Запустите сборку и контейнер:

docker-compose up --build
В отдельном терминале выполните миграции и создайте суперпользователя:

docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
Проект будет доступен по адресу: http://localhost:8000

Остановка: docker-compose down

Инструкция по запуску (локально, без Docker)
Создайте виртуальное окружение и активируйте его:

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
Установите зависимости:

pip install -r requirements.txt
Создайте файл .env (см. выше)

Примените миграции и запустите сервер:

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
