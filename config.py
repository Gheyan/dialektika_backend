import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ATTACHMENT_URL = os.getenv("ATTACHMENT_URL")

