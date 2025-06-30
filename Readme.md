# Smart Job Tracker - Microservices Ecosystem

## Project Overview

The **Smart Job Tracker** is a resilient, observable microservices-based application designed to help users track job applications, notes, statuses, and overall progress. 
It integrates best practices around **self-healing**, **dependency isolation**, **distributed tracing**, **metrics collection**, and **log aggregation**.

1. Health Tracking: 
   * Monitoring whether a service is alive and functioning correctly, especially during startup or in runtime.
   * FastAPI already has a /health endpoint in the Application Service.
   * In Kubernetes, defined readiness & liveness probes to automatically restart or isolate it.

2. Dependency Isolation:
   * Each service, application-service, auth-service, etc is containerized using Docker and has its own SQLite.
   * Kubernetes is handling service isolation using pods and network policies with retry logic and circuit breakers with httpx + tenacity.

3. Observability Patterns:
   * Each serivce has techniques to monitor, trace, and analyze system behavior through Logs, Metrics, Traces
   * Prometheus + fastapi-instrumentator, OpenTelemetry + OTLP, Python logging, Grafana

---

## Architecture Diagram

```
                  +------------------+
                  |     Frontend     |
                  |  (React + Tailwind)
                  +--------+---------+
                           |
              +------------v-------------+
              |        API Gateway       |
              |    (FastAPI + CORS)      |
              +------------+-------------+
                           |
            +--------------+---------------------+
            |                                    |
+-----------v------------+           +-----------v----------+
|   Application Service  |           |   Notification Svc   |
| (FastAPI + SQLite/OTEL)|           |  (FastAPI + Broker)  |
+-----------+------------+           +-----------+----------+
            |                                    |
            +-----------------+------------------+
                              |
                    +---------v--------+
                    |  Observability   |
                    | (OTel Collector) |
                    +---------+--------+
                              |
         +--------------------+---------------------+
         |                                          |
 +-------v--------+                      +----------v----------+
 |   Jaeger (UI)  |                      |  Prometheus + Grafana |
 +----------------+                      +-----------------------+
```

---

## Services

### 1. Application Service

* Core service for tracking job applications.
* Stores company name, job title, notes, status, and timestamps.
* Uses **SQLite (in-memory or file-based)** for quick setup and persistence.
* Integrated with **OpenTelemetry (OTLP)** for distributed tracing.
* Exposes `/prometheus` for Prometheus scraping.

### Notification Service

* Sends email or system notifications about application updates.
* Uses a pub/sub or direct API pattern.

### Observability Stack

* **OpenTelemetry Collector**: Gathers traces and metrics.
* **Jaeger**: Visualizes distributed tracing.
* **Prometheus**: Collects metrics from services.
* **Grafana**: Visualizes metrics dashboards.

---

## Technologies Used

| Technology           | Purpose                            |
| -------------------- | ---------------------------------- |
| **FastAPI**          | Python-based web service framework |
| **SQLite**           | Lightweight SQL database           |
| **OpenTelemetry**    | Observability: tracing and metrics |
| **Prometheus**       | Metrics collection                 |
| **Jaeger**           | Trace visualization                |
| **Grafana**          | Dashboard metrics UI               |
| **Docker**           | Containerization                   |
| **React + Tailwind** | Frontend (Optional UI)             |

---

## How to Run

### 1. Prerequisites

* Docker & Docker Compose
* Git

### 2. Clone Repo

```bash
git clone https://github.com/shantanukr/smart-job-tracker.git
cd smart-job-tracker
```

### 3. Start Services

```bash
docker-compose up --build
```

### 4. Access Services

* **Application Service API**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Prometheus Metrics**: [http://localhost:9090](http://localhost:9090)
* **Jaeger UI**: [http://localhost:16686](http://localhost:16686)
* **Grafana**: [http://localhost:3000](http://localhost:3000) (admin/admin)

---

## Environment Variables (Optional)

You may define `.env` files or Docker secrets for configuration:

```env
APPLICATION_PORT=8000
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
DATABASE_PATH=/data/applications.db
```

---

## Development & Testing

```bash
# Run locally
uvicorn app.main:app --reload

# Run unit tests
pytest tests/
```

## Running on Kubernetes

### Prerequisites:

* Docker Desktop with Kubernetes enabled

* kubectl CLI installed

 
### Steps:

### Build and Push Images

```commandline
docker build -t your-dockerhub/app-service ./services/application-service
docker push your-dockerhub/app-service
```


### Apply Kubernetes Configurations
```commandline

kubectl apply -f k8/base/application-service/ 
kubectl apply -f k8/base/otel/ 
kubectl apply -f application-tracker-backend/k8/prometheus/ 
kubectl apply -f application-tracker-backend/k8/grafana/
```
Another Way
```commandline
kubectl apply -R -f k8/base/
```


### Verify Pods
````commandline
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
````


### Port Forward to Access Services with Debugging
```commandline
kubectl port-forward svc/application-service 8000:80
kubectl port-forward svc/prometheus 9090:9090
kubectl port-forward svc/grafana 3000:3000
```


### View Logs
```commandline
kubectl logs -f <pod-name>
```


### Delete Old Deployments

```commandline
kubectl delete deployment application-service
kubectl delete pod <pod-name>
kubectl delete svc application-service
```


## Metrics & Observability

Prometheus scrapes /prometheus endpoint on the application-service

Grafana dashboards visualize performance, latency, and uptime

OTEL Collector collects traces via port 4318

## Clean Up

```commandline
kubectl delete -f k8s/
docker-compose down -v
```
