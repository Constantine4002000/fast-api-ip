# FastAPI Image Processing — Лабораторная работа №4

## Обзор проекта

Это учебный проект для освоения создания **постоянного уровня данных** в многоуровневом веб-приложении на FastAPI. Приложение предназначено для обработки изображений и распознавания образов.

### Основные технологии

-   **FastAPI** — веб-фреймворк для создания API
-   **SQLite** — реляционная база данных (через DB-API/PEP 249)
-   **Pydantic** — валидация и сериализация данных
-   **OpenCV** — обработка изображений
-   **NumPy** — работа с массивами изображений

### Архитектура (трёхуровневая)

Проект следует принципам из главы 10 книги Билла Любановича «FastAPI. Веб-разработка на Python»:

```         
fast-api/
├── data/           # Уровень данных (SQLite + DB-API)
│   ├── __init__.py
│   ├── init.py     # Подключение к БД
│   └── pictures.py # CRUD-операции с изображениями
├── db/             # Файл базы данных (pictures.db)
├── model/          # Pydantic-модели
│   ├── __init__.py
│   └── pictures.py # Модель Picture
├── service/        # Бизнес-логика + OpenCV
│   ├── __init__.py
│   └── pictures.py # Сервисный слой
├── src/            # Точка входа приложения
│   └── main.py     # FastAPI app
├── web/            # FastAPI-роутеры (уровень представления)
│   ├── __init__.py
│   └── pictures.py # HTTP-эндпоинты
└── lab-work.qmd    # Исходный документ лабораторной работы
```

## Модель данных

**model/pictures.py** — Pydantic-модель `Picture`:

``` python
class Picture(BaseModel):
    name: str
    img: np.ndarray          # Изображение как numpy-массив
    description: str = ""    # Описание (необязательно)
    dt: datetime             # Дата/время создания
```

`model_config = {"arbitrary_types_allowed": True}` — обязательно для `np.ndarray`.

## База данных

**Таблица `pictures`:**

| Поле        | Тип                 | Описание              |
|-------------|---------------------|-----------------------|
| id          | INTEGER PRIMARY KEY | Автоинкремент         |
| name        | TEXT NOT NULL       | Имя изображения       |
| description | TEXT                | Описание              |
| image_data  | BLOB NOT NULL       | Бинарные данные (PNG) |
| created_at  | DATETIME            | Дата создания         |

**Переменная окружения:** `PICTURES_SQLITE_DB` (по умолчанию: `db/pictures.db`)

## API Endpoints

| Метод | Маршрут            | Описание                                   |
|-------|--------------------|--------------------------------------------|
| POST  | `/pictures/upload` | Загрузка изображения (multipart/form-data) |
| GET   | `/pictures/{name}` | Получение изображения по имени             |

### Параметры для загрузки (POST /pictures/upload)

-   `file` — изображение (jpg, png, jpeg)
-   `name` — имя изображения (обязательно, уникальное)
-   `description` — описание (необязательно)

## Запуск приложения

``` bash
# Активация виртуального окружения (если есть)
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Запуск сервера
uvicorn src.main:app --reload
```

**Swagger UI:** http://127.0.0.1:8000/docs

## Поток данных

### Загрузка изображения

1.  `UploadFile.read()` → `bytes`
2.  `cv2.imdecode()` → `np.ndarray` (BGR)
3.  Создание объекта `Picture`
4.  `service.add_one()` → `data.add_one()`
5.  `cv2.imencode('.png')` → `BLOB`
6.  `INSERT INTO pictures` → SQLite

### Получение изображения

1.  `SELECT * FROM pictures WHERE name = ?`
2.  `row_to_model()`: BLOB → `np.frombuffer()` → `cv2.imdecode()`
3.  Возврат `Picture` объекта
4.  `cv2.imencode('.png')` → `Response` с `media_type="image/png"`

## Задания для реализации (практическая часть)

Согласно лабораторной работе, необходимо добавить:

1.  **DELETE /pictures/{name}** — удаление изображения
2.  **PATCH /pictures/{name}** — обновление метаданных (description)
3.  **Обработка изображений** (три операции):
    -   Градации серого (`cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`)
    -   Выделение границ (`cv2.Canny()`)
    -   Размытие (`cv2.GaussianBlur()`)

## Особенности реализации

-   **data/init.py**: глобальные `conn` и `curs`, инициализация при импорте
-   **data/pictures.py**: индекс по полю `name` для ускорения поиска
-   **web/pictures.py**: валидация типа файла (`content_type.startswith("image/")`)
-   **OpenCV**: изображения хранятся в формате BGR (не RGB)

## Контрольные вопросы

См. раздел "Контрольные вопросы к лабораторной работе" в файле `lab-work.qmd` (20 вопросов по архитектуре, CRUD-операциям и методам OpenCV).