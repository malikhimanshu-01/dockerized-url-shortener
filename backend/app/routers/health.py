from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import cache
from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    await cache.redis_client.ping()
    return {"status": "ok", "postgres": "ok", "redis": "ok"}
