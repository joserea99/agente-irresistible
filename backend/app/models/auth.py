from pydantic import BaseModel
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str
    device_fingerprint: str = "unknown"

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "member"
    device_fingerprint: str = "unknown"

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict
