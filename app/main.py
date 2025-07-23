
import dotenv
dotenv.load_dotenv(override=True)

from app.core import configs, instances, stream_clips_processes

from contextlib import asynccontextmanager
from app.core.users import create_admin_user
from app.scheduler import start_scheduler, stop_scheduler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.admin as admin

from . import routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    configs.init()
    instances.register_instance()
    create_admin_user()
    start_scheduler()
    yield
    stop_scheduler()
    stream_clips_processes.stop_instance_processes(instances.get_current_hostname())

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

admin.init(app)