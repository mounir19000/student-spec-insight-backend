import pandas as pd
from fastapi import UploadFile, HTTPException
import io
from typing import List, Dict, Any, Optional

async def process_student_file(file: UploadFile, promo: str) -> List[Dict[str, Any]]:
    """Process uploaded CSV/Excel file and return student data with provided promo"""
    
    # Read file content
    content = await file.read()
    
    try:
        # Try different encodings for CSV files
        if file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.StringIO(content.decode('latin-1')))
                except UnicodeDecodeError:
                    df = pd.read_csv(io.StringIO(content.decode('cp1252')))
        else:
            # Read as Excel
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de lecture du fichier: {str(e)}")
    
    # Validate required columns (Note: Promo and Affectation are NO LONGER required)
    required_columns = [
        "Matricule", "SYS1", "RES1", "ANUM", "RO", "ORG", "LANG1", "IGL", "THP",
        "Rang S1", "Moy S1", "MCSI", "BDD", "SEC", "CPROJ", "PROJ", "LANG2",
        "ARCH", "SYS2", "RES2", "Rang S2", "Moy S2", "Rang", "Moy Rachat"
    ]

    # Clean column names (remove extra spaces)
    df.columns = df.columns.str.strip()
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        available_columns = list(df.columns)
        raise HTTPException(
            status_code=400,
            detail=f"Colonnes manquantes: {', '.join(missing_columns)}. Colonnes disponibles: {', '.join(available_columns)}"
        )

    # Clean the dataframe
    df = df.dropna(subset=['Matricule'])  # Remove rows without matricule
    
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Le fichier ne contient aucune donnée valide"
        )
    
    # Convert to list of dictionaries
    students_data = []
    
    for index, row in df.iterrows():
        try:
            # Extract individual subject grades for the grades JSON field
            grade_columns = ['SYS1', 'RES1', 'ANUM', 'RO', 'ORG', 'LANG1', 'IGL', 'THP', 
                            'MCSI', 'BDD', 'SEC', 'CPROJ', 'PROJ', 'LANG2', 'ARCH', 'SYS2', 'RES2']
            
            grades = {}
            for col in grade_columns:
                if col in row and pd.notna(row[col]):
                    grades[col] = _safe_float(row[col])
            
            student_data = {
                'matricule': str(row['Matricule']).strip(),
                'promo': promo,  # Use the promo provided as parameter
                'rang': _safe_int(row['Rang']),
                'rang_s1': _safe_int(row['Rang S1']),
                'moy_s1': _safe_float(row['Moy S1']),
                'rang_s2': _safe_int(row['Rang S2']),
                'moy_s2': _safe_float(row['Moy S2']),
                'moy_rachat': _safe_float(row['Moy Rachat']),
                'grades': grades
            }
            
            students_data.append(student_data)
            
        except Exception as e:
            # Log the error but continue processing other students
            print(f"Error processing row {index + 2}: {str(e)}")
            continue
    
    return students_data


def _safe_float(value) -> Optional[float]:
    """Safely convert value to float, return None if conversion fails."""
    if pd.isna(value) or value == '' or value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> Optional[int]:
    """Safely convert value to int, return None if conversion fails."""
    if pd.isna(value) or value == '' or value is None:
        return None
    try:
        return int(float(value))  # Convert to float first to handle decimal strings
    except (ValueError, TypeError):
        return None