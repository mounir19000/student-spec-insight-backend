from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas, auth
from ..database import get_db
from typing import Optional, List
import math

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    token_data = auth.verify_token(credentials.credentials, credentials_exception)
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/")
async def get_students(
    search: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    promo: Optional[str] = Query(None),
    sortBy: Optional[str] = Query("rang"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(models.Student)
    
    # Apply filters
    if search:
        query = query.filter(models.Student.matricule.contains(search))
    if specialty:
        query = query.filter(models.Student.recommended_specialty == specialty)
    if promo:
        query = query.filter(models.Student.promo == promo)
    
    # Apply sorting
    if sortBy == "rang":
        query = query.order_by(models.Student.rang.asc())
    elif sortBy == "moyRachat":
        query = query.order_by(models.Student.moy_rachat.desc())
    
    # Get total count
    total_students = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    students = query.offset(offset).limit(limit).all()
    
    # Calculate pagination info
    total_pages = math.ceil(total_students / limit)
    
    return {
        "success": True,
        "data": {
            "students": students,
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalStudents": total_students,
                "hasNextPage": page < total_pages,
                "hasPrevPage": page > 1
            }
        }
    }

@router.get("/{matricule}")
async def get_student_detail(
    matricule: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # URL decode the matricule to handle encoded slashes
    from urllib.parse import unquote
    decoded_matricule = unquote(unquote(matricule))  # Double decode to handle double encoding
    
    student = db.query(models.Student).filter(models.Student.matricule == decoded_matricule).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Add some mock alternative specialties for the detail view
    alternative_specialties = [
        {"specialty": "SIL", "score": 0.75},
        {"specialty": "SID", "score": 0.68},
        {"specialty": "SIT", "score": 0.62}
    ]
    
    student_dict = {
        "id": student.id,
        "matricule": student.matricule,
        "promo": student.promo,
        "rang": student.rang,
        "rang_s1": student.rang_s1,
        "moy_s1": float(student.moy_s1) if student.moy_s1 else None,
        "rang_s2": student.rang_s2,
        "moy_s2": float(student.moy_s2) if student.moy_s2 else None,
        "moy_rachat": float(student.moy_rachat) if student.moy_rachat else None,
        "recommended_specialty": student.recommended_specialty,
        "confidence_score": float(student.confidence_score) if student.confidence_score else None,
        "grades": student.grades,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "alternative_specialties": alternative_specialties
    }
    
    return {
        "success": True,
        "data": student_dict
    }