# 🚀 GUÍA MAESTRA DE RESPALDO Y RESTAURACIÓN POST-FORMATEO
## Proyecto: EXON-FACE (EXON 2.0) — Sistema de Síntesis Facial 3D y Restauración Canónica

> **IMPORTANTE**: Guarda una copia de este archivo en un pendrive USB o en la nube antes de formatear tu computadora. Contiene todas las credenciales, enlaces, versiones exactas y pasos para dejar el sistema 100% operativo en 15 minutos en un Windows limpio.

---

## 1. 🔑 DATOS CLAVE Y CREDENCIALES DEL PROYECTO

| Concepto | Valor / Enlace |
| :--- | :--- |
| **Repositorio GitHub** | `https://github.com/bmontes93/Exon2.git` |
| **Rama Principal** | `main` |
| **Usuario Git** | `Bryan Montes` |
| **Email Git** | `bmontesr930620@gmail.com` |
| **Ubicación en Disco** | `D:\EXON2` |
| **Ubicación Fotos/Videos Masiel** | `Z:\MASIEL FOTOS\julio\` |
| **URL Estudio Web Local** | `http://localhost:3000/studio` |
| **URL API REST / Swagger Docs** | `http://127.0.0.1:8000/docs` |
| **Puerto Backend** | `8000` |
| **Puerto Frontend** | `3000` |

---

## 2. 📦 CHECKLIST PREVIO: QUÉ COPIAR A UN DISCO EXTERNO / USB ANTES DE FORMATEAR

Si formateas solo el disco `C:\` (Windows), los discos `D:\` y `Z:\` se conservarán intactos. Sin embargo, si vas a formatear todo o deseas máxima seguridad, **copia estos 4 elementos a tu disco USB**:

1. [ ] **Carpeta de Modelos (`D:\EXON2\models\`)** (~15 GB)  
   *Contiene los pesos neuronales (`inswapper_128.onnx`, `GPEN-BFR-512.onnx`, `buffalo_l`, etc.). Si la respaldas, te ahorras horas de descarga.*
2. [ ] **Base de Datos SQLite (`D:\EXON2\backend\exon_metadata.db`)** (~1 MB)  
   *Contiene el perfil biométrico de Masiel curado y clasificado en los 7 cuadrantes 3D a partir de 137 fotos y fotogramas de video.*
3. [ ] **Carpeta de Fotos/Videos Fuente (`Z:\MASIEL FOTOS\julio\`)**  
   *Tus videos `.mp4` y fotos originales de Masiel.*
4. [ ] **Este archivo Markdown (`GUIA_RESTAURACION_POST_FORMATEO.md`)**

---

## 3. 🖥️ ESPECIFICACIONES DE HARDWARE Y DRIVERS (PC ACTUAL)

* **Tarjeta Gráfica (GPU)**: NVIDIA GeForce RTX 3070 (8 GB VRAM GDDR6).
* **Driver NVIDIA**: Versión 550+ o 621+ con soporte para CUDA 12.1+ / 12.4.
* **Versión de CUDA Soportada**: CUDA 12.1 / 12.4.

---

## 4. 🛠️ INSTALACIÓN DE SOFTWARE BASE EN WINDOWS LIMPIO

Una vez que Windows esté recién instalado:

### Paso 1: Instalar Driver de NVIDIA
1. Descarga el driver GeForce Game Ready para RTX 3070 desde:  
   👉 [https://www.nvidia.com/Download/index.aspx](https://www.nvidia.com/Download/index.aspx)
2. Instálalo y reinicia si el instalador lo solicita.
3. Verifica abriendo un terminal (CMD o PowerShell):
   ```cmd
   nvidia-smi
   ```
   *(Debe mostrar tu RTX 3070 y CUDA Version 12.x)*

---

### Paso 2: Instalar Git para Windows
* Descargar desde: 👉 [https://git-scm.com/download/win](https://git-scm.com/download/win)
* Configura tus credenciales tras instalarlo:
  ```cmd
  git config --global user.name "Bryan Montes"
  git config --global user.email "bmontesr930620@gmail.com"
  ```

---

### Paso 3: Instalar Node.js (LTS)
* Descargar Node.js v20 o v22 (LTS) desde: 👉 [https://nodejs.org/](https://nodejs.org/)
* Verifica en consola:
  ```cmd
  node -v
  npm -v
  ```

---

### Paso 4: Instalar Python 3.11 y uv
> ⚠️ **CRÍTICO**: PyTorch, InsightFace y ONNXRuntime-GPU son estables en **Python 3.11**. NO instales Python 3.12 ni 3.14 para este entorno de IA.

1. Descarga e instala **Python 3.11.9 (64-bit)**:  
   👉 [https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)  
   *(Asegúrate de marcar la casilla "Add python.exe to PATH" durante la instalación).*

2. Instala **uv** (el gestor ultrarrápido de paquetes Python):
   Abre PowerShell y ejecuta:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

---

## 5. ⚡ RESTAURACIÓN PASO A PASO DEL PROYECTO (15 MINUTOS)

### Paso A: Clonar el Repositorio (si formateaste el disco D)
Si tu disco `D:` se formateó, abre CMD y clónalo:
```cmd
cd /d D:\
git clone https://github.com/bmontes93/Exon2.git EXON2
cd D:\EXON2
```
*(Si tu disco `D:` no fue tocado, entra directo a `cd /d D:\EXON2` y ejecuta `git pull origin main`).*

---

### Paso B: Restaurar Archivos Respaldados del USB
Copia desde tu memoria USB:
1. Pega la carpeta `models\` dentro de `D:\EXON2\models\`.
2. Pega el archivo `exon_metadata.db` dentro de `D:\EXON2\backend\exon_metadata.db`.
3. Pega la carpeta de fotos y videos en `Z:\MASIEL FOTOS\julio\` (si formateaste Z).

---

### Paso C: Crear el Entorno Virtual Python con Soporte CUDA
Abre CMD y ejecuta:
```cmd
cd /d D:\EXON2\backend

