from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    username: str
    embedding: List[float]

class LoginResult(BaseModel):
    username: str
    match: bool
    distance: float
