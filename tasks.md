# TASKS.MD — DESGLOSE DE TAREAS DE IMPLEMENTACIÓN TDD (EXON-FACE)

**Versión:** 1.0.0  
**Metodología:** Test-Driven Development (TDD) & Spec-Driven Development (SDD)  
**Estimación por tarea:** 20 a 30 minutos  
**Fecha de Inicio:** 2026-09-02  

---

## CONVENCIONES DE ESTADO
- `[ ]` **PENDIENTE**
- `[>]` **EN PROGRESO**
- `[X]` **COMPLETADA**
- `[!]` **BLOQUEADA**

---

## FASE 1: ANDAMIAJE DEL PROYECTO, HERRAMIENTAS Y ENTORNO

- [X] **TASK-01: Estructura del Workspace y Configuración de Herramientas**
  * **Objetivo:** Inicializar las raíces `backend/` y `frontend/`, crear configuraciones de calidad de código (`pyproject.toml`, `pytest.ini`, `.gitignore`, `tsconfig.json`).
  * **Pruebas (TDD):** Test de verificación de entorno y paquetes (`test_environment.py`).
  * **Archivos a crear:** `backend/pyproject.toml`, `backend/pytest.ini`, `.gitignore`.
  * **Tiempo estimado:** 20 min.

---

## FASE 2: NÚCLEO DE DOMINIO, SEGURIDAD Y GESTIÓN DE VRAM (BACKEND)

- [X] **TASK-02: Entidades de Dominio, Value Objects y Excepciones**
  * **Objetivo:** Definir las clases de datos puras: `FaceCrop`, `HeadPose3D`, `IdentityProfile`, `RenderJob`, `AngleQuadrant` y excepciones de dominio.
  * **Pruebas (TDD):** `tests/unit/test_domain_entities.py` (validaciones de inmutabilidad, cálculo de cuadrantes de ángulo, límites de valores).
  * **Archivos a crear:** `backend/src/domain/entities.py`, `backend/src/domain/enums.py`, `backend/src/domain/exceptions.py`.
  * **Tiempo estimado:** 25 min.

- [X] **TASK-03: Módulo de Seguridad y Sanitización (DevSecOps Guard)**
  * **Objetivo:** Implementar el validador de rutas seguras (anti *Path Traversal*), verificación de firmas binarias (*Magic Bytes*) y límites de archivo.
  * **Pruebas (TDD):** `tests/security/test_security_sanitization.py` (intentos de inyección `../`, payloads binarios corruptos, extensiones falsificadas).
  * **Archivos a crear:** `backend/src/infrastructure/security/file_guard.py`, `backend/src/infrastructure/security/path_sanitizer.py`.
  * **Tiempo estimado:** 25 min.

- [X] **TASK-04: Orquestador Secuencial de Memoria GPU (VRAM Orchestrator)**
  * **Objetivo:** Crear el manejador de contexto y gestor de ciclo de vida de modelos para mantener el uso de VRAM $\le 7.0 \text{ GB}$ con recolección de basura determinista.
  * **Pruebas (TDD):** `tests/unit/test_vram_orchestrator.py` (adquisición de slots, limpieza forzada, detección de sobregiro simulado).
  * **Archivos a crear:** `backend/src/infrastructure/memory/vram_orchestrator.py`.
  * **Tiempo estimado:** 30 min.

- [X] **TASK-05: Adaptador de Almacenamiento Local e Indexación SQLite**
  * **Objetivo:** Implementar la persistencia de datasets, imágenes procesadas y metadatos de poses/embeddings con SQLite (WAL mode).
  * **Pruebas (TDD):** `tests/unit/test_storage_adapter.py` (CRUD de perfiles de sujeto, lectura y escritura segura en carpetas configuradas).
  * **Archivos a crear:** `backend/src/infrastructure/storage/local_storage_adapter.py`, `backend/src/infrastructure/storage/sqlite_metadata_repo.py`.
  * **Tiempo estimado:** 25 min.

---

