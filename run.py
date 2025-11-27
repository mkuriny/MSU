import uvicorn
import os
import sys

def main():
    """Запуск FastAPI-приложения."""
    # Убедимся, что Python видит пакет app/
    sys.path.append(os.path.dirname(__file__))

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()