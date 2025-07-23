import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Enum, String, Boolean, Text, Integer, DateTime, ForeignKey, event, Float, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship



from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)

class Instance(Base):
    __tablename__ = "instances"

    hostname = Column(String, primary_key=True)
    max_processes = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
    last_heartbeat = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
    
    # Relationship to StreamClipsProcess
    processes = relationship("StreamClipsProcess", back_populates="instance")

class StreamClipsProcess(Base):
    __tablename__ = "stream_clips_processes"

    __mapper_args__ = {
        "confirm_deleted_rows": False
    }

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    streamer_id = Column(UUID(as_uuid=True), ForeignKey("streamers.id"), nullable=False)
    instance_hostname = Column(String, ForeignKey("instances.hostname"), nullable=False)
    pid = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(tz=timezone.utc))
    last_activity = Column(DateTime(timezone=True), default=datetime.now(tz=timezone.utc))
    
    # Relationships
    streamer = relationship("Streamer", back_populates="stream_clips_process")
    instance = relationship("Instance", back_populates="processes")

class Streamer(Base):
    __tablename__ = "streamers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to StreamClipsProcess (one-to-one)
    stream_clips_process = relationship("StreamClipsProcess", back_populates="streamer", uselist=False, cascade="all, delete-orphan")

@event.listens_for(Streamer, "before_update")
def on_streamer_update(mapper, connection, target: Streamer):
    from app.core import stream_clips_processes
    from app.database.connection import get_db

    state = inspect(target)
    # Check if any field other than `last_processed_at` has changed
    dirty_keys = {attr.key for attr in state.attrs if attr.history.has_changes()}
    # Only stop if something other than 'last_processed_at' changed
    if dirty_keys - {'last_processed_at'} and target.stream_clips_process:
        db = next(get_db())
        try:
            stream_clips_processes.stop_process(db, str(target.stream_clips_process.id))
        except Exception as e:
            print(f"Error stopping process on streamer update: {e}")
            db.rollback()
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

class StreamConfig(Base):
    __tablename__ = "stream_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    clip_duration = Column(Float, nullable=False, default=60.0)
    window_timespan = Column(Float, nullable=False, default=30.0)
    sample_interval = Column(Integer, nullable=False, default=1)
    baseline_duration = Column(Integer, nullable=False, default=180)
    surge_threshold = Column(Float, nullable=False, default=2.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))

@event.listens_for(StreamConfig, "before_update")
def on_stream_config_update(mapper, connection, target: StreamConfig):
    """Stop all processes when config is updated so they restart with new settings."""
    from app.core import stream_clips_processes
    from app.database.connection import get_db
    
    db = next(get_db())
    try:
        stream_clips_processes.stop_all_processes()
    except Exception as e:
        print(f"Error stopping all processes: {e}")
    finally:
        db.close()

class Log(Base):
    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(Enum(LogLevel), nullable=False)
    created_at = Column(DateTime(timezone=True), default= lambda: datetime.now(tz=timezone.utc))