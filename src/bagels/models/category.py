from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, Float, Integer, String, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from .database.db import Base


class Nature(Enum):
    WANT = "Want"
    NEED = "Need"
    MUST = "Must"

    def __str__(self):
        return self.value


class Category(Base):
    __tablename__ = "category"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    id = Column(Integer, primary_key=True, index=True)
    parentCategoryId = Column(Integer, ForeignKey("category.id"), nullable=True)
    name = Column(String, nullable=False)
    nature = Column(SQLEnum(Nature), nullable=False)
    color = Column(String, nullable=False)
    monthlyBudget = Column(Float, nullable=True)

    records = relationship("Record", back_populates="category")
    parentCategory = relationship(
        "Category", back_populates="subCategories", remote_side=[id]
    )
    subCategories = relationship(
        "Category", back_populates="parentCategory", remote_side=[parentCategoryId]
    )
