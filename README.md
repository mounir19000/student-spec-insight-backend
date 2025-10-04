# Student Specialty Predictor 🎓

A FastAPI-based system for analyzing student academic data and providing optimal
specialty recommendations.

## 📋 Overview

This application helps educational institutions analyze student performance data
and provide intelligent specialty recommendations based on academic grades,
rankings, and historical patterns. The system processes student data from
CSV/Excel files and generates insights to guide students toward their most
suitable academic specializations.

## ✨ Features

- **📊 Student Data Upload**: Import student academic data from CSV/Excel files
- **🎯 Specialty Recommendations**: Intelligent specialty recommendations
- **📈 Performance Analysis**: Comprehensive analysis of student grades and
  rankings
- **👥 Promotion Management**: Organize students by academic promotion/year
- **🔐 Secure Authentication**: JWT-based user authentication system
- **📱 RESTful API**: Clean and documented REST API endpoints
- **💾 Data Export**: Export analysis results and student data

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with passlib
- **Data Processing**: Pandas, NumPy
- **File Processing**: Support for CSV, XLS, XLSX formats
- **API Documentation**: Automatic OpenAPI/Swagger documentation

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── auth.py              # Authentication utilities
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── dashboard.py     # Dashboard analytics
│   │   ├── export.py        # Data export endpoints
│   │   ├── promos.py        # Promotion management
│   │   ├── students.py      # Student data endpoints
│   │   └── upload.py        # File upload endpoints
│   └── utils/               # Utility modules
│       ├── file_processor.py    # File processing logic
│       └── specialty_predictor.py # Recommendation engine
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/student-specialty-predictor.git
   cd student-specialty-predictor
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once the application is running, you can access:

- **Interactive API Documentation**: `http://localhost:8000/docs`
- **Alternative API Documentation**: `http://localhost:8000/redoc`

## 🔧 Configuration

Create a `.env` file in the root directory with the following variables:

```env
DATABASE_URL=sqlite:///./student_spec_insight.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## 📊 Data Format

The system expects student data files with the following columns:

```
Matricule, SYS1, RES1, ANUM, RO, ORG, LANG1, IGL, THP, Rang S1, Moy S1,
MCSI, BDD, SEC, CPROJ, PROJ, LANG2, ARCH, SYS2, RES2, Rang S2, Moy S2,
Rang, Moy Rachat
```

### Usage Example

1. **Upload student data**:

   ```bash
   POST /api/upload/student-data
   Content-Type: multipart/form-data

   FormData:
   - file: [CSV/Excel file]
   - promo: "2024"
   ```

2. **Get specialty recommendations**:
   ```bash
   GET /api/students/{student_id}/recommendations
   ```

## 🎯 Recommendation Features

The specialty recommendation engine analyzes:

- **Academic Performance**: Individual subject grades and overall averages
- **Ranking Patterns**: Class rankings across semesters
- **Subject Affinity**: Performance patterns in specific subject areas
- **Historical Data**: Trends from previous student cohorts

## 🔒 Security

- JWT-based authentication for all API endpoints
- Secure password hashing with bcrypt
- Input validation and sanitization
- SQL injection protection through SQLAlchemy ORM

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## 📄 API Endpoints

### Authentication

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Student Management

- `POST /api/upload/student-data` - Upload student data
- `GET /api/students` - List students
- `GET /api/students/{id}` - Get student details
- `GET /api/students/{id}/recommendations` - Get specialty recommendations

### Analytics

- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/promos` - List promotions
- `GET /api/promos/{promo}/analytics` - Promotion analytics

### Export

- `POST /api/export/students` - Export student data
- `GET /api/export/download/{file_id}` - Download exported file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.

## 👥 Authors

- **Your Name** - _Initial work_ - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- FastAPI framework for the excellent web framework
- Pandas team for powerful data processing capabilities
- SQLAlchemy for robust ORM functionality

## 📞 Support

If you have any questions or need help with setup, please open an issue on
GitHub.

---

⭐ **Star this repository if you find it helpful!**
