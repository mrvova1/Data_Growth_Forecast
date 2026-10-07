# Лабораторная работа №3 — REST API

Проект на FastAPI для темы «Прогноз роста объёма данных».
## Запуск

1. Создайте/обновите `.env` по примеру `.env.example`.
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Поднимите PostgreSQL, Adminer и MinIO:

```bash
docker compose up -d
```

4. Запустите FastAPI:

```bash
python main.py
```

5. REST API доступен по адресу:

```text
http://127.0.0.1:8000/api
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Adminer:

```text
http://127.0.0.1:8081
```

MinIO Console:

```text
http://127.0.0.1:9001
```

При запуске сервер автоматически проверяет наличие пользователя `id=1` и bucket `media`.

## Методы REST API

### 1. GET `/api/services`

Возвращает только опубликованные услуги.

Поддерживает фильтрацию на backend:

```text
GET /api/services?growth_coefficient_min=1.06&growth_coefficient_max=1.20
```

Каждая запись содержит:

- `is_creator` — `1`, если текущий пользователь является создателем;
- `is_liked` — `1`, если текущий пользователь поставил лайк;
- `likes_count` — количество лайков.

### 2. POST `/api/services`

Создает единственный черновик текущего пользователя.

Тип тела: `multipart/form-data`.

Поля:

```text
growth_factor_name — Text
image_file        — File
video_file        — File
```

Статус, creator, id и даты клиент не передает.

Изображение и видео сохраняются в MinIO.

### 3. GET `/api/services/draft`

Возвращает черновик текущего пользователя. URL не содержит id.

Если черновика нет — `404`.

### 4. PUT `/api/services/draft`

Публикует черновик текущего пользователя.

Тело JSON:

```json
{
  "growth_factor_description": "Описание услуги",
  "growth_coefficient": 1.18,
  "storage_impact_coefficient": 0.91
}
```

Единственный разрешенный переход:

```text
черновик -> опубликован
```

`id`, `status`, `creator_user_id`, `created_at`, `formed_at` клиент не передает.

### 5. GET `/api/services/feed`

Возвращает первый опубликованный элемент ленты.

### 6. GET `/api/services/feed/{id}?next=true`

Возвращает следующий опубликованный элемент.

Если следующего элемента нет, выполняется переход к первому опубликованному элементу.

### 7. POST `/api/services/{id}/like`

Тело JSON:

```json
{
  "like": 1
}
```

`1` — поставить лайк.

`0` — отменить лайк.

Ответ содержит актуальный `like` и `likes_count`.

### 8. DELETE `/api/services/{id}`

Удаляет услугу только логически.

В БД строка остается, меняется только:

```text
опубликован -> удален
```

Удалить можно только услугу текущего пользователя.

Списки и лента услуги со статусом `удален` не возвращают.

### 9. POST `/api/users/register`

Регистрация пользователя.

Тело:

```json
{
  "username": "student_lab3"
}
```

### 10. POST `/api/users/auth`

Заглушка аутентификации для ЛР4.

### Дополнительно: POST `/api/users/logout`

Заглушка деавторизации для ЛР4.

## Таблицы БД

### `growth_factors`

| Поле                         | Тип            | Назначение                            |
| ---------------------------- | -------------- | ------------------------------------- |
| `id`                         | `integer`      | первичный ключ                        |
| `growth_factor_name`         | `varchar(100)` | название услуги                       |
| `growth_factor_description`  | `varchar(500)` | описание                              |
| `growth_factor_status`       | `varchar(20)`  | `черновик` / `опубликован` / `удален` |
| `image_key`                  | `varchar(255)` | ключ изображения в MinIO              |
| `video_key`                  | `varchar(255)` | ключ видео в MinIO                    |
| `growth_coefficient`         | `float`        | коэффициент роста                     |
| `storage_impact_coefficient` | `float`        | влияние на объем                      |
| `created_at`                 | `timestamp`    | дата создания, вычисляется сервером   |
| `creator_user_id`            | `integer`      | создатель, вычисляется сервером       |
| `formed_at`                  | `timestamp`    | дата публикации, вычисляется сервером |


### `likes`

| Поле               | Тип       | Назначение               |
| ------------------ | --------- | ------------------------ |
| `id`               | `integer` | первичный ключ           |
| `user_id`          | `integer` | FK → `users.id`          |
| `growth_factor_id` | `integer` | FK → `growth_factors.id` |


### `users`

| Поле       | Тип           | Назначение                  |
| ---------- | ------------- | --------------------------- |
| `id`       | `integer`     | первичный ключ              |
| `username` | `varchar(50)` | уникальное имя пользователя |


## Сериализаторы / DTO

Pydantic-модели находятся в `schemas/service.py`.

`ServiceOut` — публичное представление услуги.

`DraftOut` — представление черновика.

`PublishIn` — входные бизнес-поля публикации.

`LikeIn` — входное значение `0/1` для лайка.

`UserRegisterIn` — вход регистрации.

`UserOut` — результат регистрации.

Системные поля намеренно не входят в входные DTO.

## Что показывать на защите

### Скриншоты 1–10

Используйте коллекцию `postman/Lab3.postman_collection.json` в таком порядке:

1. GET список с фильтром;
2. POST создание услуги + изображение + видео;
3. GET черновика;
4. PUT публикация;
5. GET лента без id;
6. GET лента по id с `?next=true`;
7. POST like;
8. DELETE soft delete;
9. POST регистрация;
10. POST auth-заглушка.

### Скриншоты 11–13

В Adminer покажите `SELECT` из:

- `growth_factors` — особенно статус, creator и ключи MinIO;
- `likes` — запись о лайке;
- `users` — созданного пользователя.

Готовые SQL-команды лежат в `sql/lab3_selects.sql`.

### Скриншоты 14–15

Покажите:

- `models/growth_factor.py`, `models/like.py`, `models/user.py` — ORM-модели;
- `schemas/service.py` — Pydantic DTO/сериализаторы;
- `api/rest.py` — бизнес-правила обработки.

### Скриншоты 16–17

Покажите:

- `api/deps.py` — singleton `get_current_user()` с `id=1`;
- использование `Depends(get_current_user)` в методах;
- `README.md` с описанием endpoint'ов и таблиц;
- `mermaid_class_diagram.md` с архитектурой.

## Почему это REST

API строится вокруг ресурса `services`, а HTTP-методы выражают действия:

- GET — получение;
- POST — создание/действие;
- PUT — изменение состояния;
- DELETE — удаление.

URL начинаются с `/api`, а данные между клиентом и сервером передаются в JSON либо `multipart/form-data` для загрузки файлов.

## Тестовые сценарии ошибок

Обязательно проверьте несколько кодов ответа:

- `400` — некорректные параметры;
- `404` — услуга/черновик не найдены;
- `409` — второй черновик или существующий пользователь;
- `415` — файл неправильного типа;
- `422` — ошибка валидации DTO;
- `204` — успешный soft delete.
