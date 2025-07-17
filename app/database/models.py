import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Enum, String, Boolean, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from sqlalchemy.orm import column_property
from sqlalchemy import select, func


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
    streamer = relationship("Streamer", back_populates="stream_clips_processes")

class Streamer(Base):
    __tablename__ = "streamers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationship to StreamClipsProcess
    stream_clips_processes = relationship("StreamClipsProcess", back_populates="streamer")

    process_count = column_property(
        select(func.count(StreamClipsProcess.id))
        .where(StreamClipsProcess.streamer_id == id)
        .correlate_except(StreamClipsProcess)
        .scalar_subquery()
    )

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
    created_at = Column(DateTime, default=datetime.now(tz=timezone.utc))