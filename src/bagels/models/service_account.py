from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from .database.db import Base


class ServiceAccount(Base):
    """A customer/account number for an external service provider."""

    __tablename__ = "service_account"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    accountNumber = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)
