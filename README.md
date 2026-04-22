# Instagram Automation System (FastAPI + Playwright)

Este proyecto es una herramienta de automatización diseñada para interactuar con Instagram de manera programática. Utiliza **FastAPI** como servidor backend y **Playwright** para la navegación y gestión de sesiones avanzadas, permitiendo el acceso a funciones privadas mediante la inyección de cookies.

## 🛠️ Requisitos del Sistema

### 1. Dependencias de Python
El proyecto se basa en las siguientes librerías principales:
- `fastapi`: Framework moderno para la construcción de APIs.
- `uvicorn`: Servidor ASGI de alto rendimiento.
- `playwright`: Motor de automatización para navegadores modernos.
- `python-dotenv`: Gestión de variables de entorno desde archivos `.env`.
- `requests`: Manejo de peticiones HTTP síncronas.

### 2. Variables de Entorno (`.env`)
Para evitar bloqueos y la necesidad de iniciar sesión manualmente en cada ejecución, el sistema requiere cookies de una sesión activa. Debes crear un archivo `.env` en la carpeta `backend/` con el siguiente formato:

```env
IG_SESSIONID=tu_sessionid_aqui
IG_CSRFTOKEN=tu_csrftoken_aqui
IG_DS_USER_ID=tu_ds_user_id_aqui
IG_DID=tu_ig_did_aqui

### 3. Requerimientos
```cd
pip install -r requirements.txt
playwright install chromium

### 4. Ejecucion
```cd Terminal 1
cd backend
uvicorn main:app --reload --port 8000

```cd Terminal 2
cd frontend
python -m http.server 3000
