from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sqlite3

from database import get_connection
import recommendation_model as models
import recommendation_schema as schemas
from third_party_client import fetch_mock_jobs

router = APIRouter(tags=['Recommendation Route'])


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.post(
    "/fetch-jobs/{role}",
    response_model=List[schemas.JobApplicationOut],
    summary="Fetch jobs for a role from a third‑party API and save them",
)
def fetch_and_store_jobs(role: str, db: sqlite3.Connection = Depends(get_db)):
    jobs = fetch_mock_jobs(role)
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")

    saved_records = []
    for job in jobs:
        job_id = models.insert_job(db, job)
        job["id"] = job_id
        saved_records.append(job)

    return saved_records


@router.get(
    "/jobs",
    response_model=List[schemas.JobApplicationOut],
    summary="Return every stored job application",
)
def list_jobs(db: sqlite3.Connection = Depends(get_db)):
    return models.fetch_all_jobs(db)
