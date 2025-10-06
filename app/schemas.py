from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class StudentGrades(BaseModel):
    SYS1: Optional[float] = None
    RES1: Optional[float] = None
    ANUM: Optional[float] = None
    RO: Optional[float] = None
    ORG: Optional[float] = None
    LANG1: Optional[float] = None
    IGL: Optional[float] = None
    THP: Optional[float] = None
    MCSI: Optional[float] = None
    BDD: Optional[float] = None
    SEC: Optional[float] = None
    CPROJ: Optional[float] = None
    PROJ: Optional[float] = None
    LANG2: Optional[float] = None
    ARCH: Optional[float] = None
    SYS2: Optional[float] = None
    RES2: Optional[float] = None

class StudentBase(BaseModel):
    matricule: str
    promo: str
    rang: Optional[int] = None
    rang_s1: Optional[int] = None
    moy_s1: Optional[float] = None
    rang_s2: Optional[int] = None
    moy_s2: Optional[float] = None
    moy_rachat: Optional[float] = None
    recommended_specialty: Optional[str] = None
    confidence_score: Optional[float] = None
    grades: Optional[Dict[str, float]] = None

class Student(StudentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StudentDetail(Student):
    alternative_specialties: Optional[List[Dict[str, Any]]] = None

class PromoBase(BaseModel):
    promo: str
    student_count: int = 0
    status: str = "pending"
    file_name: Optional[str] = None

class Promo(PromoBase):
    id: int
    upload_date: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PaginatedStudents(BaseModel):
    students: List[Student]
    pagination: Dict[str, Any]

class DashboardStats(BaseModel):
    total_students: int
    avg_moy_rachat: float
    specialty_distribution: Dict[str, int]
    top_specialty: Dict[str, Any]
    promo_stats: List[Dict[str, Any]]
    grade_distribution: Dict[str, int]

class StudentWithModuleRank(StudentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    module_rank: int
    module_grade: float

    class Config:
        from_attributes = True

class ModuleInfo(BaseModel):
    module_name: str
    total_students_with_grade: int
    average_grade: float
    highest_grade: float
    lowest_grade: float

class ModuleRankingResponse(BaseModel):
    students: List[StudentWithModuleRank]
    pagination: Dict[str, Any]
    module_info: ModuleInfo

# Analysis schemas
class AnalysisRequest(BaseModel):
    promo: str
    modules: List[str]

class PCARequest(BaseModel):
    promo: str
    modules: List[str]
    n_components: Optional[int] = None

class ClusteringRequest(BaseModel):
    promo: str
    modules: List[str]
    n_clusters: Optional[int] = None
    auto_detect_k: bool = False
    max_k: int = 10

class ElbowRequest(BaseModel):
    promo: str
    modules: List[str]
    max_k: int = 10

class BiplotRequest(BaseModel):
    promo: str
    modules: List[str]
    pc1: int = 1
    pc2: int = 2
    n_clusters: int = 3

class AnalysisResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PCAResponse(AnalysisResponse):
    explained_variance: Optional[List[float]] = None
    cumulative_variance: Optional[List[float]] = None
    loadings: Optional[Dict[str, Dict[str, float]]] = None
    variance_plot: Optional[str] = None
    cumulative_plot: Optional[str] = None

class ClusteringResponse(AnalysisResponse):
    cluster_assignments: Optional[List[Dict[str, Any]]] = None
    cluster_statistics: Optional[Dict[str, Any]] = None
    silhouette_score: Optional[float] = None
    elbow_plot: Optional[str] = None
    optimal_k: Optional[int] = None

class ElbowResponse(AnalysisResponse):
    suggested_k: Optional[int] = None
    elbow_scores: Optional[List[float]] = None
    elbow_plot: Optional[str] = None
    max_k_tested: Optional[int] = None

class BiplotResponse(AnalysisResponse):
    biplot: Optional[str] = None
    pc1: Optional[int] = None
    pc2: Optional[int] = None
    explained_variance_pc1: Optional[float] = None
    explained_variance_pc2: Optional[float] = None

class AvailableModulesResponse(BaseModel):
    success: bool
    modules: List[str]
    promo: str