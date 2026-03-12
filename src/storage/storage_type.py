import os
from abc import ABC, abstractmethod
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
import magic
from supabase import create_client
import uuid
import urllib.parse


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
        # Generate a unique filename using uuid and preserve the original filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        try:
            file_content = await file.read()

            # Determine MIME type for the file
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file_content)

            # URL encode the filename to handle special characters like spaces, etc.
            encoded_filename = urllib.parse.quote(unique_filename)

            # Upload the file to Supabase storage
            response = self.supabase.storage.from_(SUPABASE_BUCKET).upload(
                unique_filename, 
                file_content,  
                {"content-type": mime_type}  
            )

            if hasattr(response, 'path') and response.path:
                # Return the URL of the uploaded file, properly formatted with URL encoding
                file_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{encoded_filename}"
                return file_url
            else:
                raise HTTPException(status_code=500, detail="Upload failed: No valid response path")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    def get_url(self, path: str) -> str:
        # Return the public URL of the file
        return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"

    async def delete(self, filename: str):
        try:
            # URL encode the filename to handle any special characters in the file name
            encoded_filename = urllib.parse.quote(filename)
            
            # Delete the file from Supabase storage
            response = self.supabase.storage.from_(SUPABASE_BUCKET).remove([encoded_filename])

            # Check if the delete operation was successful
            if hasattr(response, 'status_code') and response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Delete failed: {response.error_message}")
            return {"message": "File deleted successfully."}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

def get_storage() -> StorageProvider:
    return SupabaseStorage()  

StorageDep = Annotated[StorageProvider, Depends(get_storage)]