"""Security test suite for Path Sanitization, Magic Bytes validation, and Payload Guard."""
import io
import pytest
from pathlib import Path

from src.domain.exceptions import SecurityViolationException
from src.infrastructure.security.path_sanitizer import PathSanitizer
from src.infrastructure.security.file_guard import FileGuard


class TestPathSanitizer:
    def test_safe_path_resolution(self, tmp_path):
        base_dir = tmp_path / "safe_storage"
        base_dir.mkdir()
        
        safe_result = PathSanitizer.resolve_safe_path(base_dir=base_dir, relative_path="images/sub/photo.png")
        assert safe_result.is_relative_to(base_dir)

    def test_path_traversal_detection_parent_directory(self, tmp_path):
        base_dir = tmp_path / "safe_storage"
        base_dir.mkdir()

        with pytest.raises(SecurityViolationException) as exc_info:
            PathSanitizer.resolve_safe_path(base_dir=base_dir, relative_path="../../etc/passwd")
        assert "Path traversal attempt detected" in str(exc_info.value)

    def test_path_traversal_windows_backslashes(self, tmp_path):
        base_dir = tmp_path / "safe_storage"
        base_dir.mkdir()

        with pytest.raises(SecurityViolationException) as exc_info:
            PathSanitizer.resolve_safe_path(base_dir=base_dir, relative_path="..\\..\\Windows\\System32")
        assert "Path traversal attempt detected" in str(exc_info.value)

    def test_null_byte_injection(self, tmp_path):
        base_dir = tmp_path / "safe_storage"
        base_dir.mkdir()

        with pytest.raises(SecurityViolationException):
            PathSanitizer.resolve_safe_path(base_dir=base_dir, relative_path="image.png\x00.exe")

    def test_sanitize_filename(self):
        unsafe_name = "my ../weird * <file>: name?.png"
        safe_name = PathSanitizer.sanitize_filename(unsafe_name)
        assert "/" not in safe_name
        assert "\\" not in safe_name
        assert ".." not in safe_name
        assert safe_name.endswith(".png")


class TestFileGuard:
    def test_valid_jpeg_magic_bytes(self):
        # JPEG header: FF D8 FF E0
        jpeg_header = b"\xFF\xD8\xFF\xE0" + b"\x00" * 50
        mime = FileGuard.inspect_magic_bytes(jpeg_header)
        assert mime == "image/jpeg"

    def test_valid_png_magic_bytes(self):
        # PNG header: 89 50 4E 47 0D 0A 1A 0A
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        mime = FileGuard.inspect_magic_bytes(png_header)
        assert mime == "image/png"

    def test_valid_webp_magic_bytes(self):
        # WEBP: RIFF + 4 bytes size + WEBP
        webp_header = b"RIFF\x20\x00\x00\x00WEBP" + b"\x00" * 50
        mime = FileGuard.inspect_magic_bytes(webp_header)
        assert mime == "image/webp"

    def test_fake_extension_executable_rejected(self):
        # DOS/PE header: MZ
        exe_header = b"MZ\x90\x00" + b"\x00" * 50
        with pytest.raises(SecurityViolationException) as exc_info:
            FileGuard.inspect_magic_bytes(exe_header)
        assert "Unsupported or malicious file signature" in str(exc_info.value)

    def test_payload_size_limit_exceeded(self):
        max_bytes = 1024 * 1024  # 1 MB limit
        large_payload = b"\x00" * (max_bytes + 1)
        with pytest.raises(SecurityViolationException) as exc_info:
            FileGuard.validate_payload_size(len(large_payload), max_allowed_bytes=max_bytes)
        assert "Payload size exceeds maximum allowed limit" in str(exc_info.value)
