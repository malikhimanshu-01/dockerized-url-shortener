from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, Text, func
from sqlalchemy.orm import relationship

from app.db import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    short_code = Column(String(16), unique=True, nullable=False, index=True)
    long_url = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    owner_id = Column(Integer, nullable=True)

    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"), nullable=False, index=True)
    clicked_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    referrer = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    country = Column(String(2), nullable=True)

    link = relationship("Link", back_populates="clicks")
