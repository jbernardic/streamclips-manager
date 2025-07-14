from pydantic import BaseModel, UUID4

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CreateStreamer(BaseModel):
    name: str
    url: str

class Streamer(BaseModel):
    id: UUID4
    name: str
    url: str