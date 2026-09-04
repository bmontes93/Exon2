"""FastAPI Application Factory with DevSecOps Exception Handlers and Dependency Injection."""
from typing import Optional
from dataclasses import dataclass
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    DomainException,
    DomainValidationError,
    FaceNotFoundException,
    SecurityViolationException,
    VRAMExceededException,
)
from src.infrastructure.memory.vram_orchestrator import VRAMOrchestrator
from src.infrastructure.storage.local_storage_adapter import LocalStorageAdapter
from src.infrastructure.storage.sqlite_metadata_repo import SQLiteMetadataRepo
from src.infrastructure.adapters.pose_estimator_adapter import PoseEstimatorAdapter
from src.infrastructure.adapters.insightface_adapter import InsightFaceAdapter
from src.infrastructure.adapters.diffusers_renderer import DiffusersRendererAdapter
from src.infrastructure.adapters.bisenet_parser import BiSeNetParserAdapter
from src.infrastructure.adapters.wavelet_blender import WaveletBlenderAdapter
from src.infrastructure.adapters.codeformer_enhancer import CodeFormerEnhancerAdapter
from src.interfaces.api.sse_manager import SSEManager
from src.interfaces.api.routers.system_router import router as system_router
from src.interfaces.api.routers.dataset_router import router as dataset_router
from src.interfaces.api.routers.render_router import router as render_router


@dataclass
class ServiceContainer:
    """Dependency Injection container holding instantiated infrastructure services."""
    storage_adapter: LocalStorageAdapter
    metadata_repo: SQLiteMetadataRepo
    vram_orchestrator: VRAMOrchestrator
    face_detector: PoseEstimatorAdapter
    identity_extractor: InsightFaceAdapter
    neural_renderer: DiffusersRendererAdapter
    face_parser: BiSeNetParserAdapter
    image_blender: WaveletBlenderAdapter
    face_enhancer: CodeFormerEnhancerAdapter
    sse_manager: SSEManager


def create_app(
    models_dir: str = "D:/EXON2/models",
    datasets_dir: str = "datasets",
    outputs_dir: str = "outputs",
    db_path: str = "exon_metadata.db",
) -> FastAPI:
    """Factory creating configured FastAPI instance with Clean Architecture dependency container."""
    app = FastAPI(
        title="EXON-FACE Core API",
        version="1.0.0",
        description="High-Fidelity 3D-Aware Neural Face Synthesis & Swapping Engine",
    )

    # 1. Initialize Dependency Container
    storage = LocalStorageAdapter(models_dir=models_dir, datasets_dir=datasets_dir, outputs_dir=outputs_dir)
    repo = SQLiteMetadataRepo(db_path=db_path)
    vram = VRAMOrchestrator()
    detector = PoseEstimatorAdapter()
    embedder = InsightFaceAdapter()
    renderer = DiffusersRendererAdapter(model_cache_dir=models_dir)
    parser = BiSeNetParserAdapter()
    blender = WaveletBlenderAdapter()
    enhancer = CodeFormerEnhancerAdapter(model_cache_dir=models_dir)
    sse = SSEManager()

    app.state.container = ServiceContainer(
        storage_adapter=storage,
        metadata_repo=repo,
        vram_orchestrator=vram,
        face_detector=detector,
        identity_extractor=embedder,
        neural_renderer=renderer,
        face_parser=parser,
        image_blender=blender,
        face_enhancer=enhancer,
        sse_manager=sse,
    )

    # Mount Static Outputs for direct image rendering
    from fastapi.staticfiles import StaticFiles
    import os
    os.makedirs(outputs_dir, exist_ok=True)
    app.mount("/api/v1/outputs", StaticFiles(directory=outputs_dir), name="outputs")

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Global DevSecOps & Domain Exception Handlers
    @app.exception_handler(SecurityViolationException)
    async def security_exception_handler(request: Request, exc: SecurityViolationException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "SECURITY_VIOLATION", "message": str(exc)},
        )

    @app.exception_handler(FaceNotFoundException)
    async def face_not_found_handler(request: Request, exc: FaceNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "FACE_NOT_FOUND", "message": str(exc)},
        )

    @app.exception_handler(VRAMExceededException)
    async def vram_exceeded_handler(request: Request, exc: VRAMExceededException):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "VRAM_EXCEEDED", "message": str(exc)},
        )

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(request: Request, exc: DomainValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "VALIDATION_ERROR", "message": str(exc)},
        )

    @app.exception_handler(DomainException)
    async def generic_domain_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.code, "message": str(exc)},
        )

    # 4. Include Routers
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(dataset_router, prefix="/api/v1")
    app.include_router(render_router, prefix="/api/v1")

    return app
