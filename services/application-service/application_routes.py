from datetime import datetime
from typing import List, Optional
from uuid import uuid4, UUID
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import pybreaker

from fastapi import APIRouter, Request, Query, HTTPException

from application_model import Application, ApplicationCreate

router = APIRouter()

auth_service_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="AuthServiceCircuitBreaker"
)

@retry(
    retry=retry_if_exception_type(httpx.RequestError),
    wait=wait_fixed(2),
    stop=stop_after_attempt(3),
)

@auth_service_breaker
def verify_user_with_auth_service(user_id: str, logger):
    try:
        response = httpx.get(f"http://auth-service/api/verify/{user_id}", timeout=5.0)
        response.raise_for_status()
        logger.info("Auth service verification successful")
        return response.json()
    except httpx.RequestError as e:
        logger.warning(f"Auth service failed: {e}")
        raise

@router.post("/capplication", response_model=Application, tags=["Applications"])
def create_application(request: Request, application: ApplicationCreate, user_id: str = "demo-user"):
    logger = request.app.state.logger
    conn = request.app.state.conn
    app_id = uuid4()

    try:
        auth_response = verify_user_with_auth_service(user_id, logger)
        if not auth_response.get("valid"):
            raise HTTPException(status_code=403, detail="User not authorized")
    except pybreaker.CircuitBreakerError:
        logger.error("Auth Service is down (circuit breaker open)")
        raise HTTPException(status_code=503, detail="Auth Service temporarily unavailable")

    logger.info("hello")
    now = datetime.utcnow().isoformat()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO applications (id, company, position, status, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (str(app_id), application.company, application.position,
          application.status, application.notes, now, now))
    conn.commit()
    logger.info("Application created", extra={"id": str(app_id), "status": application.status})
    return Application(id=app_id, created_at=datetime.fromisoformat(now), updated_at=datetime.fromisoformat(now),
                       **application.dict())


# List with optional tag filtering
@router.get("/applications", response_model=List[Application], tags=["Applications"])
def list_applications(request: Request,
                      tag: Optional[str] = Query(None, description="Filter applications by tag in notes")):
    logger = request.app.state.logger
    conn = request.app.state.conn
    cursor = conn.cursor()
    if tag:
        cursor.execute("SELECT * FROM applications WHERE notes LIKE ?", (f"%#{tag}%",))
        logger.info("Filtered applications by tag", extra={"tag": tag})
    else:
        cursor.execute("SELECT * FROM applications")
        logger.info("Fetched all applications")
    rows = cursor.fetchall()
    logger.info("Applications read", extra={"count": len(rows)})
    return [
        Application(
            id=UUID(row[0]),
            company=row[1],
            position=row[2],
            status=row[3],
            notes=row[4],
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6])
        ) for row in rows
    ]


# Retrieve
@router.get("/application/{app_id}", response_model=Application, tags=["Applications"])
def get_application(request: Request, app_id: UUID):
    logger = request.app.state.logger
    conn = request.app.state.conn
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE id = ?", (str(app_id),))
    row = cursor.fetchone()
    if not row:
        logger.warning("Application not found", extra={"id": str(app_id)})
        raise HTTPException(status_code=404, detail="Application not found")
    logger.info("Application retrieved", extra={"id": str(app_id)})
    return Application(
        id=UUID(row[0]),
        company=row[1],
        position=row[2],
        status=row[3],
        notes=row[4],
        created_at=datetime.fromisoformat(row[5]),
        updated_at=datetime.fromisoformat(row[6])
    )


# Update
@router.put("/application/{app_id}", response_model=Application, tags=["Applications"])
def update_application(request: Request, app_id: UUID, update: ApplicationCreate):
    logger = request.app.state.logger
    conn = request.app.state.conn
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE id = ?", (str(app_id),))
    if not cursor.fetchone():
        logger.warning("Update failed: Application not found", extra={"id": str(app_id)})
        raise HTTPException(status_code=404, detail="Application not found")
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        UPDATE applications
        SET company = ?, position = ?, status = ?, notes = ?, updated_at = ?
        WHERE id = ?
    ''', (update.company, update.position, update.status, update.notes, now, str(app_id)))
    conn.commit()
    logger.info("Application updated", extra={"id": str(app_id), "new_status": update.status})
    return Application(id=app_id, created_at=datetime.fromisoformat(now), updated_at=datetime.fromisoformat(now),
                       **update.dict())


# Delete
@router.delete("/application/{app_id}", tags=["Applications"])
def delete_application(request: Request, app_id: UUID):
    logger = request.app.state.logger
    conn = request.app.state.conn
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM applications WHERE id = ?", (str(app_id),))
    if not cursor.fetchone():
        logger.warning("Delete failed: Application not found", extra={"id": str(app_id)})
        raise HTTPException(status_code=404, detail="Application not found")
    cursor.execute("DELETE FROM applications WHERE id = ?", (str(app_id),))
    conn.commit()
    logger.info("Application deleted", extra={"id": str(app_id)})
    return {"message": "Application deleted"}
