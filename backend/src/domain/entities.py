"""Domain Entities and Value Objects for EXON-FACE."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from src.domain.enums import AngleQuadrant, JobStatus, RenderMode
from src.domain.exceptions import DomainValidationError


@dataclass(frozen=True)
class HeadPose3D:
    """3D Head Pose orientation in degrees (Yaw, Pitch, Roll)."""
    yaw: float      # Rotation around Y axis: [-90, 90] (negative = left, positive = right)
    pitch: float    # Rotation around X axis: [-90, 90] (negative = down, positive = up)
    roll: float     # Rotation around Z axis: [-90, 90] (tilt)

    def __post_init__(self):
        if not (-90.0 <= self.yaw <= 90.0):
            raise DomainValidationError(f"Yaw angle {self.yaw} out of bounds [-90, 90]")
        if not (-90.0 <= self.pitch <= 90.0):
            raise DomainValidationError(f"Pitch angle {self.pitch} out of bounds [-90, 90]")
        if not (-90.0 <= self.roll <= 90.0):
            raise DomainValidationError(f"Roll angle {self.roll} out of bounds [-90, 90]")

    @property
    def quadrant(self) -> AngleQuadrant:
        """Derives the primary AngleQuadrant based on 3D angles."""
        if abs(self.yaw) <= 15.0 and abs(self.pitch) <= 15.0:
            return AngleQuadrant.FRONTAL
        if self.yaw < -45.0:
            return AngleQuadrant.PROFILE_LEFT
        if self.yaw > 45.0:
            return AngleQuadrant.PROFILE_RIGHT
        if -45.0 <= self.yaw < -15.0:
            return AngleQuadrant.THREE_QUARTER_LEFT
        if 15.0 < self.yaw <= 45.0:
            return AngleQuadrant.THREE_QUARTER_RIGHT
        if self.pitch > 15.0:
            return AngleQuadrant.PITCH_UP
        return AngleQuadrant.PITCH_DOWN


@dataclass(frozen=True)
class FaceCrop:
    """Detected and cropped facial region with quality and geometry metadata."""
    bbox: Tuple[int, int, int, int]          # (x1, y1, x2, y2)
    landmarks: List[Tuple[float, float]]     # 5 or 68 keypoints [(x, y), ...]
    pose: HeadPose3D
    confidence: float
    sharpness_score: float
    aligned_crop_path: Optional[str] = None
    embedding: Optional[List[float]] = None
    landmark_2d_106: Optional[List[Tuple[float, float]]] = None

    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise DomainValidationError(f"Confidence {self.confidence} must be between 0.0 and 1.0")
        if self.sharpness_score < 0.0:
            raise DomainValidationError("Sharpness score cannot be negative")

    def is_sharp(self, threshold: float = 100.0) -> bool:
        """Determines if the crop meets the sharpness criteria."""
        return self.sharpness_score >= threshold


@dataclass
class IdentityProfile:
    """Subject identity profile containing angle-indexed embedding vectors."""
    subject_id: str
    name: str
    embeddings_by_quadrant: Dict[AngleQuadrant, List[float]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_closest_embedding(self, target_quadrant: AngleQuadrant) -> List[float]:
        """
        Retrieves the embedding closest to the requested quadrant.
        Falls back to FRONTAL or first available embedding if requested is missing.
        """
        if target_quadrant in self.embeddings_by_quadrant:
            return self.embeddings_by_quadrant[target_quadrant]
        
        # Fallback to FRONTAL
        if AngleQuadrant.FRONTAL in self.embeddings_by_quadrant:
            return self.embeddings_by_quadrant[AngleQuadrant.FRONTAL]
        
        # Fallback to any available
        if self.embeddings_by_quadrant:
            return next(iter(self.embeddings_by_quadrant.values()))
        
        raise DomainValidationError(f"No embeddings available for subject {self.subject_id}")


@dataclass(frozen=True)
class RenderParams:
    """Fine-tuning parameters for the face synthesis pipeline."""
    identity_weight: float = 1.0        # Weight of identity injection: [0.0, 2.0]
    wavelet_high_pass: float = 1.0      # High-pass texture retention: [0.0, 3.0]
    codeformer_fidelity: float = 0.75   # Face restoration fidelity vs smoothness: [0.0, 1.0]
    occlusion_masking: bool = True      # Enable BiSeNet occlusion segmentation
    source_quadrant: Optional[AngleQuadrant] = None

    def __post_init__(self):
        if not (0.0 <= self.identity_weight <= 2.0):
            raise DomainValidationError(f"identity_weight {self.identity_weight} out of bounds [0.0, 2.0]")
        if not (0.0 <= self.wavelet_high_pass <= 3.0):
            raise DomainValidationError(f"wavelet_high_pass {self.wavelet_high_pass} out of bounds [0.0, 3.0]")
        if not (0.0 <= self.codeformer_fidelity <= 1.0):
            raise DomainValidationError(f"codeformer_fidelity {self.codeformer_fidelity} out of bounds [0.0, 1.0]")


@dataclass
class RenderJob:
    """Represents a synthesis render execution and its lifecycle state."""
    job_id: str
    subject_id: str
    target_image_path: str
    mode: RenderMode
    params: RenderParams
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0               # [0.0, 1.0]
    current_step: str = "INITIALIZING"
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def update_progress(self, step_name: str, progress: float) -> None:
        """Updates job progress and marks as RUNNING."""
        self.status = JobStatus.RUNNING
        self.current_step = step_name
        self.progress = max(0.0, min(1.0, progress))

    def complete(self, output_path: str) -> None:
        """Marks the job as successfully COMPLETED."""
        self.status = JobStatus.COMPLETED
        self.progress = 1.0
        self.current_step = "DONE"
        self.output_path = output_path
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, error_message: str) -> None:
        """Marks the job as FAILED."""
        self.status = JobStatus.FAILED
        self.current_step = "FAILED"
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
