# app/__init__.py
"""Blood Report Analyzer Backend"""

__version__ = "1.0.0"

# app/models/__init__.py
"""Database models"""
from app.database import User, Report, Metric, Recommendation

__all__ = ["User", "Report", "Metric", "Recommendation"]

# app/routes/__init__.py
"""API routes"""
from app.routes import auth, reports, history

__all__ = ["auth", "reports", "history"]

# app/services/__init__.py
"""Business logic services"""
from app.services.ocr_service import OCRService
from app.services.ner_service import NERService
from app.services.rag_service import RAGService

__all__ = ["OCRService", "NERService", "RAGService"]

# app/schemas/__init__.py
"""Pydantic schemas"""
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.schemas.report import (
    MetricBase, MetricResponse, 
    RecommendationBase, RecommendationResponse,
    ReportResponse, ReportListResponse, AnalysisResult
)

__all__ = [
    "UserCreate", "UserLogin", "Token", "UserResponse",
    "MetricBase", "MetricResponse",
    "RecommendationBase", "RecommendationResponse",
    "ReportResponse", "ReportListResponse", "AnalysisResult"
]

# app/utils/__init__.py
"""Utility functions"""
from app.utils.auth_utils import (
    hash_password, verify_password,
    create_access_token, decode_token,
    get_current_user
)

__all__ = [
    "hash_password", "verify_password",
    "create_access_token", "decode_token",
    "get_current_user"
]

# tests/__init__.py
"""Test suite"""