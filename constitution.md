# CONSTITUTION.MD — SISTEMA NEURAL DE SÍNTESIS FACIAL AVANZADA (EXON-FACE)

**Versión:** 1.0.0  
**Estado:** PROPUESTO PARA APROBACIÓN  
**Metodología:** Spec-Driven Development (SDD) & DevSecOps  
**Fecha:** 2026-09-01  

---

## 1. PROPÓSITO Y VISIÓN DEL SISTEMA
El sistema **EXON-FACE** es una plataforma de software de grado profesional diseñada para la síntesis, reconstrucción 3D y transferencia de identidad facial de ultra-alta fidelidad en imágenes estáticas. Su objetivo es superar las limitaciones de los métodos tradicionales de mapeo afín 2D (tipo Roop/ReActor) mediante una arquitectura híbrida que combina:
1. **Reconstrucción Geométrica 3D** (Malla 3DMM / FLAME / Estimación de Pose $Yaw, Pitch, Roll$).
2. **Modelado Generativo de Identidad Multi-Ángulo** (SDXL / InstantID / IP-Adapter-FaceID cuantizado / LoRA).
3. **Preservación de Frecuencias y Textura de Piel** (Wavelet Frequency Blending y corrección en espacio LAB).
4. **Segmentación y Manejo de Oclusiones** (BiSeNet / SAM).

---

## 2. PRINCIPIOS INNEGOCIABLES (CORE TENETS)

1. **Cero Monolitos (Desacoplamiento Estricto)**:
   * El **Frontend** (Next.js) y el **Backend** (FastAPI) residen en proyectos y procesos independientes.
   * La comunicación se realiza exclusivamente vía contratos tipados (OpenAPI / JSON Schema) sobre HTTP REST y WebSockets/SSE para telemetría y progreso de inferencia en tiempo real.
2. **Arquitectura Limpia (Clean Architecture / Hexagonal)**:
   * El dominio de visión por computador y los algoritmos de síntesis están aislados de los frameworks de transporte (FastAPI) y de los motores de persistencia.
   * La infraestructura de IA (PyTorch, ONNX Runtime, CUDA) se expone a los casos de uso mediante interfaces e inyección de dependencias.
3. **Respeto Estricto al Presupuesto de Hardware (VRAM 8GB Cap)**:
   * El sistema está diseñado específicamente para operar sin desbordamientos de memoria (*Out of Memory - OOM*) en una **NVIDIA RTX 3070 con 8 GB VRAM**.
   * Todo pipeline de inferencia debe implementar:
     * Carga secuencial y descarga explícita de modelos con recolección de basura CUDA (`torch.cuda.empty_cache()`).
     * Cuantización FP8 / INT8 o SDPA (Scaled Dot-Product Attention) y xFormers.
     * CPU Offloading para etapas que no requieran GPU en paralelo.
4. **Seguridad por Diseño (Security by Design / DevSecOps)**:
   * Ningún archivo se procesa sin validación estricta de tipo MIME, firma de cabecera binaria (*magic numbers*) y límites de resolución/tamaño.
   * Protección integral contra ataques de *Path Traversal*, descompresión de bombas de compresión y ejecución de código malicioso en pesos de modelos (exclusivo uso de formatos seguros `.safetensors` y `.onnx`, prohibiendo `pickle`).
5. **Doble Modalidad de Operación (Dual Mode UX)**:
   * **Modo Express (1-Click)**: Pipeline automatizado de selección de mejor ángulo, alineación 3D, síntesis y restauración.
   * **Modo Studio Pro**: Control milimétrico de pesos de identidad, edición manual de máscaras de oclusión, balance de frecuencias (*Wavelet*) y parámetros de restauración facial (*CodeFormer fidelity slider*).

---

## 3. STACK TECNOLÓGICO Y MATRIZ DE COMPONENTES

### 3.1. Backend (Motor de Inferencia y API)
* **Lenguaje:** Python 3.10+ / 3.11
* **Framework Web:** FastAPI (Asíncrono, Pydantic v2, Uvicorn)
* **Motor de Deep Learning:** PyTorch 2.x (CUDA 12.x), torchvision, torchaudio
* **Inferencia Ligera & Visión Clásica:** ONNX Runtime GPU (TensorRT Execution Provider opcional), OpenCV (headless), NumPy, Scipy (Wavelets)
* **Modelos de Visión & Difusión:**
  * *Detección & Pose 3D:* RetinaFace / SCRFD / 3DDFA-V2 / MediaPipe Face Mesh
  * *Embeddings de Identidad:* InsightFace (ArcFace / AdaFace)
  * *Generación & Fusión:* Hugging Face Diffusers (SDXL + InstantID / IP-Adapter FaceID Plus v2 con cuantización y CPU offload)
  * *Segmentación Facial:* BiSeNet Face Parsing / MobileSAM
  * *Restauración Facial:* CodeFormer / GPEN (control de fidelidad ajustable)
* **Telemetría & Eventos:** Server-Sent Events (SSE) / WebSockets para reporte de progreso fotograma a fotograma / etapa a etapa.

