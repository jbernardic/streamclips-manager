from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CreateStreamer(BaseModel):
    name: str
    url: str
    is_active: bool = True

class Streamer(BaseModel):
    id: UUID4
    name: str
    url: str
    is_active: bool

class StreamClipsProcess(BaseModel):
    id: UUID4
    streamer_id: UUID4
    pid: int
    created_at: datetime