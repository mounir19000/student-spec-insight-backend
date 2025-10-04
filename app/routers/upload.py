from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db
from ..utils.file_processor import process_student_file
from ..utils.specialty_predictor import predict_specialties
import os
import pandas as pd
import io
from typing import Optional
import logging
from datetime import datetime

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    token_data = auth.verify_token(credentials.credentials, credentials_exception)
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/student-data")
async def upload_student_data(
    file: UploadFile = File(...),
    promo: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload student data from CSV/Excel file with promotion information.
    
    Args:
        file: CSV/Excel file containing student data
        promo: Promotion year for all students in the file
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Success message with count of imported students
    """
    
    # Validate file type
    allowed_content_types = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/csv'
    ]
    
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail="Format de fichier non supporté. Veuillez utiliser CSV, XLS ou XLSX"
        )

    # Validate promo
    if not promo or not promo.strip():
        raise HTTPException(
            status_code=400,
            detail="La promotion est obligatoire"
        )

    try:
        # Process the uploaded file with the provided promo
        students_data = await process_student_file(file, promo.strip())
        
        if not students_data:
            raise HTTPException(status_code=400, detail="Aucune donnée valide trouvée dans le fichier")
        
        promo_cleaned = promo.strip()
        
        # Create or update promo
        db_promo = db.query(models.Promo).filter(models.Promo.promo == promo_cleaned).first()
        if not db_promo:
            db_promo = models.Promo(
                promo=promo_cleaned,
                file_name=file.filename,
                student_count=len(students_data)
            )
            db.add(db_promo)
        else:
            # Delete existing students for this promo
            db.query(models.Student).filter(models.Student.promo == promo_cleaned).delete()
            db_promo.student_count = len(students_data)
            db_promo.file_name = file.filename
        
        # Generate specialty recommendations
        students_with_predictions = predict_specialties(students_data)
        
        # Save students to database
        processed_students = 0
        errors = []
        
        for student_data in students_with_predictions:
            try:
                db_student = models.Student(**student_data)
                db.add(db_student)
                processed_students += 1
            except Exception as e:
                error_msg = f"Erreur pour l'étudiant {student_data.get('matricule', 'N/A')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        # Update promo status
        db_promo.status = "processed"
        db_promo.processed_at = datetime.utcnow()
        
        db.commit()
        
        # Prepare response message
        message = f"Données de {processed_students} étudiants importées avec succès pour la promotion {promo_cleaned}"
        
        if errors:
            message += f". {len(errors)} erreurs rencontrées."
            logger.warning(f"Upload completed with {len(errors)} errors")

        return {
            "success": True,
            "message": message,
            "data": {
                "processedStudents": processed_students,
                "promo": promo_cleaned,
                "uploadDate": datetime.utcnow().isoformat(),
                "fileName": file.filename,
                "errorCount": len(errors),
                "errors": errors[:10] if errors else []  # Return first 10 errors
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}"
        )