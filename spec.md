# SPEC.MD — ESPECIFICACIÓN DE REQUISITOS DEL SISTEMA EXON-FACE

**Versión:** 1.0.0  
**Estado:** PROPUESTO PARA APROBACIÓN  
**Metodología:** Spec-Driven Development (SDD) & EARS Notation  
**Fecha:** 2026-09-02  

---

## 1. INTRODUCCIÓN Y ALCANCE

Este documento define la especificación técnica formal, los requisitos funcionales bajo notación EARS (*Easy Approach to Requirements Syntax*), las historias de usuario, los casos límite y los criterios de aseguramiento de calidad (QA) y seguridad para el sistema **EXON-FACE**.

---

## 2. REQUISITOS DEL SISTEMA EN NOTACIÓN EARS

### 2.1. Requisitos Ubicuos (Ubiquitous - Comportamiento continuo)
* **[REQ-UB-01]** El sistema *siempre* deberá registrar y aislar los estados de memoria GPU (CUDA VRAM) antes y después de cada etapa de inferencia para garantizar la estabilidad bajo el límite de 8 GB VRAM.
* **[REQ-UB-02]** El sistema *siempre* deberá validar la firma binaria (*magic numbers*) y las dimensiones máximas (máx. $8192 \times 8192$ px, 50 MB) de cualquier archivo cargado antes de almacenarlo o procesarlo.
* **[REQ-UB-03]** El sistema *siempre* deberá mantener desacoplados los servicios de Backend (FastAPI) y Frontend (Next.js), comunicándose únicamente mediante contratos tipados y endpoints REST/SSE.

### 2.2. Requisitos Dirigidos por Eventos (Event-driven - Disparados por acciones)
* **[REQ-EV-01]** **CUANDO** el usuario ingesta una carpeta o lista de imágenes de un sujeto, **EL SISTEMA DEBERÁ** detectar rostros, alinear landmarks, estimar la pose 3D ($Yaw, Pitch, Roll$), calcular el índice de nitidez laplaciana y generar un catálogo de embeddings indexados por ángulo.
* **[REQ-EV-02]** **CUANDO** el usuario solicite un render en **Modo Express (1-Click)** con una imagen destino, **EL SISTEMA DEBERÁ** seleccionar automáticamente el embedding del sujeto más cercano al ángulo del rostro destino, aplicar la síntesis generativa, transferir frecuencias y aplicar restauración facial con parámetros óptimos predeterminados.
* **[REQ-EV-03]** **CUANDO** el usuario solicite un render en **Modo Studio Pro**, **EL SISTEMA DEBERÁ** permitir la selección manual de ángulo fuente, ajuste de peso de identidad ($0.0 - 1.5$), edición de máscara de oclusión interactiva, ganancia de alta frecuencia Wavelet ($0.0 - 2.0$) y fidelidad de restauración ($0.0 - 1.0$).
* **[REQ-EV-04]** **CUANDO** se inicie un trabajo de renderizado, **EL SISTEMA DEBERÁ** transmitir el progreso y telemetría de cada etapa (Detección 3D $\rightarrow$ Matching $\rightarrow$ Fusión Neural $\rightarrow$ Segmentación $\rightarrow$ Wavelet $\rightarrow$ Restauración) a través de un canal Server-Sent Events (SSE).

### 2.3. Requisitos Basados en Estados (State-driven - Comportamiento condicional al estado)
* **[REQ-ST-01]** **MIENTRAS** el motor de inferencia esté ejecutando un pase pesado de difusión/síntesis en GPU, **EL SISTEMA DEBERÁ** bloquear la asignación de nuevos procesos de inferencia paralelos en la misma GPU y mantener en cola de espera secuencial los trabajos entrantes.
* **[REQ-ST-02]** **MIENTRAS** el usuario esté editando una máscara en el lienzo del Frontend, **EL SISTEMA DEBERÁ** renderizar la superposición visual de oclusión en tiempo real con capacidad de deshacer/rehacer y vista previa de corte.

