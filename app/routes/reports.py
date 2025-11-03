from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
from typing import List

from app.database import get_db, User, Report, Metric, Recommendation
from app.schemas.report import ReportResponse, AnalysisResult
from app.utils.auth_utils import get_current_user
from app.services.ocr_service import OCRService
from app.services.ner_service import NERService
from app.services.rag_service import RAGService
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# Initialize services
ocr_service = OCRService()
ner_service = NERService()
rag_service = RAGService()

@router.post("/upload", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze a blood report"""
    
    # Validate file type
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.gif']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    try:
        # Save uploaded file
        user_upload_dir = settings.UPLOAD_DIR / str(current_user.id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 1: OCR - Extract text
        extracted_text = ocr_service.extract_text(file_path)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient text from the document. Please ensure the image is clear."
            )
        
        # Step 2: NER - Extract metrics
        analysis = ner_service.analyze_text(extracted_text)
        metrics = analysis['metrics']
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not identify blood test parameters. Please ensure the document contains valid test results."
            )
        
        # Step 3: RAG - Generate recommendations
        recommendations_list = rag_service.generate_recommendations(metrics)
        summary = rag_service.generate_summary(metrics)
        
        # Step 4: Save to database
        report = Report(
            user_id=current_user.id,
            filename=file.filename,
            file_path=str(file_path),
            extracted_text=extracted_text,
            summary=summary,
            status=analysis['status']
        )
        db.add(report)
        db.flush()
        
        # Save metrics
        for metric_data in metrics:
            metric = Metric(
                report_id=report.id,
                name=metric_data['name'],
                value=metric_data['value'],
                unit=metric_data.get('unit'),
                reference_min=metric_data.get('reference_min'),
                reference_max=metric_data.get('reference_max'),
                status=metric_data['status']
            )
            db.add(metric)
        
        # Save recommendations
        for rec_text in recommendations_list:
            recommendation = Recommendation(
                report_id=report.id,
                text=rec_text,
                source="RAG System"
            )
            db.add(recommendation)
        
        db.commit()
        db.refresh(report)
        
        # Return analysis result
        return AnalysisResult(
            report_id=report.id,
            filename=report.filename,
            summary=summary,
            status=report.status,
            metrics=metrics,
            recommendations=recommendations_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up file if database operation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing report: {str(e)}"
        )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific report"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a report"""
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Delete associated file
    file_path = Path(report.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database (cascades to metrics and recommendations)
    db.delete(report)
    db.commit()
    
    return None