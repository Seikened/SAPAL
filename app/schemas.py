from datetime import datetime
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    description: str | None = None

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ItemRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
