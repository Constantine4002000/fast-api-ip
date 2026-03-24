from fastapi import File, UploadFile, Form, HTTPException, APIRouter
from fastapi.responses import Response
from model.pictures import Picture
import service.pictures as pictures_service 
import numpy as np
import cv2


router = APIRouter(prefix='/pictures')


@router.post("/upload", summary="Загрузка нового изображения")
async def add_one(
    file: UploadFile = File(..., description="Изображение (jpg, png, jpeg и т.д.)"),
    name: str = Form(..., min_length=1, description="Имя изображения (обязательное, должно быть уникальным)"),
    description: str = Form("", description="Описание изображения (необязательно)")
):
    """
    Загружает изображение в базу данных.
    
    В Swagger / Redoc / docs будет отображаться:
    - Поле выбора файла (file)
    - Поле ввода имени (name)
    - Поле ввода описания (description)
    
    Автоматически:
    - dt = текущая дата/время
    - изображение сохраняется как BLOB (PNG)
    """
    # 1. Проверка, что пришёл именно файл-изображение
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Загруженный файл должен быть изображением"
        )

    # 2. Читаем содержимое файла
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Не удалось прочитать файл")

    # 3. Декодируем в numpy-массив через OpenCV
    nparr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(
            status_code=400,
            detail="Не удалось декодировать изображение. Возможно, файл повреждён или формат не поддерживается."
        )

    # 4. Создаём объект Picture (dt заполнится автоматически благодаря default_factory)
    picture = Picture(
        name=name.strip(),
        img=img,
        description=description.strip() if description else ""
    )

    # 5. Сохраняем через сервисный слой
    try:
        picture_id = pictures_service.add_one(picture)
        return {
            "success": True,
            "id": picture_id,
            "name": name,
            "message": "Изображение успешно загружено в базу данных"
        }
    except ValueError as e:          # например, ошибка кодирования PNG
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сохранении в базу: {str(e)}"
        )
    

# ====================== ВЫГРУЗКА (ПОЛУЧЕНИЕ) ======================
@router.get("/{name}", summary="Получить изображение по имени")
async def get_one(name: str):
    """
    GET /pictures/мое_изображение
    
    В Swagger будет поле для ввода имени.
    После нажатия "Execute" в браузере сразу откроется картинка.
    """
    picture = pictures_service.get_one(name)

    if picture is None:
        raise HTTPException(
            status_code=404,
            detail=f"Изображение с именем '{name}' не найдено"
        )

    # Кодируем numpy-массив обратно в PNG
    success, encoded_img = cv2.imencode('.png', picture.img)
    if not success:
        raise HTTPException(status_code=500, detail="Ошибка кодирования изображения")

    return Response(
        content=encoded_img.tobytes(),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={name}.png"}
    )