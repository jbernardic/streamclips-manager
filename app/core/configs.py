from sqlalchemy.orm import Session
from app.database import models
from app.database.connection import get_db

def init():
    db = next(get_db())
    try:
        stream_config = db.query(models.StreamConfig).first()
        if not stream_config:
            stream_config = models.StreamConfig()
            db.add(stream_config)
            db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

def get_stream_config(db: Session) -> models.StreamConfig:
    """Get the singleton StreamConfig instance, create with defaults if not exists."""
    config = db.query(models.StreamConfig).first()
    if not config:
        raise Exception("Config table missing")
    return config