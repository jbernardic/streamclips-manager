from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import models
import app.schemas as schemas


def create(db: Session, streamer: schemas.CreateStreamer) -> models.Streamer:
    new_streamer = models.Streamer(name=streamer.name, url=streamer.url, is_active=streamer.is_active)
    db.add(new_streamer)
    db.commit()
    db.refresh(new_streamer)
    return new_streamer


def update(db: Session, streamer: schemas.Streamer) -> models.Streamer:
    existing_streamer = db.query(models.Streamer).filter(models.Streamer.id == streamer.id).first()
    if not existing_streamer:
        raise HTTPException(status_code=404, detail=f"Streamer of id {streamer.id} not found!")
    
    existing_streamer.name = streamer.name
    existing_streamer.url = streamer.url
    existing_streamer.is_active = streamer.is_active

    db.commit()
    db.refresh(existing_streamer)

    return existing_streamer

def delete(db: Session, id: str):
    streamer = db.query(models.Streamer).filter(models.Streamer.id == id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail=f"Streamer with id {id} not found")

    db.delete(streamer)
    db.commit()

def get(db: Session, id: str) -> Optional[schemas.Streamer]:
    return db.query(models.Streamer).filter(models.Streamer.id == id).first()

def list(db: Session) -> List[schemas.Streamer]:
    return db.query(models.Streamer).all()