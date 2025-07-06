from datetime import datetime
from typing import List, Dict


def fetch_mock_jobs(role: str) -> List[Dict]:
    """Pretend to hit a free jobs endpoint and return matches."""
    return [
        {
            "title": f"{role.title()} Engineer",
            "company": "OpenAI",
            "location": "Remote",
            "url": "https://openai.com/careers",
            "description": f"Work on cutting‑edge {role} problems with us.",
            "source": "MockAPI",
            "date_posted": datetime.utcnow().isoformat(),
        }
    ]
