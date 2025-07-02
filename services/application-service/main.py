import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.datastructures import State

import application_routes
import service_metrics
from application_schema import setup_sqlite_db_conn

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


def setup_logger():
    # Structured logging setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logger = logging.getLogger("application_service")
    return logger


# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = setup_logger()
    conn = setup_sqlite_db_conn(logger)
    app.state.logger = logger
    app.state.conn = conn
    logger.info("Application is starting up...")
    yield
    logger.info("Application is shutting down...")


app = FastAPI(title="Application Service - Smart Job Tracker", lifespan=lifespan)
app.state: State
app.include_router(application_routes.router, prefix="/api/v1", tags=["Application"])
app.include_router(service_metrics.router, prefix="/api/v1", tags=["ServiceMetrics"])

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Prometheus metrics setup
Instrumentator().instrument(app).expose(app, include_in_schema=True, endpoint="/prometheus")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