:: 1. Crear entorno virtual con Python 3.11
uv venv .venv_cuda --python 3.11

:: 2. Instalar PyTorch con aceleración CUDA 12.1
uv pip install --python .venv_cuda\Scripts\python.exe torch torchvision --index-url https://download.pytorch.org/whl/cu121

:: 3. Instalar ONNXRuntime y librerías de visión y servidor
uv pip install --python .venv_cuda\Scripts\python.exe onnxruntime==1.19.2 insightface opencv-python fastapi uvicorn pydantic scipy scikit-image requests tqdm pillow albumentations
```

---

### Paso D: Instalar Dependencias del Frontend (Next.js)
Abre CMD y ejecuta:
```cmd
cd /d D:\EXON2\frontend
npm install
```

---

### Paso E: Crear Accesos Directos de 1-Clic en el Escritorio
Copia los siguientes dos archivos desde `D:\EXON2` a tu Escritorio (`C:\Users\<TuUsuario>\Desktop`):
* `D:\EXON2\EJECUTAR_EXON_FACE.bat`
* `D:\EXON2\DETENER_EXON_FACE.bat`

¡Listo! Al hacer doble clic en **`EJECUTAR_EXON_FACE.bat`**, la aplicación se encenderá sola y abrirá el estudio web en tu navegador.

---

## 6. 🌐 CATÁLOGO DE MODELOS Y ENLACES DE DESCARGA DIRECTA

Si por alguna razón no tienes la copia de respaldo de la carpeta `models/`, estos son los enlaces directos de cada modelo:

| Modelo | Archivo Destino | URL de Descarga Directa | Tamaño |
| :--- | :--- | :--- | :--- |
| **InSwapper 128 ONNX** | `models/swappers/inswapper_128.onnx` | [Descargar de HuggingFace](https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx) | 528 MB |
| **GPEN-BFR-512 ONNX** | `models/codeformer/GPEN-BFR-512.onnx` | [Descargar de HuggingFace ReActor](https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GPEN-BFR-512.onnx) | 271 MB |
| **Buffalo_L (Pack Completo)** | `models/models/buffalo_l.zip` | [Descargar de InsightFace Releases](https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip) | 275 MB |
| **SCRFD 10G Detection** | `models/models/buffalo_l/det_10g.onnx` | [Descargar de HuggingFace](https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/det_10g.onnx) | 16 MB |
| **ArcFace w600k Embedding** | `models/models/buffalo_l/w600k_r50.onnx` | [Descargar de HuggingFace](https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/w600k_r50.onnx) | 166 MB |
| **Landmarks 2D 106** | `models/models/buffalo_l/2d106det.onnx` | [Descargar de HuggingFace](https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/2d106det.onnx) | 4.8 MB |
| **Landmarks 3D 68** | `models/models/buffalo_l/1k3d68.onnx` | [Descargar de HuggingFace](https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/1k3d68.onnx) | 137 MB |
| **Gender & Age** | `models/models/buffalo_l/genderage.onnx` | [Descargar de HuggingFace](https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/genderage.onnx) | 1.3 MB |

> **Descarga automática por script**: También puedes ejecutar:  
> `D:\EXON2\backend\.venv_cuda\Scripts\python.exe D:\EXON2\backend\scripts\download_models.py`  
> y descargará los modelos principales automáticamente.

---

## 7. 🧪 SCRIPTS ÚTILES DE PRUEBA Y CURACIÓN

Todos los scripts se ejecutan desde `D:\EXON2`:

```cmd
# 1. Probar el pipeline completo con 3 fotos de prueba:
d:\EXON2\backend\.venv_cuda\Scripts\python.exe backend/scripts/test_batch_3_photos.py

