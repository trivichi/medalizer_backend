from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db, User, Report
from app.schemas.report import ReportListResponse
from app.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("/", response_model=List[ReportListResponse])
async def get_report_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for the current user"""
    reports = db.query(Report)\
        .filter(Report.user_id == current_user.id)\
        .order_by(Report.created_at.desc())\
        .all()
    
    return reports