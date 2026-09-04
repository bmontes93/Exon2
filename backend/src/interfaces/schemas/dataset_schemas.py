"""Pydantic v2 schemas for Dataset Ingestion and Subject Profiles."""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.domain.enums import AngleQuadrant


class DatasetIngestResponse(BaseModel):
    """Response payload returned after dataset ingestion."""
    subject_id: str
    name: str
    processed_count: int
    valid_faces_count: int
    discarded_count: int
    quadrants_covered: List[AngleQuadrant]


class SubjectProfileResponse(BaseModel):
    """Profile representation of a cataloged subject."""
    subject_id: str
    name: str
    available_quadrants: List[AngleQuadrant]
    created_at: datetime
