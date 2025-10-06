from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas, auth
from ..database import get_db
from ..utils.data_analyzer import DataAnalyzer
from typing import Optional, List, Dict, Any
import json

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

@router.get("/modules/{promo}", response_model=schemas.AvailableModulesResponse)
async def get_available_modules(
    promo: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available modules for a specific promo
    """
    try:
        # Get a sample student from the promo to extract available modules
        sample_student = db.query(models.Student).filter(
            models.Student.promo == promo
        ).first()
        
        if not sample_student:
            raise HTTPException(status_code=404, detail=f"No students found for promo {promo}")
        
        if sample_student.grades:
            # Extract modules from grades JSON
            modules = list(sample_student.grades.keys())
        else:
            # Fallback to predefined modules
            modules = [
                'SYS1', 'RES1', 'ANUM', 'RO', 'ORG', 'LANG1', 'IGL', 'THP',
                'MCSI', 'BDD', 'SEC', 'CPROJ', 'PROJ', 'LANG2', 'ARCH', 'SYS2', 'RES2'
            ]
        
        return schemas.AvailableModulesResponse(
            success=True,
            modules=modules,
            promo=promo
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pca", response_model=schemas.PCAResponse)
async def perform_pca_analysis(
    request: schemas.PCARequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform PCA analysis on selected modules for a promo
    """
    try:
        # Get students data for the promo
        students = db.query(models.Student).filter(
            models.Student.promo == request.promo
        ).all()
        
        if not students:
            raise HTTPException(status_code=404, detail=f"No students found for promo {request.promo}")
        
        # Convert to list of dictionaries
        students_data = []
        for student in students:
            student_dict = {
                'matricule': student.matricule,
                'promo': student.promo,
                'grades': student.grades or {}
            }
            students_data.append(student_dict)
        
        # Initialize analyzer and load data
        analyzer = DataAnalyzer()
        load_result = analyzer.load_data(students_data, request.modules)
        
        if not load_result['success']:
            raise HTTPException(status_code=400, detail=load_result['error'])
        
        # Perform PCA
        pca_result = analyzer.perform_pca(request.n_components)
        
        if not pca_result['success']:
            raise HTTPException(status_code=500, detail=pca_result['error'])
        
        return schemas.PCAResponse(
            success=True,
            data=pca_result,
            explained_variance=pca_result['explained_variance'],
            cumulative_variance=pca_result['cumulative_variance'],
            loadings=pca_result['loadings'],
            variance_plot=pca_result['variance_plot'],
            cumulative_plot=pca_result['cumulative_plot']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/elbow", response_model=schemas.ElbowResponse)
async def perform_elbow_analysis(
    request: schemas.ElbowRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform elbow method analysis to suggest optimal number of clusters
    """
    try:
        # Get students data for the promo
        students = db.query(models.Student).filter(
            models.Student.promo == request.promo
        ).all()
        
        if not students:
            raise HTTPException(status_code=404, detail=f"No students found for promo {request.promo}")
        
        # Convert to list of dictionaries
        students_data = []
        for student in students:
            student_dict = {
                'matricule': student.matricule,
                'promo': student.promo,
                'grades': student.grades or {}
            }
            students_data.append(student_dict)
        
        # Initialize analyzer and load data
        analyzer = DataAnalyzer()
        load_result = analyzer.load_data(students_data, request.modules)
        
        if not load_result['success']:
            raise HTTPException(status_code=400, detail=load_result['error'])
        
        # Perform PCA first (required for clustering)
        pca_result = analyzer.perform_pca()
        if not pca_result['success']:
            raise HTTPException(status_code=500, detail=pca_result['error'])
        
        # Perform elbow method analysis
        elbow_result = analyzer.find_optimal_clusters(request.max_k)
        
        if not elbow_result['success']:
            raise HTTPException(status_code=500, detail=elbow_result['error'])
        
        return schemas.ElbowResponse(
            success=True,
            suggested_k=elbow_result.get('optimal_k'),
            elbow_scores=elbow_result.get('elbow_scores', []),
            elbow_plot=elbow_result.get('elbow_plot'),
            max_k_tested=request.max_k
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clustering", response_model=schemas.ClusteringResponse)
async def perform_clustering_analysis(
    request: schemas.ClusteringRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform clustering analysis with optional auto k-detection
    """
    try:
        # Get students data for the promo
        students = db.query(models.Student).filter(
            models.Student.promo == request.promo
        ).all()
        
        if not students:
            raise HTTPException(status_code=404, detail=f"No students found for promo {request.promo}")
        
        # Convert to list of dictionaries
        students_data = []
        for student in students:
            student_dict = {
                'matricule': student.matricule,
                'promo': student.promo,
                'grades': student.grades or {}
            }
            students_data.append(student_dict)
        
        # Initialize analyzer and load data
        analyzer = DataAnalyzer()
        load_result = analyzer.load_data(students_data, request.modules)
        
        if not load_result['success']:
            raise HTTPException(status_code=400, detail=load_result['error'])
        
        # Perform PCA first (required for clustering)
        pca_result = analyzer.perform_pca()
        if not pca_result['success']:
            raise HTTPException(status_code=500, detail=pca_result['error'])
        
        # Find optimal clusters if requested
        optimal_k_result = None
        n_clusters = request.n_clusters
        
        if request.auto_detect_k or request.n_clusters is None:
            optimal_k_result = analyzer.find_optimal_clusters(request.max_k)
            if optimal_k_result['success']:
                n_clusters = optimal_k_result['optimal_k']
            else:
                n_clusters = 3  # Default fallback
        
        # Perform clustering
        clustering_result = analyzer.perform_clustering(n_clusters)
        
        if not clustering_result['success']:
            raise HTTPException(status_code=500, detail=clustering_result['error'])
        
        response_data = clustering_result.copy()
        if optimal_k_result:
            response_data.update({
                'elbow_plot': optimal_k_result.get('elbow_plot'),
                'optimal_k': optimal_k_result.get('optimal_k')
            })
        
        return schemas.ClusteringResponse(
            success=True,
            data=response_data,
            cluster_assignments=clustering_result['cluster_assignments'],
            cluster_statistics=clustering_result['cluster_statistics'],
            silhouette_score=clustering_result['silhouette_score'],
            elbow_plot=optimal_k_result.get('elbow_plot') if optimal_k_result else None,
            optimal_k=optimal_k_result.get('optimal_k') if optimal_k_result else n_clusters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/biplot", response_model=schemas.BiplotResponse)
async def create_biplot(
    request: schemas.BiplotRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create biplot visualization for selected principal components
    """
    try:
        # Get students data for the promo
        students = db.query(models.Student).filter(
            models.Student.promo == request.promo
        ).all()
        
        if not students:
            raise HTTPException(status_code=404, detail=f"No students found for promo {request.promo}")
        
        # Convert to list of dictionaries
        students_data = []
        for student in students:
            student_dict = {
                'matricule': student.matricule,
                'promo': student.promo,
                'grades': student.grades or {}
            }
            students_data.append(student_dict)
        
        # Initialize analyzer and perform complete analysis
        analyzer = DataAnalyzer()
        load_result = analyzer.load_data(students_data, request.modules)
        
        if not load_result['success']:
            raise HTTPException(status_code=400, detail=load_result['error'])
        
        # Perform PCA
        pca_result = analyzer.perform_pca()
        if not pca_result['success']:
            raise HTTPException(status_code=500, detail=pca_result['error'])
        
        # Perform clustering (required for biplot)
        clustering_result = analyzer.perform_clustering(request.n_clusters)
        if not clustering_result['success']:
            raise HTTPException(status_code=500, detail=clustering_result['error'])
        
        # Create biplot
        biplot_result = analyzer.create_biplot(request.pc1, request.pc2)
        
        if not biplot_result['success']:
            raise HTTPException(status_code=500, detail=biplot_result['error'])
        
        return schemas.BiplotResponse(
            success=True,
            data=biplot_result,
            biplot=biplot_result['biplot'],
            pc1=biplot_result['pc1'],
            pc2=biplot_result['pc2'],
            explained_variance_pc1=biplot_result['explained_variance_pc1'],
            explained_variance_pc2=biplot_result['explained_variance_pc2']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete-analysis", response_model=schemas.AnalysisResponse)
async def perform_complete_analysis(
    request: schemas.AnalysisRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform complete analysis workflow: PCA + Clustering + Results
    """
    try:
        # Get students data for the promo
        students = db.query(models.Student).filter(
            models.Student.promo == request.promo
        ).all()
        
        if not students:
            raise HTTPException(status_code=404, detail=f"No students found for promo {request.promo}")
        
        # Convert to list of dictionaries
        students_data = []
        for student in students:
            student_dict = {
                'matricule': student.matricule,
                'promo': student.promo,
                'grades': student.grades or {}
            }
            students_data.append(student_dict)
        
        # Initialize analyzer and perform complete workflow
        analyzer = DataAnalyzer()
        
        # Load data
        load_result = analyzer.load_data(students_data, request.modules)
        if not load_result['success']:
            raise HTTPException(status_code=400, detail=load_result['error'])
        
        # Perform PCA
        pca_result = analyzer.perform_pca()
        if not pca_result['success']:
            raise HTTPException(status_code=500, detail=pca_result['error'])
        
        # Find optimal clusters
        optimal_k_result = analyzer.find_optimal_clusters()
        if not optimal_k_result['success']:
            raise HTTPException(status_code=500, detail=optimal_k_result['error'])
        
        # Perform clustering with optimal k
        clustering_result = analyzer.perform_clustering(optimal_k_result['optimal_k'])
        if not clustering_result['success']:
            raise HTTPException(status_code=500, detail=clustering_result['error'])
        
        # Export all results
        export_result = analyzer.export_analysis_results()
        if not export_result['success']:
            raise HTTPException(status_code=500, detail=export_result['error'])
        
        # Combine all results
        complete_results = {
            'load_info': load_result,
            'pca_analysis': pca_result,
            'optimal_k_analysis': optimal_k_result,
            'clustering_analysis': clustering_result,
            'export_data': export_result['results']
        }
        
        return schemas.AnalysisResponse(
            success=True,
            message="Complete analysis performed successfully",
            data=complete_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{promo}")
async def export_analysis_data(
    promo: str,
    modules: str = Query(..., description="Comma-separated list of modules"),
    format: str = Query("json", description="Export format: json or csv"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export analysis results in various formats
    """
    try:
        module_list = [mod.strip() for mod in modules.split(',')]
        
        # Get students data for the promo
        students = db.query(models.Student).filter(
            models.Student.promo == promo
        ).all()
        
        if not students:
            raise HTTPException(status_code=404, detail=f"No students found for promo {promo}")
        
        # Convert to list of dictionaries
        students_data = []
        for student in students:
            student_dict = {
                'matricule': student.matricule,
                'promo': student.promo,
                'grades': student.grades or {}
            }
            students_data.append(student_dict)
        
        # Perform complete analysis
        analyzer = DataAnalyzer()
        load_result = analyzer.load_data(students_data, module_list)
        if not load_result['success']:
            raise HTTPException(status_code=400, detail=load_result['error'])
        
        pca_result = analyzer.perform_pca()
        if not pca_result['success']:
            raise HTTPException(status_code=500, detail=pca_result['error'])
        
        optimal_k_result = analyzer.find_optimal_clusters()
        if not optimal_k_result['success']:
            raise HTTPException(status_code=500, detail=optimal_k_result['error'])
        
        clustering_result = analyzer.perform_clustering(optimal_k_result['optimal_k'])
        if not clustering_result['success']:
            raise HTTPException(status_code=500, detail=clustering_result['error'])
        
        export_result = analyzer.export_analysis_results()
        if not export_result['success']:
            raise HTTPException(status_code=500, detail=export_result['error'])
        
        if format.lower() == 'json':
            return export_result['results']
        else:
            # For CSV format, return a simplified version
            import pandas as pd
            from fastapi.responses import StreamingResponse
            import io
            
            # Create CSV with cluster assignments
            df = pd.DataFrame(clustering_result['cluster_assignments'])
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analysis_{promo}.csv"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))