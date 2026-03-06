import uvicorn
from api import get_app
from database.database import create_tables
import asyncio
from fastapi.staticfiles import StaticFiles

app = get_app()

app.mount("/static", StaticFiles(directory="uploads"), name="static")

def main():
    asyncio.run(create_tables())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()