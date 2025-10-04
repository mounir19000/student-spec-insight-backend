from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, JSON, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Promo(Base):
    __tablename__ = "promos"

    id = Column(Integer, primary_key=True, index=True)
    promo = Column(String(10), unique=True, index=True, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    student_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    file_name = Column(String(255))
    processed_at = Column(DateTime(timezone=True))

    students = relationship("Student", back_populates="promo_rel", cascade="all, delete-orphan")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    matricule = Column(String(20), unique=True, index=True, nullable=False)
    promo = Column(String(10), ForeignKey("promos.promo"), nullable=False)
    rang = Column(Integer)
    rang_s1 = Column(Integer)
    moy_s1 = Column(DECIMAL(5, 2))
    rang_s2 = Column(Integer)
    moy_s2 = Column(DECIMAL(5, 2))
    moy_rachat = Column(DECIMAL(5, 2))
    recommended_specialty = Column(String(10))
    confidence_score = Column(DECIMAL(5, 2))
    grades = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    promo_rel = relationship("Promo", back_populates="students")