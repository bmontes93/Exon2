"""Domain Exceptions for EXON-FACE."""


class DomainException(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class DomainValidationError(DomainException):
    """Raised when an entity attribute violates domain invariants."""
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class FaceNotFoundException(DomainException):
    """Raised when no face is detected with sufficient confidence in an image."""
    def __init__(self, message: str = "No face detected in the provided image"):
        super().__init__(message, code="FACE_NOT_FOUND")


class LowSharpnessException(DomainException):
    """Raised when an image fails the Laplacian sharpness threshold."""
    def __init__(self, message: str = "Image sharpness is below acceptable threshold"):
        super().__init__(message, code="LOW_SHARPNESS")


class InvalidPoseException(DomainException):
    """Raised when head pose estimation produces invalid values."""
    def __init__(self, message: str = "Invalid head pose angles detected"):
        super().__init__(message, code="INVALID_POSE")


class VRAMExceededException(DomainException):
    """Raised when VRAM allocation exceeds safe thresholds (e.g. > 7.2 GB)."""
    def __init__(self, message: str = "GPU VRAM allocation exceeded safety threshold"):
        super().__init__(message, code="VRAM_EXCEEDED")


class SecurityViolationException(DomainException):
    """Raised when an action violates security constraints (e.g. path traversal)."""
    def __init__(self, message: str = "Security policy violation detected"):
        super().__init__(message, code="SECURITY_VIOLATION")
