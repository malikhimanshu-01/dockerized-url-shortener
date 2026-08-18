"""Insert sample links and synthetic click events for local development.

Run once via: docker compose exec backend python seed.py
"""

import random
from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.models import Click, Link

SAMPLE_LINKS = [
    {"short_code": "anthropic", "long_url": "https://www.anthropic.com"},
    {"short_code": "claude", "long_url": "https://www.anthropic.com/claude"},
    {"short_code": "fastapi", "long_url": "https://fastapi.tiangolo.com"},
    {"short_code": "docker", "long_url": "https://www.docker.com"},
    {"short_code": "postgres", "long_url": "https://www.postgresql.org"},
]

REFERRERS = ["https://google.com", "https://twitter.com", None, "https://news.ycombinator.com"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
]


def main():
    db = SessionLocal()
    try:
        if db.query(Link).count() > 0:
            print("links table is not empty — skipping (delete existing rows first to reseed)")
            return

        now = datetime.now(timezone.utc)
        links = []
        for i, sample in enumerate(SAMPLE_LINKS):
            link = Link(
                short_code=sample["short_code"],
                long_url=sample["long_url"],
                created_at=now - timedelta(days=len(SAMPLE_LINKS) - i),
            )
            db.add(link)
            links.append(link)
        db.flush()  # assigns ids without committing yet

        click_count = 0
        for i, link in enumerate(links):
            # Earlier links in the list get more clicks, so "top links" has a real ranking.
            num_clicks = random.randint(3, 20) * (len(links) - i)
            for _ in range(num_clicks):
                clicked_at = now - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))
                db.add(
                    Click(
                        link_id=link.id,
                        clicked_at=clicked_at,
                        referrer=random.choice(REFERRERS),
                        user_agent=random.choice(USER_AGENTS),
                    )
                )
                click_count += 1

        db.commit()
        print(f"seeded {len(links)} links and {click_count} clicks")
    finally:
        db.close()


if __name__ == "__main__":
    main()
