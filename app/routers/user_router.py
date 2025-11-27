from fastapi import APIRouter, Depends
from app.core.container import Container


router = APIRouter()
container = Container()

@router.post("/run-task")
def run_task(service=Depends(lambda: container.user_service)):
    """
    Пример: запускает службу при вызове API
    """
    result = service.list_users()  # здесь вызывается нужная функция
    return {"status": "success", "result": result}

@router.get("/")
def get_users(service=Depends(lambda: container.user_service)):
    return service.list_users()


@router.get("/{user_id}")
def get_user(user_id: int, service=Depends(lambda: container.user_service)):
    user = service.get_user(user_id)
    if user:
        return user
    return {"error": "Пользователь не найден"}