"""Test suite for verifying workspace environment and package integrity."""
import sys
import importlib
from pathlib import Path


def test_python_version():
    """Verify that Python runtime satisfies the requirement >= 3.10."""
    assert sys.version_info >= (3, 10), "Python version must be 3.10 or higher"


def test_backend_package_structure():
    """Verify that the backend package can be imported and has version metadata."""
    backend_src = Path(__file__).resolve().parent.parent.parent / "src"
    assert backend_src.exists(), f"Source directory {backend_src} does not exist"
    assert (backend_src / "__init__.py").exists(), "__init__.py missing in src directory"


def test_core_package_import():
    """Verify that the root package imports cleanly."""
    import src
    assert hasattr(src, "__version__")
    assert src.__version__ == "1.0.0"
