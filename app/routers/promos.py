from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

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
async def get_promos(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    promos = db.query(models.Promo).all()
    
    promo_data = [
        {
            "promo": promo.promo,
            "studentCount": promo.student_count,
            "uploadDate": promo.upload_date.isoformat(),
            "lastProcessed": promo.processed_at.isoformat() if promo.processed_at else None,
            "status": promo.status
        }
        for promo in promos
    ]
    
    return {
        "success": True,
        "data": promo_data
    }

@router.delete("/{promo}")
async def delete_promo(
    promo: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the promo
    db_promo = db.query(models.Promo).filter(models.Promo.promo == promo).first()
    
    if not db_promo:
        raise HTTPException(status_code=404, detail="Promo non trouvée")
    
    # Count students before deletion
    student_count = db.query(models.Student).filter(models.Student.promo == promo).count()
    
    # Delete the promo (students will be deleted automatically due to cascade)
    db.delete(db_promo)
    db.commit()
    
    return {
        "success": True,
        "message": "Promo supprimée avec succès",
        "data": {
            "deletedStudents": student_count,
            "promo": promo
        }
    }