from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as main_router
from app.api.workers import router as workers_router
from app.api.machines import router as machines_router
from app.api.issues import router as issues_router
from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.core.mongodb import (
    create_indexes,
    close_mongo_connection,
)


settings = get_settings()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    # MongoDB Atlas
    create_indexes()

    yield

    close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(main_router)
app.include_router(workers_router)
app.include_router(machines_router)
app.include_router(issues_router)
app.include_router(auth_router)


@app.get("/")
def root():

    return {
        "message": (
            "AI Industrial Virtual Supervisor "
            "API is running"
        )
    }