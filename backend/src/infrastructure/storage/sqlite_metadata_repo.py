"""SQLite Metadata Repository for Subject Profiles and Render Jobs."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.domain.entities import IdentityProfile, RenderJob, RenderParams
from src.domain.enums import AngleQuadrant, JobStatus, RenderMode


class SQLiteMetadataRepo:
    """Manages metadata persistence using an embedded SQLite database in WAL mode."""

    def __init__(self, db_path: Union[str, Path] = "exon_metadata.db"):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subjects (
                    subject_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    embeddings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS render_jobs (
                    job_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    target_image_path TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL,
                    current_step TEXT NOT NULL,
                    output_path TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                """
            )
            conn.commit()

    def save_subject_profile(self, profile: IdentityProfile) -> None:
        """Inserts or replaces an IdentityProfile record."""
        # Serialize embeddings dictionary
        emb_serialized = {
            quadrant.value: vector
            for quadrant, vector in profile.embeddings_by_quadrant.items()
        }
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO subjects (subject_id, name, embeddings_json, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (
                    profile.subject_id,
                    profile.name,
                    json.dumps(emb_serialized),
                    profile.created_at.isoformat(),
                ),
            )
            conn.commit()

    def get_subject_profile(self, subject_id: str) -> Optional[IdentityProfile]:
        """Fetches an IdentityProfile by subject_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT subject_id, name, embeddings_json, created_at FROM subjects WHERE subject_id = ?;",
                (subject_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            raw_embs = json.loads(row["embeddings_json"])
            embeddings_by_quadrant = {
                AngleQuadrant(k): v for k, v in raw_embs.items()
            }
            return IdentityProfile(
                subject_id=row["subject_id"],
                name=row["name"],
                embeddings_by_quadrant=embeddings_by_quadrant,
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def list_subject_profiles(self) -> List[IdentityProfile]:
        """Lists all registered IdentityProfiles."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT subject_id, name, embeddings_json, created_at FROM subjects ORDER BY created_at DESC;"
            )
            results = []
            for row in cursor.fetchall():
                raw_embs = json.loads(row["embeddings_json"])
                embeddings_by_quadrant = {
                    AngleQuadrant(k): v for k, v in raw_embs.items()
                }
                results.append(
                    IdentityProfile(
                        subject_id=row["subject_id"],
                        name=row["name"],
                        embeddings_by_quadrant=embeddings_by_quadrant,
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
            return results

    def save_render_job(self, job: RenderJob) -> None:
        """Saves a new RenderJob."""
        params_dict = {
            "identity_weight": job.params.identity_weight,
            "wavelet_high_pass": job.params.wavelet_high_pass,
            "codeformer_fidelity": job.params.codeformer_fidelity,
            "occlusion_masking": job.params.occlusion_masking,
            "source_quadrant": job.params.source_quadrant.value if job.params.source_quadrant else None,
        }
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO render_jobs (
                    job_id, subject_id, target_image_path, mode, params_json,
                    status, progress, current_step, output_path, error_message,
                    created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    job.job_id,
                    job.subject_id,
                    job.target_image_path,
                    job.mode.value,
                    json.dumps(params_dict),
                    job.status.value,
                    job.progress,
                    job.current_step,
                    job.output_path,
                    job.error_message,
                    job.created_at.isoformat(),
                    job.completed_at.isoformat() if job.completed_at else None,
                ),
            )
            conn.commit()

    def update_render_job(self, job: RenderJob) -> None:
        """Updates an existing RenderJob status and progress."""
        self.save_render_job(job)

    def get_render_job(self, job_id: str) -> Optional[RenderJob]:
        """Retrieves a RenderJob by its job_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM render_jobs WHERE job_id = ?;", (job_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            raw_params = json.loads(row["params_json"])
            source_q = (
                AngleQuadrant(raw_params["source_quadrant"])
                if raw_params.get("source_quadrant")
                else None
            )
            params = RenderParams(
                identity_weight=raw_params["identity_weight"],
                wavelet_high_pass=raw_params["wavelet_high_pass"],
                codeformer_fidelity=raw_params["codeformer_fidelity"],
                occlusion_masking=raw_params["occlusion_masking"],
                source_quadrant=source_q,
            )

            job = RenderJob(
                job_id=row["job_id"],
                subject_id=row["subject_id"],
                target_image_path=row["target_image_path"],
                mode=RenderMode(row["mode"]),
                params=params,
                status=JobStatus(row["status"]),
                progress=row["progress"],
                current_step=row["current_step"],
                output_path=row["output_path"],
                error_message=row["error_message"],
                created_at=datetime.fromisoformat(row["created_at"]),
                completed_at=(
                    datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None
                ),
            )
            return job
