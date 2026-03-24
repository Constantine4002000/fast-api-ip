from .init import conn, curs
from model.pictures import Picture
import cv2
import numpy as np
from datetime import datetime


# ====================== Создание таблицы и индекса ======================
curs.execute('''
    CREATE TABLE IF NOT EXISTS pictures(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        image_data BLOB NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

curs.execute('CREATE INDEX IF NOT EXISTS idx_name ON pictures(name)')
conn.commit()


# ====================== Вспомогательные функции ======================
def row_to_model(row: tuple) -> Picture | None:
    """
    Преобразует строку из таблицы pictures в объект Picture (новая версия модели).
    
    Поля в row (порядок из SELECT *):
      0: id (int)          — игнорируется (в новой модели Picture его нет)
      1: name (str)
      2: description (str | None)
      3: image_data (bytes)
      4: created_at (str)
    
    Возвращает None, если строка некорректна или изображение не удалось декодировать.
    """
    if row is None or len(row) < 5:
        return None

    try:
        _, name, description, image_bytes, created_at = row   # id игнорируем

        # 1. Декодируем BLOB → numpy-массив (OpenCV)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            print(f"Не удалось декодировать изображение для записи name='{name}'")
            return None

        # 2. Приводим created_at к datetime
        if isinstance(created_at, str):
            dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        elif isinstance(created_at, datetime):
            dt = created_at
        else:
            dt = datetime.now()   # fallback (на всякий случай)

        # 3. Создаём объект новой модели Picture (без id!)
        return Picture(
            name=str(name),
            img=img,                                 # BGR numpy array
            description=description or "",           # None → "" (теперь description обязательный str)
            dt=dt
        )

    except Exception as e:
        print(f"Ошибка при преобразовании строки → Picture: {e}")
        return None


def model_to_dict(picture: Picture) -> dict:
    """Преобразует модель Picture в словарь (Pydantic)."""
    return picture.model_dump()


# ====================== CRUD ======================
def get_one(name: str) -> Picture | None:
    """Возвращает одну запись по имени или None."""
    qry = "SELECT * FROM pictures WHERE name = :name"
    curs.execute(qry, {"name": name})
    return row_to_model(curs.fetchone())


def add_one(picture: Picture) -> int:
    """
    Сохраняет объект Picture в таблицу pictures.

    Возвращает:
        id новой записи (AUTOINCREMENT)
    """
    # 1. Кодируем изображение в PNG (без потерь)
    success, encoded_img = cv2.imencode('.png', picture.img)
    if not success:
        raise ValueError("Не удалось закодировать изображение в PNG")
    image_blob = encoded_img.tobytes()

    # 2. Подготавливаем дату (в новой модели dt всегда есть)
    created_at_str = picture.dt.strftime('%Y-%m-%d %H:%M:%S')

    # 3. Вставляем запись
    curs.execute('''
        INSERT INTO pictures (name, description, image_data, created_at)
        VALUES (?, ?, ?, ?)
    ''', (picture.name, picture.description, image_blob, created_at_str))

    conn.commit()                    # ← ОБЯЗАТЕЛЬНО!
    return curs.lastrowid