# 2. Re-escanear videos .mp4 y extraer los mejores frames nítidos:
d:\EXON2\backend\.venv_cuda\Scripts\python.exe backend/scripts/curate_media_dataset.py

# 3. Construir / Actualizar el perfil 3D multi-ángulo de Masiel en SQLite:
d:\EXON2\backend\.venv_cuda\Scripts\python.exe backend/scripts/build_curated_profile.py

# 4. Iniciar manualmente solo el Backend:
d:\EXON2\backend\.venv_cuda\Scripts\python.exe -m uvicorn src.interfaces.api.app:create_app --factory --host 127.0.0.1 --port 8000

# 5. Iniciar manualmente solo el Frontend:
cd D:\EXON2\frontend && npm run dev
```

---

## 8. 🛠️ SOLUCIÓN RÁPIDA A PROBLEMAS CONOCIDOS TRAS FORMATEAR

### Problema 1: `npm : No se puede cargar el archivo npm.ps1 porque la ejecución de scripts está deshabilitada`
* **Solución**: Abre PowerShell como Administrador y escribe:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

### Problema 2: `Error loading onnxruntime_providers_cuda.dll which depends on cublasLt64_13.dll`
* **Solución**: Se instaló una versión de ONNXRuntime que busca CUDA 13. Se resuelve fijando la versión 1.19.2:
  ```cmd
  uv pip install --python .venv_cuda\Scripts\python.exe onnxruntime==1.19.2
  ```

### Problema 3: Error de importación de `face_align` en InsightFace
* **Solución**: Asegúrate de que `scikit-image` y `scipy` estén instalados en `.venv_cuda`:
  ```cmd
  uv pip install --python .venv_cuda\Scripts\python.exe scikit-image scipy
  ```

---

## 9. 🔒 RESUMEN DE SEGURIDAD

* **Código fuente**: 100% respaldado en GitHub (`https://github.com/bmontes93/Exon2.git`).
* **Pesos y modelos**: Guardar copia de `D:\EXON2\models\` en USB.
* **Base de datos biométrica**: Guardar copia de `D:\EXON2\backend\exon_metadata.db` en USB.
* **Fotos y videos**: Guardar copia de `Z:\MASIEL FOTOS\julio\` en USB.
