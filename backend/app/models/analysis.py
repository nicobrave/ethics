from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EthicsCategory(str, Enum):
    ETHICAL = "ethical"
    WARNING = "warning"
    DANGER = "danger"

class AnalysisRequest(BaseModel):
    url: HttpUrl
    deep_scan: bool = Field(default=False, description="Análisis profundo incluyendo términos de servicio")

class CriteriaScore(BaseModel):
    privacy: int = Field(ge=0, le=10)
    social_impact: int = Field(ge=0, le=10)
    transparency: int = Field(ge=0, le=10)
    fairness: int = Field(ge=0, le=10)

class RedFlag(BaseModel):
    severity: str = Field(description="low, medium, high")
    category: str = Field(description="privacy, social, transparency, etc.")
    description: str
    evidence: Optional[str] = None

class AnalysisResult(BaseModel):
    id: str
    url: str
    timestamp: datetime
    
    # Core Results
    overall_score: int = Field(ge=0, le=100)
    category: EthicsCategory
    title: str
    justification: str
    
    # Detailed Scores
    criteria_scores: CriteriaScore
    
    # Red Flags
    red_flags: List[RedFlag] = []
    
    # Technical Details
    analysis_time: float = Field(description="Tiempo de análisis en segundos")
    pages_analyzed: int
    content_length: int
    
    # AI Analysis Details
    ai_confidence: float = Field(ge=0, le=1)
    detected_patterns: List[str] = []

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None 