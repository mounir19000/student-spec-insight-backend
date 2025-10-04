from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas, auth
from ..database import get_db
from typing import Optional, List

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

@router.get("/stats")
async def get_dashboard_stats(
    promos: Optional[str] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Build base query
    query = db.query(models.Student)
    
    # Filter by promos if provided
    if promos:
        promo_list = promos.split(',')
        query = query.filter(models.Student.promo.in_(promo_list))
    
    # Get total students
    total_students = query.count()
    
    # Get average moy_rachat
    avg_moy_rachat = db.query(func.avg(models.Student.moy_rachat)).scalar() or 0
    
    # Get specialty distribution
    specialty_counts = db.query(
        models.Student.recommended_specialty,
        func.count(models.Student.id)
    ).group_by(models.Student.recommended_specialty).all()
    
    specialty_distribution = {specialty: count for specialty, count in specialty_counts}
    
    # Get top specialty
    top_specialty = max(specialty_distribution.items(), key=lambda x: x[1]) if specialty_distribution else ("N/A", 0)
    top_specialty_data = {
        "name": top_specialty[0],
        "count": top_specialty[1],
        "percentage": round((top_specialty[1] / total_students * 100) if total_students > 0 else 0, 1)
    }
    
    # Get promo stats
    promo_stats = db.query(
        models.Promo.promo,
        models.Promo.student_count,
        models.Promo.upload_date
    ).all()
    
    promo_stats_data = [
        {
            "promo": promo.promo,
            "studentCount": promo.student_count,
            "avgGrade": 14.5,  # Mock data for now
            "uploadDate": promo.upload_date.isoformat()
        }
        for promo in promo_stats
    ]
    
    # Get grade distribution (mock data for now)
    grade_distribution = {
        "excellent": int(total_students * 0.2),
        "good": int(total_students * 0.4),
        "average": int(total_students * 0.3),
        "poor": int(total_students * 0.1)
    }
    
    return {
        "success": True,
        "data": {
            "total_students": total_students,
            "avg_moy_rachat": round(float(avg_moy_rachat), 2),
            "specialty_distribution": specialty_distribution,
            "top_specialty": top_specialty_data,
            "promo_stats": promo_stats_data,
            "grade_distribution": grade_distribution
        }
    }

@router.get("/specialty-analysis")
async def get_specialty_analysis(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Mock specialty analysis data for now
    specialties_data = [
        {
            "name": "SIL",
            "studentCount": db.query(models.Student).filter(models.Student.recommended_specialty == "SIL").count(),
            "avgGrade": 14.8,
            "topModules": ["IGL", "PROJ", "LANG1"],
            "demandTrend": "increasing"
        },
        {
            "name": "SIQ",
            "studentCount": db.query(models.Student).filter(models.Student.recommended_specialty == "SIQ").count(),
            "avgGrade": 14.5,
            "topModules": ["ORG", "THP", "MCSI"],
            "demandTrend": "stable"
        },
        {
            "name": "SID",
            "studentCount": db.query(models.Student).filter(models.Student.recommended_specialty == "SID").count(),
            "avgGrade": 15.2,
            "topModules": ["BDD", "SEC", "MCSI"],
            "demandTrend": "increasing"
        },
        {
            "name": "SIT",
            "studentCount": db.query(models.Student).filter(models.Student.recommended_specialty == "SIT").count(),
            "avgGrade": 14.9,
            "topModules": ["SYS1", "SYS2", "RES1"],
            "demandTrend": "stable"
        }
    ]
    
    module_correlations = {
        "SIQ": ["BDD", "PROJ", "ARCH"],
        "SIL": ["IGL", "LANG1", "PROJ"],
        "SID": ["SEC", "RES1", "RES2"],
        "SIT": ["SYS1", "SYS2", "RES1"]
    }
    
    return {
        "success": True,
        "data": {
            "specialties": specialties_data,
            "moduleCorrelations": module_correlations
        }
    }