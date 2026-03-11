import os
from abc import ABC, abstractmethod
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
import magic
from supabase import create_client
import uuid


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "uploads") 

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

class SupabaseStorage(StorageProvider):
    def __init__(self):
        self.supabase = supabase  

    async def upload(self, file, filename: str) -> str:
        unique_filename = f"{uuid.uuid4()}_{filename}"

        try:
            file_content = await file.read()

            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file_content)

            response = self.supabase.storage.from_(SUPABASE_BUCKET).upload(
                unique_filename, 
                file_content,  
                {"content-type": mime_type}  
            )

            if hasattr(response, 'path') and response.path:
                file_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{response.path}"
                return file_url
            else:
                raise HTTPException(status_code=500, detail="Upload failed: No valid response path")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    def get_url(self, path: str) -> str:
        return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"

    async def delete(self, filename: str):
        try:
            response = self.supabase.storage.from_(SUPABASE_BUCKET).remove([filename])
            if hasattr(response, 'status_code') and response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Delete failed: {response.error_message}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

def get_storage() -> StorageProvider:
    return SupabaseStorage()  

StorageDep = Annotated[StorageProvider, Depends(get_storage)]