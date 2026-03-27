import math
from typing import Optional, List
from models import ExistingIssue


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the Haversine distance between two GPS coordinates.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def detect_duplicate(
    latitude: float,
    longitude: float,
    category: str,
    existing_issues: List[ExistingIssue],
    radius_meters: float = 500.0,
) -> tuple[bool, Optional[str]]:
    """
    Detect if the new issue is a duplicate of an existing one using geospatial analysis.

    Args:
        latitude: New issue latitude
        longitude: New issue longitude
        category: AI-classified category of the new issue
        existing_issues: List of existing active issues
        radius_meters: Duplicate detection radius (default 500m)

    Returns:
        Tuple of (is_duplicate: bool, duplicate_of_id: Optional[str])
    """
    non_terminal_statuses = {"PENDING", "UNDER_REVIEW", "IN_PROGRESS"}
    closest_distance = float("inf")
    closest_id = None

    for existing in existing_issues:
        # Skip resolved/rejected/already-duplicate issues
        if existing.status not in non_terminal_statuses:
            continue

        # Check if same category
        if existing.category != category:
            continue

        # Calculate distance
        distance = haversine_distance(latitude, longitude, existing.latitude, existing.longitude)

        if distance <= radius_meters and distance < closest_distance:
            closest_distance = distance
            closest_id = existing.id

    if closest_id:
        return True, closest_id
    return False, None