### 3.2. Frontend (Interfaz de Usuario)
* **Framework:** Next.js 14+ (App Router, React 18/19, TypeScript estricto)
* **Estilos:** Tailwind CSS v3 / v4
* **Diseño Visual:** **Neo-Brutalism Industrial / Cyber-Tech**:
  * *Bordes:* Gruesos (`border-2 border-black` o `border-slate-900`), sombras duras sin difuminar (`shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]`).
  * *Paleta de Color Primaria:*
    * Fondo: Slate Profundo / Negro Carbón (`#0F172A` / `#050505`) y Blanco Puro (`#FFFFFF`).
    * Acentos de Alto Impacto: Naranja Neón Industrial (`#FF5500`), Lima Eléctrico (`#CCFF00`) y Cian Cibernético (`#00F0FF`).
  * *Tipografía:* Monoespaciada y Sans-Serif geométrica (JetBrains Mono / Space Grotesk / Inter).
* **Gestión de Estado & Fetching:** TanStack Query (React Query) + Zustand para el estado del estudio y parámetros de renderizado.
* **Componentes Interactivos:** Comparador interactivo Antes/Después (Split-screen slider), visualizador de nubes de puntos 3D / landmarks faciales en Canvas/Three.js y lienzo de dibujo de máscaras.

### 3.3. Almacenamiento y Sistema de Archivos
* **Rutas Configurables por el Usuario:** El usuario define dinámicamente en la interfaz o variables de entorno:
  * Directorio de Modelos / Checkpoints (`MODEL_CACHE_DIR`).
  * Directorio de Datasets de Sujetos (`DATASET_DIR`).
  * Directorio de Salidas y Renders (`OUTPUT_DIR`).
* **Base de Datos / Indexación Local:** SQLite con WAL mode o DuckDB para indexar metadatos de sujetos, ángulos precalculados y registros de renders históricos sin dependencias externas pesadas.

---

## 4. ESTÁNDARES DE SEGURIDAD (DEVSECOPS)

1. **Blindaje de Archivos y Rutas (Path Traversal & Injection Defense)**:
   * Las rutas de entrada/salida se resuelven mediante `pathlib.Path.resolve()` validando que permanezcan estrictamente dentro del árbol permitido configurado.
   * Nombres de archivos saneados con hashes criptográficos (SHA-256) para evitar colisiones y caracteres de inyección (`../`, `\`, null bytes).
2. **Validación Estricta de Carga Útil (Payload Validation)**:
   * Validación de encabezados binarios con `python-magic` / comprobación de cabeceras JPEG, PNG, WEBP.
   * Límite de carga útil máximo por archivo (ej. 50 MB) y dimensión máxima de píxeles (ej. 8192x8192) para prevenir ataques de denegación de servicio por consumo de RAM (*Decompression Bombs*).
3. **Protección de Memoria GPU**:
   * Context Managers para control estricto de VRAM con `with torch.inference_mode():` y liberación determinista de memoria tras cada paso.
4. **Cero Dependencias de Formatos Vulnerables**:
   * Prohibición absoluta de carga de checkpoints serializados con `pickle` inseguro. Únicamente se admiten archivos `.safetensors`, `.onnx` y configuraciones JSON.

---

## 5. REGLAS DE ARQUITECTURA LIMPIA

El Backend respetará la siguiente separación de capas:

```
backend/
├── src/
│   ├── domain/               # Entidades de negocio, Enums, Value Objects (Independientes de frameworks)
│   │   ├── models/           # FaceIdentity, Landmark3D, HeadPose, RenderJob, MaskLayer
│   │   └── exceptions/       # DomainExceptions (FaceNotFoundException, OOMRiskException)
│   ├── application/          # Casos de uso y orquestación
│   │   ├── use_cases/        # ProcessSubjectDataset, Estimate3DPose, ExecuteDualFaceSwap
│   │   └── interfaces/       # Contratos/Puertos para detectores, generadores, almacenamiento
│   ├── infrastructure/       # Implementación de adaptadores y modelos IA
│   │   ├── ai_engines/       # Adaptadores PyTorch/Diffusers, InsightFace, CodeFormer, 3DDFA
│   │   ├── storage/          # LocalFileSystemAdapter, MetadataRepository
│   │   └── memory_manager/   # CUDA VRAM Sequential Orchestrator
│   └── interfaces/           # Capa de transporte y controladores
│       ├── api/              # Endpoints FastAPI (REST & SSE)
│       └── schemas/          # Esquemas DTO de Pydantic v2
└── tests/                    # Suites TDD (Unitarios, Integración, Seguridad)
```

El Frontend respetará la separación de responsabilidades:

```
frontend/
├── src/
│   ├── app/                  # Rutas Next.js (App Router)
│   ├── components/           # UI Components (Neo-brutalism design system)
│   │   ├── ui/               # Botones, Sliders, Cards, Badges de estilo brutalista
│   │   ├── studio/           # Editor Pro, Canvas de Máscaras, Comparador Split-View
│   │   └── dataset/          # Gestor de galería de fotos de sujeto y análisis de ángulos
│   ├── hooks/                # Hooks personalizados (useRenderPipeline, useSSEProgress)
│   ├── services/             # Clientes de API tipados (Axios / Fetch + TypeScript)
│   └── stores/               # Estado global Zustand (configuración de rutas, modo de render)
```

---

## 6. CRITERIOS DE ACEPTACIÓN DE ESTA CONSTITUCIÓN

Esta constitución regirá todo el ciclo de vida del proyecto. Ningún cambio de código o arquitectura podrá contravenir los principios aquí establecidos sin una revisión y actualización explícita de este documento.

---
**Firma de Conformidad Requerida para avanzar al Paso 2 (`spec.md`):**  
*¿Apruebas la Constitución del Sistema EXON-FACE para proceder con la redacción de la especificación funcional detallada (`spec.md`)?*
