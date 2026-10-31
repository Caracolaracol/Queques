from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from .database.db import Base


class WishlistItem(Base):
    """A single wishlist item (e.g. something you want to buy/do)."""

    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item = Column(String, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    done = Column(Boolean, nullable=False, default=False)
    # Manual priority order: rows created before this column existed have NULL
    # and get backfilled by id (see managers/wishlist.py). New rows always get
    # an explicit position on insert.
    position = Column(Integer, nullable=True)
