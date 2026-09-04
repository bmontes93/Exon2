"""Port interface for Facial Identity Extraction and Embedding Vector Operations."""
from abc import ABC, abstractmethod
from typing import List
import numpy as np


class IIdentityExtractor(ABC):
    """Port for deep facial feature representation and ArcFace identity extraction."""

    @abstractmethod
    def extract_embedding(self, face_image: np.ndarray) -> List[float]:
        """Extracts a 512-dimensional normalized ArcFace embedding vector."""
        pass

    @abstractmethod
    def compute_cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Computes the cosine similarity metric between two normalized embedding vectors."""
        pass

    @abstractmethod
    def aggregate_embeddings(self, embeddings: List[List[float]]) -> List[float]:
        """Averages and re-normalizes multiple embeddings representing the same pose quadrant."""
        pass
