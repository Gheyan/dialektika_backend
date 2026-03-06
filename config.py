import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
ATTACHMENT_URL = os.getenv("ATTACHMENT_URL")