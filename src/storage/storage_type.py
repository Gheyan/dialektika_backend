import os
from abc import ABC, abstractmethod
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app and static file serving
app = FastAPI()

# Mount the "uploads" directory to serve as static files under "/media"
app.mount("/media", StaticFiles(directory="uploads"), name="media")


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, file, filename: str) -> str:
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        pass

    @abstractmethod
    async def delete(self, filename: str):
        pass


class LocalStorage(StorageProvider):

    def __init__(self, upload_dir="uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def upload(self, file, filename: str) -> str:
        path = os.path.join(self.upload_dir, filename)

        with open(path, "wb") as buffer:
            buffer.write(await file.read())

        return filename

    def get_url(self, path: str) -> str:
        # Use ATTACHMENT_URL from environment variable, fallback to default if not set
        attachment_url = os.getenv("ATTACHMENT_URL", "https://dialektika-backend.onrender.com/media")
        return f"{attachment_url}/{path}"

    async def delete(self, filename: str):
        path = os.path.join(self.upload_dir, filename)

        if os.path.exists(path):
            os.remove(path)


def get_storage() -> StorageProvider:
    # Get storage type from environment variable, default to LOCAL
    storage_type = os.getenv("STORAGE_TYPE", "LOCAL")

    if storage_type == "LOCAL":
        return LocalStorage()
    
    return LocalStorage()

StorageDep = Annotated[StorageProvider, Depends(get_storage)]