### 2.4. Requisitos de Comportamiento no Deseado (Unwanted Behavior - Manejo de fallos)
* **[REQ-UW-01]** **SI** una imagen no contiene ningún rostro detectable o la confianza de detección es menor a $0.65$, **EL SISTEMA DEBERÁ** interrumpir el pipeline para dicha imagen y retornar un error `422 Unprocessable Entity` con el código `FACE_DETECTION_FAILED` y detalles visuales del fallo.
* **[REQ-UW-02]** **SI** el consumo de VRAM supera el umbral crítico del 90% ($7.2 \text{ GB}$ en RTX 3070), **EL SISTEMA DEBERÁ** invocar el vaciado preventivo de caché CUDA (`torch.cuda.empty_cache()`), forzar CPU-offloading de los modelos inactivos y, de ser necesario, reducir la resolución interna de trabajo sin abortar el proceso.
* **[REQ-UW-03]** **SI** el usuario intenta acceder o guardar archivos fuera de las rutas base configuradas mediante secuencias `../` o rutas relativas no autorizadas, **EL SISTEMA DEBERÁ** rechazar la solicitud con `403 Forbidden` y registrar una alerta de seguridad por intento de *Path Traversal*.

### 2.5. Requisitos Opcionales (Optional Features)
* **[REQ-OP-01]** **DONDE SEA POSIBLE**, el sistema ofrecerá exportación directa en formato `.exr` de 32 bits para integración con flujos de postproducción profesional (VFX / DaVinci Resolve / Nuke).

---

## 3. HISTORIAS DE USUARIO Y CRITERIOS DE ACEPTACIÓN (BDD / GHERKIN)

### US-01: Ingesta y Análisis Multi-Ángulo del Sujeto
* **Como:** Artista digital / Operador del sistema.
* **Quiero:** Cargar un lote de fotografías de un sujeto para que el sistema aprenda su estructura tridimensional y rasgos en diferentes perspectivas.
* **Para:** Obtener sustituciones faciales consistentes sin deformaciones en ángulos difíciles.

```gherkin
Scenario: Ingesta exitosa de dataset con detección de ángulos
  Given el usuario proporciona una carpeta con 15 imágenes válidas del sujeto
  When el backend ejecuta el caso de uso "ProcessSubjectDataset"
  Then el sistema detecta y recorta el rostro en cada imagen
  And calcula los ángulos Yaw, Pitch y Roll de cada pose
  And descarta automáticamente las fotos con nitidez laplaciana inferior a 100.0
  And genera un catálogo de embeddings faciales indexado por cuadrante de ángulo
  And retorna el resumen con el número de poses frontales, 3/4 y perfiles válidos.
```

---

### US-02: Síntesis Dual en Ángulo Extremo (Studio Pro)
* **Como:** Especialista en efectos visuales.
* **Quiero:** Reemplazar el rostro en una imagen destino con un ángulo de perfil pronunciado ($Yaw > 45^\circ$), ajustando la máscara de oclusión y la fidelidad de piel.
* **Para:** Lograr un resultado indistinguible de la realidad sin que el rostro parezca una calcomanía plana.

```gherkin
Scenario: Renderizado avanzado con oclusión y retención de textura
  Given una imagen destino con una persona de perfil y una mano sobre la mejilla
  And el sujeto pre-procesado con embeddings multi-ángulo disponibles
  When el usuario ajusta en Modo Studio:
    | Parámetro           | Valor |
    | Identity Weight     | 1.15  |
    | Wavelet High-Pass   | 1.30  |
    | CodeFormer Fidelity | 0.75  |
    | Occlusion Masking   | True  |
  And presiona el botón "Renderizar Síntesis Pro"
  Then el motor proyecta la pose 3D exacta del destino
  And genera la cara del sujeto preservando la línea de mandíbula en perspectiva
  And la máscara de oclusión preserva los dedos de la mano por encima del rostro sintetizado
  And la fusión Wavelet retiene el grano de película y poros originales
  And el visor interactivo muestra la comparación Split-Screen Antes/Después.
```

---

