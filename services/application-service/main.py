import logging
import os
import sqlite3
from datetime import datetime
from typing import List, Optional
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

# Set up resource (used for identifying your service in observability tools)
resource = Resource(attributes={
    SERVICE_NAME: "application-service"
})

# Set tracer provider and span processor
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

# Register the tracer provider globally
trace.set_tracer_provider(provider)

# Initialize FastAPI app
app = FastAPI(title="Application Service - Smart Job Tracker")

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Prometheus metrics setup
Instrumentator().instrument(app).expose(app, include_in_schema=True, endpoint="/prometheus")

# Your routes and logic below...


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Adjust to your frontend's URL/port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("application_service")

# SQLite DB setup (file-based)
DB_FILE = "application.db"
is_new_db = not os.path.exists(DB_FILE)
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Schema setup
if is_new_db:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id TEXT PRIMARY KEY,
        company TEXT NOT NULL,
        position TEXT NOT NULL,
        status TEXT NOT NULL,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    conn.commit()
    logger.info("Initialized new SQLite DB", extra={"schema": "applications"})


# Models
class ApplicationCreate(BaseModel):
    company: str
    position: str
    status: str = Field(..., example="Applied")
    notes: Optional[str] = None


class Application(ApplicationCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


# Startup & shutdown logs
@app.on_event("startup")
def on_startup():
    logger.info("🚀 Service started", extra={"db": DB_FILE, "mode": "file-based"})


@app.on_event("shutdown")
def on_shutdown():
    conn.close()
    logger.info("🛑 Service shutdown")


# Health
@app.get("/health", tags=["Health"])
def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}


# Create
@app.post("/capplication", response_model=Application, tags=["Applications"])
def create_application(application: ApplicationCreate):
    app_id = uuid4()
    logger.info("hello")
    now = datetime.utcnow().isoformat()
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
@app.get("/applications", response_model=List[Application], tags=["Applications"])
def list_applications(tag: Optional[str] = Query(None, description="Filter applications by tag in notes")):
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
@app.get("/application/{app_id}", response_model=Application, tags=["Applications"])
def get_application(app_id: UUID):
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
@app.put("/application/{app_id}", response_model=Application, tags=["Applications"])
def update_application(app_id: UUID, update: ApplicationCreate):
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
@app.delete("/application/{app_id}", tags=["Applications"])
def delete_application(app_id: UUID):
    cursor.execute("SELECT * FROM applications WHERE id = ?", (str(app_id),))
    if not cursor.fetchone():
        logger.warning("Delete failed: Application not found", extra={"id": str(app_id)})
        raise HTTPException(status_code=404, detail="Application not found")
    cursor.execute("DELETE FROM applications WHERE id = ?", (str(app_id),))
    conn.commit()
    logger.info("Application deleted", extra={"id": str(app_id)})
    return {"message": "Application deleted"}


# Metrics Endpoint
@app.get("/metrics", tags=["Observability"])
def get_metrics():
    cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
    status_counts = {status: count for status, count in cursor.fetchall()}

    cursor.execute("SELECT notes FROM applications")
    notes = [note for (note,) in cursor.fetchall() if note]
    tag_counts = {}
    for note in notes:
        tags = [word[1:] for word in note.split() if word.startswith("#")]
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    logger.info("Metrics generated", extra={
        "status_metrics": status_counts,
        "tag_metrics": tag_counts,
        "total": sum(status_counts.values())
    })
    return {
        "total_applications": sum(status_counts.values()),
        "by_status": status_counts,
        "by_tag": tag_counts
    }
