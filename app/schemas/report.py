from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MetricBase(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: str = "normal"


class MetricResponse(MetricBase):
    id: int
    report_id: int
    
    class Config:
        from_attributes = True


class RecommendationBase(BaseModel):
    text: str
    source: Optional[str] = None


class RecommendationResponse(RecommendationBase):
    id: int
    report_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    summary: Optional[str] = None
    status: str
    created_at: datetime
    metrics: List[MetricResponse] = []
    recommendations: List[RecommendationResponse] = []
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    id: int
    filename: str
    summary: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    report_id: int
    filename: str
    summary: str
    status: str
    metrics: List[dict]
    recommendations: List[str]