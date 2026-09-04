"""File Guard and Binary Magic Bytes Inspector."""
from typing import Union, BinaryIO

from src.domain.exceptions import SecurityViolationException

# Known safe image signatures (magic numbers)
MAGIC_SIGNATURES = {
    b"\xFF\xD8\xFF": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # WebP container starts with RIFF and has WEBP at offset 8
    b"\x76\x2F\x31\x01": "image/x-exr",  # OpenEXR magic
}

# Malicious signatures to explicitly flag
DANGEROUS_SIGNATURES = [
    (b"MZ", "DOS/PE Executable"),
    (b"\x7FELF", "ELF Executable"),
    (b"PK\x03\x04", "ZIP / Archive executable payload"),
    (b"#!/", "Shell Script"),
    (b"<?php", "PHP Script"),
    (b"<script", "HTML/JS Payload"),
]


class FileGuard:
    """Validates binary signatures, payload sizes, and dimensions."""

    @staticmethod
    def inspect_magic_bytes(header_bytes: bytes) -> str:
        """
        Inspects the leading bytes of a file payload to ensure it is a genuine safe image format.
        Raises SecurityViolationException for unsupported or dangerous file types.
        """
        if not header_bytes or len(header_bytes) < 4:
            raise SecurityViolationException("Payload is empty or too short for signature inspection")

        # First check dangerous signatures
        for sig, description in DANGEROUS_SIGNATURES:
            if header_bytes.startswith(sig):
                raise SecurityViolationException(
                    f"Unsupported or malicious file signature detected: {description}"
                )

        # Check JPEG
        if header_bytes.startswith(b"\xFF\xD8\xFF"):
            return "image/jpeg"

        # Check PNG
        if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"

        # Check WebP (RIFF....WEBP)
        if header_bytes.startswith(b"RIFF") and len(header_bytes) >= 12:
            if header_bytes[8:12] == b"WEBP":
                return "image/webp"

        # Check OpenEXR
        if header_bytes.startswith(b"\x76\x2F\x31\x01"):
            return "image/x-exr"

        raise SecurityViolationException("Unsupported or malicious file signature detected")

    @staticmethod
    def validate_payload_size(byte_length: int, max_allowed_bytes: int = 50 * 1024 * 1024) -> None:
        """Validates that payload byte length does not exceed maximum allowable threshold."""
        if byte_length > max_allowed_bytes:
            raise SecurityViolationException(
                f"Payload size exceeds maximum allowed limit ({byte_length} > {max_allowed_bytes} bytes)"
            )
