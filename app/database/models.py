import uuid

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID


from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)

class Streamer(Base):
    __tablename__ = "streamers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)