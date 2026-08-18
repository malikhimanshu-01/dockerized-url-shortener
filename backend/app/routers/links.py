import logging
import secrets
import string

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import cache, models, schemas
from app.config import settings
from app.db import SessionLocal, get_db

logger = logging.getLogger("app.links")

router = APIRouter(prefix="/api/links", tags=["links"])
redirect_router = APIRouter(tags=["redirect"])

_ALPHABET = string.ascii_letters + string.digits


def _generate_short_code(length: int = 7) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def _client_ip(request: Request) -> str:
    # Behind the proxy, request.client.host is always the nginx container's address —
    # trust X-Forwarded-For instead, which nginx sets and which is the only path to this
    # service now that backend no longer publishes a host port.
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit_create(request: Request):
    client_ip = _client_ip(request)
    allowed = await cache.check_rate_limit(
        f"create:{client_ip}", settings.rate_limit_max, settings.rate_limit_window_seconds
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="rate limit exceeded, try again later")


@router.post(
    "",
    response_model=schemas.LinkOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_create)],
)
def create_link(payload: schemas.LinkCreate, db: Session = Depends(get_db)):
    short_code = payload.short_code or _generate_short_code()

    if payload.short_code:
        existing = db.query(models.Link).filter(models.Link.short_code == short_code).first()
        if existing:
            raise HTTPException(status_code=409, detail="short_code already in use")

    link = models.Link(short_code=short_code, long_url=payload.long_url, expires_at=payload.expires_at)
    db.add(link)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="short_code already in use")
    db.refresh(link)
    return link


@router.get("", response_model=list[schemas.LinkOut])
def list_links(db: Session = Depends(get_db)):
    return db.query(models.Link).order_by(models.Link.created_at.desc()).all()


@router.get("/{short_code}", response_model=schemas.LinkOut)
def get_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")
    return link


@router.put("/{short_code}", response_model=schemas.LinkOut)
async def update_link(short_code: str, payload: schemas.LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")

    if payload.long_url is not None:
        link.long_url = payload.long_url
    if payload.expires_at is not None:
        link.expires_at = payload.expires_at

    db.commit()
    db.refresh(link)
    await cache.invalidate_cached_url(short_code)
    return link


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")
    db.delete(link)
    db.commit()
    await cache.invalidate_cached_url(short_code)
    return None


def _record_click(short_code: str, referrer: str | None, user_agent: str | None) -> None:
    """Runs as a FastAPI background task, after the redirect response is sent."""
    db = SessionLocal()
    try:
        db.execute(
            text(
                "INSERT INTO clicks (link_id, referrer, user_agent) "
                "SELECT id, :referrer, :user_agent FROM links WHERE short_code = :short_code"
            ),
            {"short_code": short_code, "referrer": referrer, "user_agent": user_agent},
        )
        db.commit()
    finally:
        db.close()


@redirect_router.get("/{short_code}")
async def redirect_to_long_url(
    short_code: str, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    long_url = await cache.get_cached_long_url(short_code)
    if long_url is not None:
        logger.info("cache HIT short_code=%s", short_code)
    else:
        logger.info("cache MISS short_code=%s", short_code)
        link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
        if not link:
            raise HTTPException(status_code=404, detail="link not found")
        long_url = link.long_url
        await cache.cache_long_url(short_code, long_url)

    background_tasks.add_task(
        _record_click, short_code, request.headers.get("referer"), request.headers.get("user-agent")
    )
    return RedirectResponse(url=long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
