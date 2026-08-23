"""
Domain Models — Layer 0 (Foundation)
=====================================
Pydantic v2 schemas that act as strict data contracts for the entire pipeline.
All layers above MUST communicate through these models.

Architectural Rule: This layer imports NOTHING from this project.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ── Enumerations ──────────────────────────────────────────────────────────────


class OpportunityType(str, Enum):
    """Classification of the AI opportunity."""

    HACKATHON = "Hackathon"
    COMPETITION = "Competition"
    CONFERENCE = "Conference"
    FELLOWSHIP = "Fellowship"
    GRANT = "Grant"
    OTHER = "Other"


class DifficultyLevel(str, Enum):
    """Skill level required for the opportunity."""

    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class LocationType(str, Enum):
    """Modality of the opportunity."""

    ONLINE = "Online"
    HYBRID = "Hybrid"
    IN_PERSON = "In-Person"


# ── Core Domain Model ─────────────────────────────────────────────────────────


class Opportunity(BaseModel):
    """
    Core domain schema representing a single AI opportunity.

    This model is the single source of truth for what constitutes a valid
    opportunity record throughout the entire pipeline. Pydantic v2 enforces
    all constraints at instantiation time — any schema drift from the scraper
    will raise a ValidationError and trigger the self-healing loop.
    """

    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="The name of the event or hackathon.",
    )
    url: HttpUrl = Field(
        ...,
        description="The direct, canonical URL to the opportunity page.",
    )
    source: str = Field(
        ...,
        description="The platform where this was found (e.g., 'unstop', 'devpost', 'hack2skill').",
    )
    organizer: str = Field(
        ...,
        min_length=2,
        description="The organizing body, company, or institution.",
    )
    opportunity_type: OpportunityType = Field(
        default=OpportunityType.OTHER,
        description="Classification of the opportunity.",
    )
    description: Optional[str] = Field(
        None,
        description="Detailed explanation of the opportunity.",
    )
    prizes_total: Optional[float] = Field(
        0.0,
        ge=0.0,
        description="Aggregate financial value of all prizes in USD.",
    )
    deadline: Optional[datetime] = Field(
        None,
        description="ISO-formatted application or submission deadline.",
    )
    location_type: LocationType = Field(
        default=LocationType.ONLINE,
        description="Modality of the opportunity.",
    )
    difficulty: Optional[DifficultyLevel] = Field(
        None,
        description="Skill level required to participate.",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Array of tech stack tags (e.g. ['Python', 'ML', 'NLP']).",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the opportunity is currently open for applications.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this record was first ingested.",
    )

    @field_validator("prizes_total", mode="before")
    @classmethod
    def coerce_prizes_total(cls, value: object) -> Optional[float]:
        """
        Coerces prize value from various scraper formats:
        - dict: {"value": 740000, "currency": "USD", ...} -> 740000.0
        - string: "$740,000", "740000" -> 740000.0
        - float / int -> float
        - None / missing -> 0.0
        """
        if value is None:
            return 0.0
        if isinstance(value, dict):
            val = value.get("value")
            try:
                return float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            import re
            cleaned = re.sub(r"[^\d.]", "", value)
            try:
                return float(cleaned) if cleaned else 0.0
            except ValueError:
                return 0.0
        return 0.0

    @field_validator("deadline", mode="before")
    @classmethod
    def parse_flexible_deadline(cls, value: object) -> Optional[datetime]:
        """
        Parses deadlines from various scraper formats:
        - ISO datetime string: '2026-10-01T00:00:00Z'
        - Date range: 'Jul 31 - Oct 01, 2026' -> takes end date 'Oct 01, 2026'
        - Short date range: 'Aug 04 - 31, 2026' -> takes end date 'Aug 31, 2026'
        - Relative string: '18 days left' -> calculates future datetime
        - None or unparseable -> returns None gracefully
        """
        if value is None or isinstance(value, datetime):
            return value

        if isinstance(value, str):
            val = value.strip()
            if not val:
                return None

            import re
            from datetime import timedelta

            # Relative: "X days left" / "X hours left"
            rel_days_match = re.search(r"(\d+)\s+days?\s+left", val, re.IGNORECASE)
            if rel_days_match:
                days = int(rel_days_match.group(1))
                return datetime.utcnow() + timedelta(days=days)

            rel_hours_match = re.search(r"(\d+)\s+hours?\s+left", val, re.IGNORECASE)
            if rel_hours_match:
                hours = int(rel_hours_match.group(1))
                return datetime.utcnow() + timedelta(hours=hours)

            # Date range format: "Jul 31 - Oct 01, 2026" or "Aug 04 - 31, 2026"
            if "-" in val:
                parts = [p.strip() for p in val.split("-")]
                end_part = parts[-1]  # e.g., "Oct 01, 2026" or "31, 2026"
                # If end_part is just "31, 2026", get month from first part
                if not re.search(r"[a-zA-Z]", end_part) and len(parts) > 1:
                    start_month = re.search(r"([a-zA-Z]+)", parts[0])
                    if start_month:
                        end_part = f"{start_month.group(1)} {end_part}"
                val = end_part

            # Try parsing with various date formats
            date_formats = [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%b %d, %Y",    # Oct 01, 2026
                "%B %d, %Y",    # October 01, 2026
                "%b %d %Y",
                "%d %b %Y",
                "%d %B %Y",
            ]
            for fmt in date_formats:
                try:
                    return datetime.strptime(val, fmt)
                except ValueError:
                    continue

            # Fallback: regex for "Month Day, Year"
            match = re.search(r"([a-zA-Z]+)\s+(\d{1,2}),?\s+(\d{4})", val)
            if match:
                month_str, day_str, year_str = match.groups()
                for m_fmt in ["%b", "%B"]:
                    try:
                        parsed_m = datetime.strptime(month_str, m_fmt).month
                        return datetime(int(year_str), parsed_m, int(day_str))
                    except ValueError:
                        pass

        # Return None rather than crashing ingestion on unparseable date text
        return None


    @field_validator("url", mode="before")
    @classmethod
    def coerce_url_string(cls, value: object) -> object:
        """Accept plain strings alongside HttpUrl objects."""
        if isinstance(value, str):
            return value
        return value

    @field_validator("opportunity_type", mode="before")
    @classmethod
    def normalize_opportunity_type(cls, value: object) -> object:
        """
        Maps raw scraper strings (e.g. 'hackathon', 'competition') to the
        OpportunityType enum. Case-insensitive. Falls back to OTHER.
        """
        if isinstance(value, str):
            mapping = {
                "hackathon": "Hackathon",
                "competition": "Competition",
                "conference": "Conference",
                "fellowship": "Fellowship",
                "grant": "Grant",
                "event": "Other",
            }
            return mapping.get(value.lower().strip(), "Other")
        return value

    @field_validator("is_active", mode="before")
    @classmethod
    def normalize_is_active(cls, value: object) -> object:
        """
        Converts scraper status strings ('active', 'upcoming', 'closed') to bool.
        'active' and 'upcoming' → True, 'closed'/'expired' → False.
        """
        if isinstance(value, str):
            return value.lower().strip() in ("active", "upcoming", "open")
        return value

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "ignore",  # Tolerate extra scraper fields without failing
    }
