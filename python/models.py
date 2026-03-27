from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class Category(str, Enum):
    POTHOLE = "POTHOLE"
    GARBAGE = "GARBAGE"
    WATER_LEAKAGE = "WATER_LEAKAGE"
    DAMAGED_INFRASTRUCTURE = "DAMAGED_INFRASTRUCTURE"
    STREET_LIGHT = "STREET_LIGHT"
    SEWAGE = "SEWAGE"
    ENCROACHMENT = "ENCROACHMENT"
    NOISE_POLLUTION = "NOISE_POLLUTION"
    AIR_POLLUTION = "AIR_POLLUTION"
    OTHER = "OTHER"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Urgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    IMMEDIATE = "IMMEDIATE"


class ExistingIssue(BaseModel):
    id: str
    latitude: float
    longitude: float
    category: str
    status: str


class AnalysisRequest(BaseModel):
    title: str
    description: str
    latitude: float
    longitude: float
    category: Optional[str] = None
    image_base64: Optional[str] = None
    existing_issues: Optional[List[ExistingIssue]] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    category: str
    severity: str
    urgency: str
    priority_score: float
    confidence: float
    analysis_text: str
    tags: List[str]
    is_duplicate: bool
    duplicate_of_id: Optional[str] = None
    mcia_breakdown: dict = Field(default_factory=dict)
