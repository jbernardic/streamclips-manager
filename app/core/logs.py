from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import models
import app.schemas as schemas

def create(db: Session, source: str, message: str, level: models.LogLevel) -> models.Streamer:
    log = models.Log(source=source, message=message, level=level)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def list(db: Session, source: Optional[str], level: Optional[models.LogLevel], offset: int = 0, limit: int = 100):
    query = db.query(models.Log)
    if source:
        query = query.filter_by(source=source)
    if level:
        query = query.filter_by(level=level)
    return query.order_by(models.Log.created_at.desc()).offset(offset).limit(limit).all()