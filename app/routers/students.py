from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
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

@router.get("/rank-by-module")
async def get_students_rank_by_module(
    module: str = Query(..., description="Module name (e.g., 'SYS1', 'BDD', 'MCSI')"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    promo: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get students ranked by their grade in a specific module.
    """
    # Build base query - only include students who have a grade for the module
    query = db.query(models.Student).filter(
        func.json_extract(models.Student.grades, f'$.{module}').isnot(None),
        func.json_extract(models.Student.grades, f'$.{module}') != '',
        func.json_extract(models.Student.grades, f'$.{module}') != 'null'
    )
    
    # Apply filters
    if search:
        query = query.filter(models.Student.matricule.contains(search))
    if specialty:
        query = query.filter(models.Student.recommended_specialty == specialty)
    if promo:
        query = query.filter(models.Student.promo == promo)
    
    # Get all students for ranking calculation
    all_students = query.all()
    
    if not all_students:
        return {
            "success": True,
            "data": {
                "students": [],
                "pagination": {
                    "currentPage": page,
                    "totalPages": 0,
                    "totalStudents": 0,
                    "hasNextPage": False,
                    "hasPrevPage": False
                },
                "module_info": {
                    "module_name": module,
                    "total_students_with_grade": 0,
                    "average_grade": 0.0,
                    "highest_grade": 0.0,
                    "lowest_grade": 0.0
                }
            }
        }
    
    # Extract module grades and calculate rankings
    students_with_grades = []
    module_grades = []
    
    for student in all_students:
        if student.grades and module in student.grades and student.grades[module] is not None:
            try:
                grade = float(student.grades[module])
                module_grades.append(grade)
                students_with_grades.append({
                    'student': student,
                    'module_grade': grade
                })
            except (ValueError, TypeError):
                continue
    
    if not students_with_grades:
        return {
            "success": True,
            "data": {
                "students": [],
                "pagination": {
                    "currentPage": page,
                    "totalPages": 0,
                    "totalStudents": 0,
                    "hasNextPage": False,
                    "hasPrevPage": False
                },
                "module_info": {
                    "module_name": module,
                    "total_students_with_grade": 0,
                    "average_grade": 0.0,
                    "highest_grade": 0.0,
                    "lowest_grade": 0.0
                }
            }
        }
    
    # Sort by module grade (descending - highest grade gets rank 1)
    students_with_grades.sort(key=lambda x: x['module_grade'], reverse=True)
    
    # Calculate ranks (handle ties)
    ranked_students = []
    current_rank = 1
    for i, item in enumerate(students_with_grades):
        if i > 0 and item['module_grade'] < students_with_grades[i-1]['module_grade']:
            current_rank = i + 1
        
        student = item['student']
        ranked_students.append({
            'id': student.id,
            'matricule': student.matricule,
            'promo': student.promo,
            'rang': student.rang,
            'moy_rachat': float(student.moy_rachat) if student.moy_rachat else None,
            'recommended_specialty': student.recommended_specialty,
            'rang_s1': student.rang_s1,
            'moy_s1': float(student.moy_s1) if student.moy_s1 else None,
            'rang_s2': student.rang_s2,
            'moy_s2': float(student.moy_s2) if student.moy_s2 else None,
            'grades': student.grades,
            'module_rank': current_rank,
            'module_grade': item['module_grade'],
            'created_at': student.created_at,
            'updated_at': student.updated_at
        })
    
    # Calculate module statistics
    average_grade = sum(module_grades) / len(module_grades)
    highest_grade = max(module_grades)
    lowest_grade = min(module_grades)
    
    # Apply pagination
    total_students = len(ranked_students)
    total_pages = math.ceil(total_students / limit)
    offset = (page - 1) * limit
    paginated_students = ranked_students[offset:offset + limit]
    
    return {
        "success": True,
        "data": {
            "students": paginated_students,
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalStudents": total_students,
                "hasNextPage": page < total_pages,
                "hasPrevPage": page > 1
            },
            "module_info": {
                "module_name": module,
                "total_students_with_grade": len(students_with_grades),
                "average_grade": round(average_grade, 2),
                "highest_grade": highest_grade,
                "lowest_grade": lowest_grade
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