## FASE 3: ADAPTADORES DE VISIÓN E IA (INFRAESTRUCTURA)

- [X] **TASK-06: Módulo de Detección 3D y Estimación de Pose (SCRFD / 3DDFA)**
  * **Objetivo:** Implementar el extractor de landmarks faciales, cálculo de $Yaw, Pitch, Roll$ y filtro de nitidez laplaciana.
  * **Pruebas (TDD):** `tests/unit/test_pose_estimator.py` (clasificación de poses en ángulos conocidos, descarte de imágenes borrosas).
  * **Archivos a crear:** `backend/src/infrastructure/adapters/pose_estimator_adapter.py`.
  * **Tiempo estimado:** 30 min.

- [X] **TASK-07: Módulo de Embeddings de Identidad Multi-Ángulo (ArcFace)**
  * **Objetivo:** Extraer vectores de identidad de 512 dimensiones normalizados y calcular similitud coseno entre diferentes ángulos.
  * **Pruebas (TDD):** `tests/unit/test_identity_embedder.py` (consistencia de embeddings, matching de mejor ángulo).
  * **Archivos a crear:** `backend/src/infrastructure/adapters/insightface_adapter.py`.
  * **Tiempo estimado:** 25 min.

- [X] **TASK-08: Fusión de Frecuencias Wavelet y Coincidencia de Color LAB**
  * **Objetivo:** Implementar descomposición de alta/baja frecuencia con Transformada Wavelet 2D para transferir la cara sin perder poros, arrugas o grano de película.
  * **Pruebas (TDD):** `tests/unit/test_wavelet_blender.py` (fusión de texturas, preservación de histograma de color).
  * **Archivos a crear:** `backend/src/infrastructure/adapters/wavelet_blender.py`.
  * **Tiempo estimado:** 30 min.

- [X] **TASK-09: Segmentación de Oclusiones y Restauración Facial (BiSeNet & CodeFormer)**
  * **Objetivo:** Adaptadores para generación de máscaras de exclusión (pelo, manos, gafas) y mejora de detalles faciales ajustada por slider.
  * **Pruebas (TDD):** `tests/unit/test_face_parser_restorer.py` (generación de máscaras binarias, aplicación de pesos de fidelidad).
  * **Archivos a crear:** `backend/src/infrastructure/adapters/bisenet_parser.py`, `backend/src/infrastructure/adapters/codeformer_enhancer.py`.
  * **Tiempo estimado:** 30 min.

- [X] **TASK-10: Motor de Generación y Síntesis Neuronal (Diffusers / InstantID Core)**
  * **Objetivo:** Implementar el motor generativo de síntesis facial con soporte de cuantización, atención SDPA y carga controlada por VRAM.
  * **Pruebas (TDD):** `tests/unit/test_neural_renderer.py` (ejecución de pipeline con mocks y verificación de contratos).
  * **Archivos a crear:** `backend/src/infrastructure/adapters/diffusers_renderer.py`.
  * **Tiempo estimado:** 30 min.

---

## FASE 4: CASOS DE USO Y ORQUESTACIÓN (APPLICATION LAYER)

- [X] **TASK-11: Caso de Uso: Ingesta y Catálogo de Dataset de Sujeto**
  * **Objetivo:** Orquestar el procesamiento en lote de fotos de un sujeto: filtrado por calidad $\rightarrow$ detección 3D $\rightarrow$ embeddings $\rightarrow$ guardado en catálogo.
  * **Pruebas (TDD):** `tests/unit/test_use_case_ingest.py`.
  * **Archivos a crear:** `backend/src/application/use_cases/ingest_subject_dataset.py`.
  * **Tiempo estimado:** 25 min.

- [X] **TASK-12: Caso de Uso: Ejecución de Síntesis Dual (Express & Studio Pro)**
  * **Objetivo:** Orquestar el pipeline completo con telemetría de eventos paso a paso y retorno de artefactos de imagen y metadatos.
  * **Pruebas (TDD):** `tests/unit/test_use_case_synthesis.py`.
  * **Archivos a crear:** `backend/src/application/use_cases/execute_face_synthesis.py`.
  * **Tiempo estimado:** 30 min.

