"""Domain Enums for EXON-FACE."""
from enum import Enum


class AngleQuadrant(str, Enum):
    """Categorization of 3D facial pose angles."""
    FRONTAL = "FRONTAL"                     # Yaw in [-15, 15], Pitch in [-15, 15]
    THREE_QUARTER_LEFT = "THREE_QUARTER_LEFT"   # Yaw in [-45, -15)
    THREE_QUARTER_RIGHT = "THREE_QUARTER_RIGHT" # Yaw in (15, 45]
    PROFILE_LEFT = "PROFILE_LEFT"           # Yaw < -45
    PROFILE_RIGHT = "PROFILE_RIGHT"         # Yaw > 45
    PITCH_UP = "PITCH_UP"                   # Pitch > 15
    PITCH_DOWN = "PITCH_DOWN"               # Pitch < -15


class RenderMode(str, Enum):
    """Execution mode for face synthesis."""
    EXPRESS = "EXPRESS"         # 1-Click automatic pipeline
    STUDIO_PRO = "STUDIO_PRO"   # Full control over weights, masks, wavelet and restoration


class JobStatus(str, Enum):
    """Status lifecycle of a render job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
