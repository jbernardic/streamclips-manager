
import dotenv

dotenv.load_dotenv()

from contextlib import asynccontextmanager
from app.core.users import create_admin_user
from app.scheduler import start_scheduler, stop_scheduler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import models, connection
from . import routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_admin_user()
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=routers.auth_router)
app.include_router(router=routers.streamer_router)
app.include_router(router=routers.stream_clips_router)