### US-03: Configuración Dinámica y Segura de Almacenamiento
* **Como:** Administrador del entorno local.
* **Quiero:** Definir las carpetas en mis discos duros dedicados para guardar modelos pesados, datasets y renders.
* **Para:** No saturar la unidad principal del sistema operativo manteniendo la seguridad de rutas.

```gherkin
Scenario: Validación y configuración de rutas de almacenamiento
  Given el usuario envía una ruta absoluta válida "D:/AI_Storage/EXON_Models"
  When el endpoint "/api/v1/system/config/paths" procesa la solicitud
  Then el sistema valida que el directorio sea accesible y tenga permisos de lectura/escritura
  And almacena la configuración de forma persistente en la base de datos local
  And responde con estado 200 OK y espacio libre disponible en disco.
```

---

## 4. CASOS LÍMITE Y CONDICIONES DE BORDE (EDGE CASES)

| ID | Caso Límite | Comportamiento Esperado del Sistema |
| :--- | :--- | :--- |
| **EC-01** | Ángulo extremo supercrítico ($Yaw > 80^\circ$, perfil puro donde un ojo es invisible). | El sistema activa el modo de proyección 3D asistida, usando el embedding del cuadrante lateral y aplicando inpainting condicional guiado por profundidad para reconstruir la anatomía oculta sin crear duplicidad de ojos. |
| **EC-02** | Oclusión severa (gafas oscuras, barbijos, mechones gruesos de pelo o micrófonos). | La red `BiSeNet Face Parser` genera una máscara de segmentación multi-clase. Las clases "eyewear", "hair" y "hand/object" se sustraen automáticamente del área de reemplazo para no pintar la piel sobre los accesorios. |
| **EC-03** | Múltiples rostros en la imagen destino. | El sistema detecta todas las caras, genera bounding boxes numerados con miniaturas y permite al usuario elegir a qué rostro específico aplicar el swap o aplicar swaps diferenciados por índice. |
| **EC-04** | Imagen destino de muy baja resolución ($< 256 \times 256 \text{ px}$). | El sistema realiza un super-muestreo guiado preliminar antes del alineamiento y limita la fuerza de restauración para no inventar artefactos irreales. |
| **EC-05** | Desconexión del cliente web durante una inferencia. | El proceso de backend concluye ordenadamente, guarda el resultado en el disco local y libera la memoria VRAM sin dejar hilos colgados. |

---

## 5. CRITERIOS DE QA, SEGURIDAD Y RENDIMIENTO

### 5.1. Seguridad y DevSecOps
1. **OWASP API Security Top 10**:
   * Blindaje contra inyecciones y deserialización insegura (prohibido `pickle.load`).
   * Desinfección de rutas con `Path.resolve()` contra ataques `../../etc/passwd` o `C:\Windows`.
   * Validación estricta de esquemas de entrada mediante `Pydantic v2`.
2. **Sanitización de Archivos**:
   * Lectura de los primeros 512 bytes de cada imagen para verificar firmas MIME reales (`image/jpeg`, `image/png`, `image/webp`).

### 5.2. Métricas de Rendimiento en NVIDIA RTX 3070 (8 GB VRAM)
* **Consumo Pico de VRAM:** $\le 7.0 \text{ GB}$ en cualquier etapa del pipeline.
* **Tiempo de Ingesta por Imagen:** $\le 0.4 \text{ s}$ por foto de dataset (detección + crop + pose 3D + embedding).
* **Tiempo de Renderizado Express:** $\le 4.5 \text{ s}$ por imagen ($1024 \times 1024$).
* **Tiempo de Renderizado Studio Pro (con Wavelet + Inpainting + CodeFormer):** $\le 9.0 \text{ s}$ por imagen ($2048 \times 2048$ export).

---
**Firma de Conformidad Requerida para avanzar al Paso 3 (`plan.md` y `tasks.md`):**  
*¿Apruebas la Especificación de Requisitos (`spec.md`) para proceder con el diseño del Plan de Arquitectura y el Desglose de Tareas de Implementación?*
