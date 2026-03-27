"""
Urban Governance AI Service
FastAPI service for AI-powered civic issue analysis using Google Gemini.

Features:
- Multimodal issue analysis (text + image) using Gemini 1.5 Flash
- AI-powered classification into civic categories
- Severity and urgency detection
- Duplicate detection using geospatial analysis (Haversine formula)
- MCIA (Multimodal Civic Intelligence Algorithm) priority scoring

Run: uvicorn main:app --reload --port 8000
"""

import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import AnalysisRequest, AnalysisResponse
from ai_analyzer import analyze_civic_issue
from duplicate_detector import detect_duplicate
from priority_calculator import calculate_mcia_priority, get_priority_label

load_dotenv()

app = FastAPI(
    title="Urban Governance AI Service",
    description="AI-powered civic issue analysis using Google Gemini and MCIA algorithm",
    version="1.0.0",
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "Urban Governance AI Service",
        "version": "1.0.0",
        "model": "gemini-1.5-flash",
        "status": "operational",
        "features": [
            "Multimodal Issue Classification",
            "Severity & Urgency Detection",
            "Geospatial Duplicate Detection",
            "MCIA Priority Scoring",
        ],
    }


@app.get("/health")
async def health():
    api_key = os.getenv("GEMINI_API_KEY")
    return {
        "status": "healthy",
        "gemini_configured": bool(api_key),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_issue(request: AnalysisRequest):
    """
    Analyze a civic issue using Gemini AI.

    Process:
    1. Send text + optional image to Gemini 1.5 Flash
    2. AI classifies category, severity, urgency with confidence
    3. Check for duplicate reports within 500m using Haversine formula
    4. Calculate MCIA priority score
    5. Return comprehensive analysis

    MCIA Priority Score Formula:
        Score = (Severity × 0.4) + (Urgency × 0.3) + (Community × 0.2) + (Recency × 0.1)
    """
    try:
        # Step 1: AI Analysis using Gemini
        ai_result = await analyze_civic_issue(request)

        # Step 2: Duplicate Detection (Geospatial)
        is_duplicate = False
        duplicate_of_id = None

        if request.existing_issues:
            is_duplicate, duplicate_of_id = detect_duplicate(
                latitude=request.latitude,
                longitude=request.longitude,
                category=ai_result["category"],
                existing_issues=request.existing_issues,
                radius_meters=500.0,
            )

        # Step 3: MCIA Priority Score Calculation
        priority_score, mcia_breakdown = calculate_mcia_priority(
            severity=ai_result["severity"],
            urgency=ai_result["urgency"],
            upvote_count=0,
            created_at=datetime.now(),
        )

        priority_label = get_priority_label(priority_score)

        return AnalysisResponse(
            category=ai_result["category"],
            severity=ai_result["severity"],
            urgency=ai_result["urgency"],
            priority_score=priority_score,
            confidence=ai_result["confidence"],
            analysis_text=ai_result["analysis_text"],
            tags=ai_result["tags"],
            is_duplicate=is_duplicate,
            duplicate_of_id=duplicate_of_id,
            mcia_breakdown={
                **mcia_breakdown,
                "priority_label": priority_label,
            },
        )

    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )


@app.post("/priority/recalculate")
async def recalculate_priority(
    severity: str,
    urgency: str,
    upvote_count: int = 0,
    created_at: Optional[str] = None,
):
    """
    Recalculate MCIA priority score for an existing issue.
    Called when upvotes change or for periodic priority updates.
    """
    dt = datetime.fromisoformat(created_at) if created_at else datetime.now()
    priority_score, breakdown = calculate_mcia_priority(severity, urgency, upvote_count, dt)

    return {
        "priority_score": priority_score,
        "priority_label": get_priority_label(priority_score),
        "breakdown": breakdown,
    }


@app.post("/duplicate/check")
async def check_duplicate(
    latitude: float,
    longitude: float,
    category: str,
    existing_issues: list,
    radius_meters: float = 500.0,
):
    """Check if an issue is a duplicate of existing ones."""
    from models import ExistingIssue
    issues = [ExistingIssue(**i) for i in existing_issues]
    is_dup, dup_id = detect_duplicate(latitude, longitude, category, issues, radius_meters)
    return {"is_duplicate": is_dup, "duplicate_of_id": dup_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
