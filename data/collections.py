growth_factors_collection = [
    {
        "id": 1,
        "growth_factor_name": "Количество пользователей",
        "growth_factor_description": (
            "Рост числа пользователей увеличивает объём профилей и связанных "
            "с пользователями записей."
        ),
        "growth_coefficient": 1.10,
        "storage_impact_coefficient": 0.80,
        "growth_factor_status": "опубликован",
        "image_key": "users_growth.png",
        "video_key": "users_growth.mp4",
        "like_user_ids": [1, 2, 4, 7, 11],
    },
    {
        "id": 2,
        "growth_factor_name": "Частота операций",
        "growth_factor_description": (
            "Увеличение частоты операций ускоряет накопление событий, журналов "
            "и других операционных записей."
        ),
        "growth_coefficient": 1.05,
        "storage_impact_coefficient": 0.50,
        "growth_factor_status": "опубликован",
        "image_key": "operations_frequency.png",
        "video_key": "operations_frequency.mp4",
        "like_user_ids": [1, 3, 4, 8],
    },
    {
        "id": 3,
        "growth_factor_name": "Размер записей",
        "growth_factor_description": (
            "Рост среднего размера одной записи напрямую увеличивает требуемый "
            "объём хранения при неизменном числе записей."
        ),
        "growth_coefficient": 1.02,
        "storage_impact_coefficient": 1.00,
        "growth_factor_status": "черновик",
        "image_key": "record_size.png",
        "video_key": "record_size.mp4",
        "like_user_ids": [2, 5, 9],
    },
    {
        "id": 4,
        "growth_factor_name": "Архивный фактор роста",
        "growth_factor_description": (
            "Увеличение объёма данных за счёт переноса устаревших записей в "
            "долгосрочное архивное хранилище и кумулятивного накопления "
            "исторических логов."
        ),
        "growth_coefficient": 1.15,
        "storage_impact_coefficient": 0.40,
        "growth_factor_status": "удален",
        "image_key": "archive_growth.png",
        "video_key": "archive_retention.mp4",
        "like_user_ids": [1, 4, 12, 15]
  },
  {
    "id": 5,
    "growth_factor_name": "Объём событий хранения",
    "growth_factor_description": (
        "Рост интенсивности генерации системных событий, транзакционных "
        "логов и пользовательских действий, увеличивающий плотность записи "
        "в единицу времени."
    ),
    "growth_coefficient": 1.35,
    "storage_impact_coefficient": 0.85,
    "growth_factor_status": "удален",
    "image_key": "event_volume.png",
    "video_key": "event_streaming.mp4",
    "like_user_ids": [3, 7, 9, 22, 45]
  }
]
