from fastapi import FastAPI
from . import rest
from database.database import create_tables
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

origins = ['*']

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup logic
    await create_tables()
    yield
    # Run shutdown logic (if any) here


def get_app() -> FastAPI:
    app = FastAPI(title="Dialektika Webapp", lifespan=lifespan)
    app.include_router(rest.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,            # Allows specific origins
        allow_credentials=True,           # Allows cookies/auth headers
        allow_methods=["*"],              # Allows all methods (GET, POST, etc.)
        allow_headers=["*"],              # Allows all headers
    )

    @app.get("/")
    async def root():
        return {"Connection Status": "Success"}

    return app