from datetime import datetime
from pydantic import BaseModel


class JobApplicationBase(BaseModel):
    title: str
    company: str
    location: str
    url: str
    description: str
    source: str = "Unknown"


class JobApplicationCreate(JobApplicationBase):
    """Used internally when we harvest roles from an API."""
    date_posted: datetime


class JobApplicationOut(JobApplicationBase):
    id: int
    date_posted: datetime

    class Config:
        orm_mode = True
