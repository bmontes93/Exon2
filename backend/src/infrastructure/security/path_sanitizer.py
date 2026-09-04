"""Path Sanitizer and Traversal Defense."""
import re
import uuid
from pathlib import Path
from typing import Union

from src.domain.exceptions import SecurityViolationException


class PathSanitizer:
    """Provides path resolution and sanitization against directory traversal attacks."""

    @staticmethod
    def resolve_safe_path(base_dir: Union[str, Path], relative_path: str) -> Path:
        """
        Resolves a user-supplied relative path against a trusted base directory.
        Raises SecurityViolationException if the path attempts to escape base_dir.
        """
        if "\x00" in relative_path:
            raise SecurityViolationException("Null byte injection detected in path")

        base_path = Path(base_dir).resolve()
        
        # Normalize slashes and remove dangerous prefixes
        clean_rel = relative_path.replace("\\", "/").lstrip("/")
        
        target_path = (base_path / clean_rel).resolve()

        if not target_path.is_relative_to(base_path):
            raise SecurityViolationException(
                f"Path traversal attempt detected: '{relative_path}' resolves outside '{base_path}'"
            )

        return target_path

    @staticmethod
    def sanitize_filename(filename: str, prefix: str = "") -> str:
        """
        Sanitizes a filename by stripping illegal characters and returning a safe alphanumeric name.
        Preserves safe image extensions.
        """
        if "\x00" in filename:
            raise SecurityViolationException("Null byte injection detected in filename")

        # Extract extension
        path_obj = Path(filename)
        ext = path_obj.suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".exr"]:
            ext = ".png"

        # Sanitize stem
        stem = path_obj.stem
        clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", stem).strip("_")
        if not clean_stem:
            clean_stem = f"file_{uuid.uuid4().hex[:8]}"

        prefix_str = f"{prefix}_" if prefix else ""
        return f"{prefix_str}{clean_stem}{ext}"
