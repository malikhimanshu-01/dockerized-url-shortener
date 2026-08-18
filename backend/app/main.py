import logging

from fastapi import FastAPI

from app.routers import analytics, health, links

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="URL Shortener API", version="0.1.0")

app.include_router(health.router)
app.include_router(links.router)
app.include_router(links.redirect_router)
app.include_router(analytics.router)
