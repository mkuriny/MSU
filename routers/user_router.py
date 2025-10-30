from fastapi import APIRouter, Depends
from app.core.container import Container

router = APIRouter()
container = Container()


@router.get("/")
def get_users(service=Depends(lambda: container.user_service)):
    return service.list_users()


@router.get("/{user_id}")
def get_user(user_id: int, service=Depends(lambda: container.user_service)):
    user = service.get_user(user_id)
    if user:
        return user
    return {"error": "Пользователь не найден"}