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

import recommendation_model as models
from recommendation_routes import router

resource = Resource(attributes={
    SERVICE_NAME: "recommendation-service"
})

provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

trace.set_tracer_provider(provider)


def setup_logger():
    # Structured logging setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logger = logging.getLogger("recommendation_service")
    return logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = setup_logger()
    conn = models.init_db()
    app.state.logger = logger
    app.state.conn = conn
    logger.info("Application is starting up...")
    yield
    logger.info("Application is shutting down...")


app = FastAPI(title="Recommendation Service - Smart Job Tracker", lifespan=lifespan)
app.state: State
app.include_router(router, prefix="/recommendation/v1")

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

# Prometheus metrics setup
Instrumentator().instrument(app).expose(app, include_in_schema=True, endpoint="/prometheus")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
