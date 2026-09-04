"""Local File System Storage Adapter with Path Defense."""
import shutil
from pathlib import Path
from typing import Dict, Union, Optional

from src.infrastructure.security.path_sanitizer import PathSanitizer


class LocalStorageAdapter:
    """Manages files and directory paths on the local filesystem."""

    def __init__(
        self,
        models_dir: Union[str, Path] = "models_cache",
        datasets_dir: Union[str, Path] = "datasets",
        outputs_dir: Union[str, Path] = "outputs",
    ):
        self.models_dir = Path(models_dir).resolve()
        self.datasets_dir = Path(datasets_dir).resolve()
        self.outputs_dir = Path(outputs_dir).resolve()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensures all configured base directories exist."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def update_paths(
        self,
        models_dir: Optional[Union[str, Path]] = None,
        datasets_dir: Optional[Union[str, Path]] = None,
        outputs_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Dynamically updates base storage paths."""
        if models_dir:
            self.models_dir = Path(models_dir).resolve()
        if datasets_dir:
            self.datasets_dir = Path(datasets_dir).resolve()
        if outputs_dir:
            self.outputs_dir = Path(outputs_dir).resolve()
        self._ensure_directories()

    def save_output_image(self, filename: str, content: bytes) -> Path:
        """Safely saves a rendered image to outputs_dir."""
        safe_name = PathSanitizer.sanitize_filename(filename)
        target_path = PathSanitizer.resolve_safe_path(self.outputs_dir, safe_name)
        target_path.write_bytes(content)
        return target_path

    def save_dataset_image(self, subject_id: str, filename: str, content: bytes) -> Path:
        """Safely saves an uploaded subject image to datasets_dir/{subject_id}/."""
        safe_subject = PathSanitizer.sanitize_filename(subject_id, prefix="subj")
        subj_dir = self.datasets_dir / safe_subject
        subj_dir.mkdir(parents=True, exist_ok=True)

        safe_name = PathSanitizer.sanitize_filename(filename)
        target_path = PathSanitizer.resolve_safe_path(subj_dir, safe_name)
        target_path.write_bytes(content)
        return target_path

    def get_disk_metrics(self) -> Dict[str, float]:
        """Calculates total, used, and free disk space in Gigabytes for outputs_dir."""
        usage = shutil.disk_usage(self.outputs_dir)
        gb_factor = 1024 ** 3
        return {
            "total_gb": round(usage.total / gb_factor, 2),
            "used_gb": round(usage.used / gb_factor, 2),
            "free_gb": round(usage.free / gb_factor, 2),
        }