---

## FASE 5: API REST, TELEMETRÍA SSE Y CONTRATOS (INTERFACES)

- [X] **TASK-13: Esquemas DTO (Pydantic v2) y Gestor de Telemetría SSE**
  * **Objetivo:** Definir contratos estrictos de entrada/salida y el canal de streaming de progreso.
  * **Pruebas (TDD):** `tests/unit/test_schemas_and_sse.py`.
  * **Archivos a crear:** `backend/src/interfaces/schemas/*.py`, `backend/src/interfaces/api/sse_manager.py`.
  * **Tiempo estimado:** 20 min.

- [X] **TASK-14: Routers FastAPI y Middlewares de Seguridad**
  * **Objetivo:** Montar los endpoints `/api/v1/dataset`, `/api/v1/render`, `/api/v1/system` con middlewares CORS y manejo global de excepciones de dominio.
  * **Pruebas (TDD):** `tests/integration/test_api_endpoints.py`.
  * **Archivos a crear:** `backend/src/interfaces/api/routers/*.py`, `backend/src/interfaces/api/app.py`.
  * **Tiempo estimado:** 25 min.

---

## FASE 6: FRONTEND NEO-BRUTALIST (NEXT.JS + TAILWIND)

- [X] **TASK-15: Inicialización de Next.js y Sistema de Diseño Neo-Brutalist**
  * **Objetivo:** Configurar proyecto Next.js con Tailwind, paleta (Slate, Naranja Neón, Lima Eléctrico, Cian) y componentes base (`BrutalButton`, `BrutalCard`, `BrutalSlider`, `BrutalBadge`).
  * **Archivos a crear:** `frontend/src/components/ui/*.tsx`, `frontend/src/app/layout.tsx`, `frontend/tailwind.config.ts`.
  * **Tiempo estimado:** 30 min.

- [X] **TASK-16: Módulo de Gestión de Datasets y Visualizador de Ángulos 3D**
  * **Objetivo:** Galería interactiva para subir fotos de sujeto, ver índice de nitidez y distribución de poses en cuadrantes.
  * **Archivos a crear:** `frontend/src/app/dataset/page.tsx`, `frontend/src/components/dataset/*.tsx`.
  * **Tiempo estimado:** 25 min.

- [X] **TASK-17: Módulo Studio Pro (Canvas de Máscaras, Sliders y Comparador Split-Screen)**
  * **Objetivo:** Vista interactiva del estudio con editor de máscaras de oclusión, controles de parámetros y comparador antes/después deslizante.
  * **Archivos a crear:** `frontend/src/app/studio/page.tsx`, `frontend/src/components/studio/*.tsx`.
  * **Tiempo estimado:** 30 min.

- [X] **TASK-18: Integración de Telemetría SSE y Consola de Estado en Tiempo Real**
  * **Objetivo:** Conectar el hook `useSSEProgress` con el backend para mostrar la barra de progreso reactiva y los logs de inferencia.
  * **Archivos a crear:** `frontend/src/hooks/useSSEProgress.ts`, `frontend/src/components/studio/TelemetryConsole.tsx`.
  * **Tiempo estimado:** 20 min.

---

## FASE 7: VERIFICACIÓN E2E, BLINDAJE DEVSECOPS Y OPTIMIZACIÓN

- [X] **TASK-19: Suite de Pruebas de Seguridad y Resiliencia E2E**
  * **Objetivo:** Ejecutar suite completa contra inyecciones de payloads, simulación de estrés de VRAM y pruebas de flujo completo.
  * **Archivos a crear:** `backend/tests/e2e/test_full_pipeline_flow.py`.
  * **Tiempo estimado:** 25 min.

---
**Documento listo para ser aprobado para iniciar la Fase 3 (Implementación TDD Tarea por Tarea).**
