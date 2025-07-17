from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import asc
from sqlalchemy.orm import Session
from app.database import models
import app.schemas as schemas

MAX_LOG_TIME_MINUTES = 1

# def remove_old_logs(db: Session):
#     cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=MAX_LOG_TIME_MINUTES)
#     db.query(models.Log).filter(models.Log.created_at <= cutoff).delete(synchronize_session=False)
#     db.commit()

def create(db: Session, source: str, message: str, level: models.LogLevel) -> models.Streamer:

    #remove_old_logs(db)

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