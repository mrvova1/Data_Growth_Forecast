# Диаграмма классов ЛР3

```mermaid
classDiagram

    class ServiceAPI {
        +getServices()
        +createService()
        +getDraft()
        +updateDraft()
        +getFeed()
        +getNextFeedItem(id, next)
        +likeService(id)
        +deleteService(id)
    }

    class UserAPI {
        +register()
        +auth()
        +logout()
    }

    class GrowthFactor {
        +id
        +growth_factor_name
        +growth_factor_description
        +growth_factor_status
        +image_key
        +video_key
        +growth_coefficient
        +storage_impact_coefficient
        +created_at
        +creator_user_id
        +formed_at
    }

    class Like {
        +id
        +user_id
        +growth_factor_id
    }

    class User {
        +id
        +username
    }

    class ServiceOut {
        +id
        +growth_factor_name
        +image_url
        +video_url
        +likes_count
        +is_creator
        +is_liked
    }

    class PublishIn {
        +growth_factor_description
        +growth_coefficient
        +storage_impact_coefficient
    }

    class CurrentUserSingleton {
        +get_current_user()
        +id = 1
    }

    class MinIOStorage {
        +ensure_bucket()
        +put_upload()
        +delete_object()
        +public_url()
    }

    class TilePage {
        <<frontend>>
    }

    class FeedPage {
        <<frontend>>
    }

    class DraftPage {
        <<frontend>>
    }

    class RegisterPage {
        <<frontend>>
    }

    ServiceAPI --> GrowthFactor : ORM
    ServiceAPI --> Like : ORM
    ServiceAPI --> ServiceOut : response DTO
    ServiceAPI --> PublishIn : request DTO
    ServiceAPI --> CurrentUserSingleton : current user
    ServiceAPI --> MinIOStorage : files

    UserAPI --> User : ORM
    UserAPI --> CurrentUserSingleton : current user

    Like --> User
    Like --> GrowthFactor

    TilePage --> ServiceAPI : list/filter
    FeedPage --> ServiceAPI : feed/next/like
    DraftPage --> ServiceAPI : draft/create/publish
    RegisterPage --> UserAPI : register/auth/logout
```

## Зависимости страниц

| Фронтенд-страница | Домен      | Метод    | URL                                 | Назначение                     |
| ----------------- | ---------- | -------- | ----------------------------------- | ------------------------------ |
| Плитка            | `services` | `GET`    | `/api/services`                     | Получение списка услуг         |
| Лента             | `services` | `GET`    | `/api/services/feed`                | Получение ленты                |
| Лента             | `services` | `GET`    | `/api/services/feed/{id}?next=true` | Переход к следующей услуге     |
| Лента             | `services` | `POST`   | `/api/services/{id}/like`           | Поставить лайк                 |
| Добавление        | `services` | `GET`    | `/api/services/draft`               | Загрузка текущего черновика    |
| Добавление        | `services` | `POST`   | `/api/services`                     | Создание услуги                |
| Добавление        | `services` | `PUT`    | `/api/services/draft`               | Изменение/публикация черновика |
| Добавление        | `services` | `DELETE` | `/api/services/{id}`                | Удаление услуги                |
| Регистрация       | `users`    | `POST`   | `/api/users/register`               | Регистрация пользователя       |
| Регистрация       | `users`    | `POST`   | `/api/users/auth`                   | Авторизация пользователя       |
| Регистрация       | `users`    | `POST`   | `/api/users/logout`                 | Выход из системы               |


| Метод    | URL                                 | Описание                                                                                                                                             |
| -------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET`    | `/api/services`                     | Получение списка доступных опубликованных услуг для отображения на странице «Плитка». Возвращает данные услуг, необходимые для карточек.             |
| `POST`   | `/api/services`                     | Создание новой услуги. На сервере создаётся запись `GrowthFactor`, устанавливаются системные поля, включая `created_at` и `creator_user_id`.         |
| `GET`    | `/api/services/draft`               | Получение текущего черновика услуги пользователя. Используется для загрузки данных на страницу «Добавление».                                         |
| `PUT`    | `/api/services/draft`               | Обновление/публикация текущего черновика. Передаваемые данные описывают услугу и её коэффициенты; при публикации может устанавливаться `formed_at`.  |
| `GET`    | `/api/services/feed`                | Получение ленты опубликованных услуг. Используется страницей «Лента».                                                                                |
| `GET`    | `/api/services/feed/{id}?next=true` | Получение следующего элемента ленты относительно услуги с указанным `id`. Параметр `next=true` указывает направление перехода к следующему элементу. |
| `POST`   | `/api/services/{id}/like`           | Установка лайка текущим пользователем для указанной услуги. Создаётся запись в таблице `likes`.                                                      |
| `DELETE` | `/api/services/{id}`                | Удаление услуги. Как правило, изменяет или устанавливает статус услуги `удален`, а не обязательно физически удаляет запись из БД.                    |
