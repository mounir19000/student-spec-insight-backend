import random
from typing import List, Dict, Any

class SpecialtyPredictor:
    def __init__(self):
        self.specialties = ['SIL', 'SIQ', 'SID', 'SIT']
        self.specialty_descriptions = {
            'SIL': 'Systèmes d\'Information et Logiciels',
            'SIQ': 'Systèmes d\'Information et de Qualité',
            'SID': 'Systèmes d\'Information et Données',
            'SIT': 'Systèmes d\'Information et Technologies'
        }
    
    def predict_single(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict specialty for a single student (random assignment for now)"""
        
        # For now, randomly assign specialty
        specialty = random.choice(self.specialties)
        
        # Generate a random confidence score between 0.6 and 0.95
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        return {
            'recommended_specialty': specialty,
            'confidence_score': confidence
        }

# Global predictor instance
predictor = SpecialtyPredictor()

def predict_specialties(students_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Predict specialties for a list of students"""
    
    results = []
    
    for student_data in students_data:
        # Get prediction
        prediction = predictor.predict_single(student_data)
        
        # Add prediction to student data
        student_data.update(prediction)
        results.append(student_data)
    
    return results