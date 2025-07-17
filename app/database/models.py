import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Enum, String, Boolean, Text, Integer, DateTime, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship



from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)

class StreamClipsProcess(Base):
    __tablename__ = "stream_clips_processes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    streamer_id = Column(UUID(as_uuid=True), ForeignKey("streamers.id"), nullable=False)
    pid = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))
    
    # Relationship to Streamer
    streamer = relationship("Streamer", back_populates="stream_clips_process")

class Streamer(Base):
    __tablename__ = "streamers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationship to StreamClipsProcess (one-to-one)
    stream_clips_process = relationship("StreamClipsProcess", back_populates="streamer", uselist=False, cascade="all, delete-orphan")

@event.listens_for(Streamer, "before_update")
def on_streamer_update(mapper, connection, target: Streamer):
    from app.core import stream_clips_processes
    from app.database.connection import get_db
    
    if target.stream_clips_process:
        db = next(get_db())
        try:
            stream_clips_processes.stop_process(db, str(target.stream_clips_process.id))
        except Exception as e:
            print(f"Error stopping process on streamer update: {e}")
        finally:
            db.close()

@event.listens_for(Streamer, "before_delete")
def on_streamer_delete(mapper, connection, target: Streamer):
    from app.core import stream_clips_processes
    from app.database.connection import get_db
    
    if target.stream_clips_process:
        db = next(get_db())
        try:
            stream_clips_processes.stop_process(db, str(target.stream_clips_process.id))
        except Exception as e:
            print(f"Error stopping process on streamer delete: {e}")
        finally:
            db.close()

class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class Log(Base):
    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(Enum(LogLevel), nullable=False)
    created_at = Column(DateTime(timezone=True), default= lambda: datetime.now(tz=timezone.utc))