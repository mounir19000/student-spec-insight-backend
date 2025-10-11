from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db
from .routers import auth, students, upload, dashboard, promos, export, analysis
from datetime import datetime

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Spec Insight API",
    description="Backend API for Student Specialty Recommendation System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(promos.router, prefix="/api/promos", tags=["Promos"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])

@app.get("/api/health")
async def health_check():
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "healthy",
            "mlModel": "healthy",
            "fileStorage": "healthy"
        }
    }

@app.get("/")
async def root():
    return {"message": "Student Spec Insight API is running"}

# Initialize default admin user
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    try:
        # Check if admin user exists
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            # Create default admin user
            from .auth import get_password_hash
            hashed_password = get_password_hash("admin")
            admin_user = models.User(
                username="admin",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("Default admin user created (username: admin, password: admin)")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()