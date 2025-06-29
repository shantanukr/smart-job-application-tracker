# Smart Job Tracker - Microservices Ecosystem

## 📊 Project Overview

The **Smart Job Tracker** is a resilient, observable microservices-based application designed to help users track job applications, notes, statuses, and overall progress. It integrates best practices around **self-healing**, **dependency isolation**, **distributed tracing**, **metrics collection**, and **log aggregation**.

---

## ⚙️ Architecture Diagram

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

## 🚀 Services

### 1. Application Service

* Core service for tracking job applications.
* Stores company name, job title, notes, status, and timestamps.
* Uses **SQLite (in-memory or file-based)** for quick setup and persistence.
* Integrated with **OpenTelemetry (OTLP)** for distributed tracing.
* Exposes `/prometheus` for Prometheus scraping.

### 2. Notification Service

* Sends email or system notifications about application updates.
* Uses a pub/sub or direct API pattern.

### 3. Observability Stack

* **OpenTelemetry Collector**: Gathers traces and metrics.
* **Jaeger**: Visualizes distributed tracing.
* **Prometheus**: Collects metrics from services.
* **Grafana**: Visualizes metrics dashboards.

---

## 🧰 Technologies Used

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

## 📚 How to Run

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

## 📝 Environment Variables (Optional)

You may define `.env` files or Docker secrets for configuration:

```env
APPLICATION_PORT=8000
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
DATABASE_PATH=/data/applications.db
```

---

## 🚧 Development & Testing

```bash
# Run locally
uvicorn app.main:app --reload

# Run unit tests
pytest tests/
```

