from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/top-links", response_model=List[schemas.TopLinkOut])
def top_links(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Link.short_code,
            models.Link.long_url,
            func.count(models.Click.id).label("click_count"),
        )
        .outerjoin(models.Click, models.Click.link_id == models.Link.id)
        .group_by(models.Link.id)
        .order_by(func.count(models.Click.id).desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.TopLinkOut(short_code=r.short_code, long_url=r.long_url, click_count=r.click_count)
        for r in rows
    ]


@router.get("/clicks-over-time", response_model=List[schemas.ClicksOverTimePoint])
def clicks_over_time(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    day_expr = func.date_trunc("day", models.Click.clicked_at).label("day")

    rows = (
        db.query(day_expr, func.count(models.Click.id).label("count"))
        .filter(models.Click.clicked_at >= cutoff)
        .group_by(day_expr)
        .order_by(day_expr)
        .all()
    )
    return [schemas.ClicksOverTimePoint(date=r.day.date(), count=r.count) for r in rows]
