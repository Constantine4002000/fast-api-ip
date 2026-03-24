from model.pictures import Picture
import data.pictures as pictures_data


def get_one(name: str) -> Picture | None:
    return pictures_data.get_one(name=name)


def add_one(picture: Picture) -> int:
    return pictures_data.add_one(picture)
