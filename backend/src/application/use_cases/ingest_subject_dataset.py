"""Use Case: Ingest and Catalog Subject Multi-Angle Dataset."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np

from src.domain.entities import IdentityProfile
from src.domain.enums import AngleQuadrant
from src.domain.exceptions import DomainValidationError
from src.application.ports.face_detector import IFaceDetector
from src.application.ports.identity_extractor import IIdentityExtractor
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from src.infrastructure.security.file_guard import FileGuard


@dataclass
class IngestInputImage:
    """Input image container for dataset ingestion."""
    filename: str
    raw_bytes: bytes
    image_np: np.ndarray


@dataclass(frozen=True)
class IngestDatasetResult:
    """Summary metrics of the dataset ingestion execution."""
    subject_id: str
    name: str
    processed_count: int
    valid_faces_count: int
    discarded_count: int
    quadrants_covered: List[AngleQuadrant]


class IngestSubjectDatasetUseCase:
    """
    Orchestrates the ingestion, quality filtering, 3D pose estimation,
    ArcFace embedding extraction, and multi-angle indexing of a subject.
    """

    def __init__(
        self,
        storage_adapter: LocalStorageAdapter,
        metadata_repo: SQLiteMetadataRepo,
        face_detector: IFaceDetector,
        identity_extractor: IIdentityExtractor,
    ):
        self.storage_adapter = storage_adapter
        self.metadata_repo = metadata_repo
        self.face_detector = face_detector
        self.identity_extractor = identity_extractor

    def execute(
        self,
        subject_id: str,
        name: str,
        images: List[IngestInputImage],
        min_sharpness: float = 100.0,
        min_confidence: float = 0.65,
    ) -> IngestDatasetResult:
        """Executes the ingestion pipeline across all supplied images."""
        if not images:
            raise DomainValidationError("At least one image is required for dataset ingestion")

        embeddings_by_quadrant_accum: Dict[AngleQuadrant, List[List[float]]] = {}
        processed = 0
        valid_faces = 0
        discarded = 0

        for item in images:
            processed += 1
            # 1. DevSecOps validation of magic bytes and size
            FileGuard.inspect_magic_bytes(item.raw_bytes[:32])
            FileGuard.validate_payload_size(len(item.raw_bytes))

            # 2. Save raw image safely to storage
            self.storage_adapter.save_dataset_image(
                subject_id=subject_id,
                filename=item.filename,
                content=item.raw_bytes,
            )

            # 3. Detect primary face in image
            try:
                crop = self.face_detector.detect_primary_face(
                    item.image_np, min_confidence=min_confidence
                )
            except Exception:
                discarded += 1
                continue

            # 4. Filter by sharpness threshold
            if not crop.is_sharp(threshold=min_sharpness):
                discarded += 1
                continue

            # 5. Extract ArcFace embedding from facial ROI
            if crop.embedding is not None:
                embedding = crop.embedding
            else:
                x1, y1, x2, y2 = crop.bbox
                face_roi = item.image_np[y1:y2, x1:x2]
                embedding = self.identity_extractor.extract_embedding(face_roi)

            # 6. Group by 3D pose quadrant
            quadrant = crop.pose.quadrant
            if quadrant not in embeddings_by_quadrant_accum:
                embeddings_by_quadrant_accum[quadrant] = []
            embeddings_by_quadrant_accum[quadrant].append(embedding)
            valid_faces += 1

        if valid_faces == 0:
            raise DomainValidationError("No valid, sharp faces could be extracted from the dataset")

        # 7. Aggregate embeddings per quadrant (normalized mean vector)
        final_embeddings: Dict[AngleQuadrant, List[float]] = {}
        for quad, embs in embeddings_by_quadrant_accum.items():
            final_embeddings[quad] = self.identity_extractor.aggregate_embeddings(embs)

        # 8. Persist profile to metadata repository
        profile = IdentityProfile(
            subject_id=subject_id,
            name=name,
            embeddings_by_quadrant=final_embeddings,
        )
        self.metadata_repo.save_subject_profile(profile)

        return IngestDatasetResult(
            subject_id=subject_id,
            name=name,
            processed_count=processed,
            valid_faces_count=valid_faces,
            discarded_count=discarded,
            quadrants_covered=list(final_embeddings.keys()),
        )
