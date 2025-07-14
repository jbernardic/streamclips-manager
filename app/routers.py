from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.core import auth, streamers
import app.schemas as schemas

auth_router = APIRouter(prefix="/auth")
streamer_router = APIRouter(prefix="/streamers", dependencies=[Depends(auth.get_current_user)])

@auth_router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    return auth.login(db, user)

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