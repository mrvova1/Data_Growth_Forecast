# Прогноз роста объёма данных — лабораторная работа №1

FastAPI-приложение по теме «Прогноз роста объёма данных».

## Структура

В проекте одна Python-коллекция в `data/collections.py`, обработчики FastAPI в `api/handlers.py`, шаблоны Jinja2 в `templates/` и отдельный CSS в `static/css/style.css`. База данных не используется.

## Три страницы

- Плитка: `GET /growth-factors`
- Лента: `GET /growth-factor/{growth_factor_id}`
- Добавление: `GET /growth-factor-draft`

## Параметры GET

Фильтрация плитки выполняется на сервере одним полем:

`/growth-factors?growth_coefficient_min=1.06&growth_coefficient_max=1.2`

В ленте предусмотрены требуемые переходы:

`/growth-factor/1?next=true`

## MinIO

1. Запустить `docker compose up -d`.
2. Открыть `http://localhost:9001`.
3. Создать публичный bucket `media`.
4. Загрузить изображения и видео с ключами из `data/collections.py`.
5. Проверить URL вида `http://localhost:9000/media/<key>`.

## Запуск

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Основная страница: `http://127.0.0.1:8000/growth-factors`.

## Палитра

Основные цвета: `#e7d9bd`, `#111419`, `#c6c9d1`.
