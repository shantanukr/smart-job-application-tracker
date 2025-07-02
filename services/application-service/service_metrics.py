from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check(request: Request):
    logger = request.app.state.logger
    logger.info("Health check requested")
    return {"status": "ok"}


@router.get("/metrics", tags=["Observability"])
def get_metrics(request: Request):
    logger = request.app.state.logger
    conn = request.app.state.conn
    cursor = conn.cursor()
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
