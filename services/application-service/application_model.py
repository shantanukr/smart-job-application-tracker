from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class ApplicationCreate(BaseModel):
    company: str
    position: str
    status: str = Field(..., example="Applied")
    notes: Optional[str] = None


class Application(ApplicationCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime