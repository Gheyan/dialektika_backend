import os
from abc import ABC, abstractmethod
from fastapi import Depends
from typing import Annotated
from dotenv import load_dotenv

load_dotenv()


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
        base = os.getenv("BASE_URL", "http://localhost:8000")
        return f"{base}/static/{path}"

    async def delete(self, filename: str):
        path = os.path.join(self.upload_dir, filename)

        if os.path.exists(path):
            os.remove(path)


def get_storage() -> StorageProvider:
    storage_type = os.getenv("STORAGE_TYPE", "LOCAL")

    if storage_type == "LOCAL":
        return LocalStorage()
    
    return LocalStorage()

StorageDep = Annotated[StorageProvider, Depends(get_storage)]
