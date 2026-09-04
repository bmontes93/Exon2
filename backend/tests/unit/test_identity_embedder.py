"""Unit tests for Multi-Angle Identity Embedding Adapter."""
import pytest
import numpy as np

from src.domain.enums import AngleQuadrant
from src.infrastructure.adapters.insightface_adapter import InsightFaceAdapter


class TestInsightFaceAdapter:
    def test_extract_embedding_shape_and_normalization(self):
        adapter = InsightFaceAdapter()
        # Synthetic RGB face crop (112x112x3)
        np.random.seed(42)
        face_img = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)

        embedding = adapter.extract_embedding(face_img)

        assert isinstance(embedding, list)
        assert len(embedding) == 512
        # Check L2 normalization
        norm = np.linalg.norm(np.array(embedding))
        assert pytest.approx(norm, 1e-4) == 1.0

    def test_cosine_similarity_computation(self):
        adapter = InsightFaceAdapter()

        v1 = np.array([1.0, 0.0, 0.0] + [0.0] * 509)
        v2 = np.array([1.0, 0.0, 0.0] + [0.0] * 509)
        v3 = np.array([0.0, 1.0, 0.0] + [0.0] * 509)
        v4 = np.array([-1.0, 0.0, 0.0] + [0.0] * 509)

        sim_identical = adapter.compute_cosine_similarity(v1.tolist(), v2.tolist())
        sim_orthogonal = adapter.compute_cosine_similarity(v1.tolist(), v3.tolist())
        sim_opposite = adapter.compute_cosine_similarity(v1.tolist(), v4.tolist())

        assert pytest.approx(sim_identical, 1e-4) == 1.0
        assert pytest.approx(sim_orthogonal, 1e-4) == 0.0
        assert pytest.approx(sim_opposite, 1e-4) == -1.0

    def test_aggregate_embeddings_for_quadrant(self):
        adapter = InsightFaceAdapter()

        # Two embeddings pointing in slightly different directions
        e1 = [0.8, 0.6] + [0.0] * 510
        e2 = [0.6, 0.8] + [0.0] * 510

        merged = adapter.aggregate_embeddings([e1, e2])
        assert len(merged) == 512
        assert pytest.approx(np.linalg.norm(merged), 1e-4) == 1.0
        # Aggregation should average the components symmetrically
        assert pytest.approx(merged[0], 1e-4) == pytest.approx(merged[1], 1e-4)
