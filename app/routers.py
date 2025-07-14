from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import UUID4
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core import auth, streamers, stream_clips_processes
import app.schemas as schemas

auth_router = APIRouter(prefix="/auth")
streamer_router = APIRouter(prefix="/streamers", dependencies=[Depends(auth.get_current_user)])
stream_clips_router = APIRouter(prefix="/stream-clips-processes", dependencies=[Depends(auth.get_current_user)])

@auth_router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    return auth.login(db, schemas.UserLogin(username=form_data.username, password=form_data.password))

@streamer_router.post("/")
def create_streamer(
    streamer: schemas.CreateStreamer,
    db: Session = Depends(get_db)
):
    return streamers.create(db, streamer)

@streamer_router.put("/", response_model=schemas.Streamer)
def update_streamer(
    streamer: schemas.Streamer,
    db: Session = Depends(get_db)
):
    return streamers.update(db, streamer)

@streamer_router.delete("/{id}")
def update_streamer(
    id: UUID4,
    db: Session = Depends(get_db)
):
    return streamers.delete(db, id)

@streamer_router.get("/")
def list_streamers(
    db: Session = Depends(get_db)
):
    return streamers.list(db)


@streamer_router.get("/{id}")
def get_streamer(
    id: UUID4,
    db: Session = Depends(get_db)
):
    return streamers.get(db, id)


# Stream Clips Process Routes
@stream_clips_router.get("/", response_model=list[schemas.StreamClipsProcess])
def list_stream_clips_processes(
    db: Session = Depends(get_db)
):
    return stream_clips_processes.list_all(db)


@stream_clips_router.get("/{id}", response_model=schemas.StreamClipsProcess)
def get_stream_clips_process(
    id: UUID4,
    db: Session = Depends(get_db)
):
    return stream_clips_processes.get(db, id)


@stream_clips_router.post("/{id}/stop")
def stop_stream_clips_process(
    id: UUID4,
    db: Session = Depends(get_db)
):
    stream_clips_processes.stop_process(db, id)


@stream_clips_router.post("/{id}/start")
def start_stream_clips_process(
    id: UUID4,
    db: Session = Depends(get_db)
):
    return stream_clips_processes.start_process(db, id)