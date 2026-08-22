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

    @field_validator("deadline")
    @classmethod
    def validate_future_deadline(cls, value: Optional[datetime]) -> Optional[datetime]:
        """
        Soft-validates that the deadline is in the future.
        Expired deadlines are allowed (is_active should be False in those cases),
        but the validator ensures the field parses as a valid ISO datetime.
        Downstream pipeline logic handles active/inactive status.
        """
        if value and value.replace(tzinfo=None) < datetime.utcnow():
            # Expired deadline — the record may still be historically relevant.
            # Log downstream; do NOT raise here to avoid blocking ingestion.
            pass
        return value

    @field_validator("url", mode="before")
    @classmethod
    def coerce_url_string(cls, value: object) -> object:
        """Accept plain strings alongside HttpUrl objects."""
        if isinstance(value, str):
            return value
        return value

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "ignore",  # Tolerate extra scraper fields without failing
    }
