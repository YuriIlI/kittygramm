# Dockerfile
FROM python:3.10-slim

# Установка системных зависимостей (необходимо для некоторых библиотек)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование файла с зависимостями и установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего исходного кода
COPY . .

# Сбор статических файлов
RUN python manage.py collectstatic --noinput || true

# Открытие порта
EXPOSE 8000

# Запуск сервера (для разработки, для продакшена использовать Gunicorn)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]