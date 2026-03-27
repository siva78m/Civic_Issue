import os
import json
import base64
import re
from typing import Optional, List
import google.generativeai as genai
from PIL import Image
import io

from models import AnalysisRequest, ExistingIssue

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

# Use the free tier Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

VALID_CATEGORIES = [
    "POTHOLE", "GARBAGE", "WATER_LEAKAGE", "DAMAGED_INFRASTRUCTURE",
    "STREET_LIGHT", "SEWAGE", "ENCROACHMENT", "NOISE_POLLUTION",
    "AIR_POLLUTION", "OTHER"
]

VALID_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VALID_URGENCIES = ["LOW", "MEDIUM", "HIGH", "IMMEDIATE"]


def decode_image(image_base64: str) -> Optional[bytes]:
    """Decode base64 image to bytes."""
    try:
        # Remove data URL prefix if present
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        return base64.b64decode(image_base64)
    except Exception:
        return None


def prepare_image_part(image_base64: str) -> Optional[dict]:
    """Prepare image for Gemini API."""
    image_bytes = decode_image(image_base64)
    if not image_bytes:
        return None

    try:
        # Detect MIME type
        img = Image.open(io.BytesIO(image_bytes))
        fmt = img.format or "JPEG"
        mime_type = f"image/{fmt.lower()}"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        return {
            "mime_type": mime_type,
            "data": base64.b64decode(image_base64.split("base64,")[-1])
            if "base64," in image_base64
            else image_bytes,
        }
    except Exception:
        return None


async def analyze_civic_issue(request: AnalysisRequest) -> dict:
    """
    Analyze a civic issue using Google Gemini AI.

    Returns structured analysis with category, severity, urgency,
    confidence, analysis text, and tags.
    """
    prompt = f"""You are an expert AI system for urban governance and civic issue analysis.
Analyze this civic complaint and provide a precise structured assessment.

Issue Title: {request.title}
Description: {request.description}
{f"Suggested Category: {request.category}" if request.category else ""}
GPS Location: Latitude {request.latitude:.6f}, Longitude {request.longitude:.6f}
{"Image provided: Yes - analyze it carefully for visual evidence." if request.image_base64 else "Image provided: No"}

Provide your analysis as ONLY a valid JSON object (no markdown, no code blocks, no extra text):
{{
  "category": "one of: POTHOLE, GARBAGE, WATER_LEAKAGE, DAMAGED_INFRASTRUCTURE, STREET_LIGHT, SEWAGE, ENCROACHMENT, NOISE_POLLUTION, AIR_POLLUTION, OTHER",
  "severity": "one of: LOW, MEDIUM, HIGH, CRITICAL",
  "urgency": "one of: LOW, MEDIUM, HIGH, IMMEDIATE",
  "confidence": 0.85,
  "analysis_text": "Professional 2-3 sentence assessment of the issue, its impact, and recommended action",
  "tags": ["tag1", "tag2", "tag3"]
}}

Severity Guidelines:
- CRITICAL: Immediate danger (open manholes, collapsed bridge, severe flooding, exposed wires)
- HIGH: Significant hazard affecting daily life (large potholes, major infrastructure damage, active water leaks)
- MEDIUM: Moderate issue reducing quality of life (garbage accumulation, minor potholes, dim street lights)
- LOW: Minor aesthetic or functional issues (faded road markings, very small potholes)

Urgency Guidelines:
- IMMEDIATE: Life-threatening or causing immediate accidents
- HIGH: Causing disruption to traffic/residents/businesses
- MEDIUM: Affecting daily convenience but not emergency
- LOW: Can wait for scheduled maintenance

Tag Guidelines:
- 3-5 specific descriptive tags (e.g., "road-damage", "public-safety", "infrastructure", "monsoon-damage")

Confidence: Float 0.0-1.0 based on clarity of report and image evidence"""

    try:
        parts = []

        # Add image if provided
        if request.image_base64:
            image_part = prepare_image_part(request.image_base64)
            if image_part:
                parts.append(image_part)

        parts.append(prompt)

        response = model.generate_content(parts)
        text = response.text.strip()

        # Clean markdown code blocks
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        # Parse JSON
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse JSON from AI response")

        # Validate and sanitize
        category = result.get("category", "OTHER")
        if category not in VALID_CATEGORIES:
            category = request.category if request.category in VALID_CATEGORIES else "OTHER"

        severity = result.get("severity", "MEDIUM")
        if severity not in VALID_SEVERITIES:
            severity = "MEDIUM"

        urgency = result.get("urgency", "MEDIUM")
        if urgency not in VALID_URGENCIES:
            urgency = "MEDIUM"

        confidence = float(result.get("confidence", 0.75))
        confidence = max(0.0, min(1.0, confidence))

        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [str(t) for t in tags[:5]]

        analysis_text = str(result.get("analysis_text", "Issue analyzed successfully."))

        return {
            "category": category,
            "severity": severity,
            "urgency": urgency,
            "confidence": confidence,
            "analysis_text": analysis_text,
            "tags": tags,
        }

    except Exception as e:
        print(f"Gemini AI analysis error: {e}")
        # Return fallback analysis
        return {
            "category": request.category if request.category in VALID_CATEGORIES else "OTHER",
            "severity": "MEDIUM",
            "urgency": "MEDIUM",
            "confidence": 0.5,
            "analysis_text": "Automated analysis unavailable. Issue recorded for manual review by civic authorities.",
            "tags": ["manual-review", "pending-analysis"],
        }
