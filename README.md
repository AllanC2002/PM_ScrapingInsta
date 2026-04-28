# Instagram Automation System (FastAPI + Playwright)

Herramienta de scraping para perfiles públicos de Instagram. Extrae publicaciones, información del perfil e imágenes usando Playwright y las expone a través de una API REST con FastAPI.

## Tecnologías
 
- **Python** — Lenguaje principal
- **FastAPI** — Framework para la API REST
- **Playwright** — Automatización del navegador para evadir detección
- **python-dotenv** — Manejo seguro de credenciales
- **requests** — Descarga de imágenes base64

## Estructura del proyecto
 
```
PM_ScrapingInsta/
├── backend/
│   ├── main.py          ← API + lógica de scraping
│   ├── requirements.txt
│   └── .env             ← cookies de sesión (no subir a Git)
└── frontend/
    └── index.html       ← interfaz web
```

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
```

### 2.1 Cómo obtener las cookies:
1. Abre Instagram en Chrome e inicia sesión
2. Presiona `F12` → pestaña **Application** → **Cookies** → `https://www.instagram.com`
3. Copia los valores de `sessionid`, `csrftoken`, `ds_user_id` e `ig_did`
---

### 3. Requerimientos
```cd OP1
pip install -r requirements.txt
playwright install chromium
```
```cd OP1
pip install fastapi uvicorn playwright python-dotenv requests
playwright install chromium
```
### 4. Ejecucion
```cd Terminal 1
cd backend
uvicorn main:app --reload --port 8000
```
```cd Terminal 2
cd frontend
python -m http.server 3000
```
### 5. Endpoints disponibles
 
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Estado de la API |
| GET | `/scrape/{username}` | Scrapea un perfil público |
 
**Parámetros del endpoint `/scrape/{username}`:**
 
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `num_posts` | int | 10 | Cantidad de posts a obtener |
 
**Ejemplo:**
```
GET http://localhost:8000/scrape/natgeo?num_posts=10
```

### 6. Flujo general
 
```
- Usuario ingresa un @username en el frontend
- El frontend llama al backend: GET /scrape/{username}
- El backend abre un navegador Chrome con las cookies
- El navegador navega a Instagram y queda autenticado
- Se consulta la API interna de Instagram para obtener el perfil
- Se consulta el feed del usuario para obtener los posts en páginas de 12
- Se cierra el navegador
- El backend descarga las imágenes y las convierte a base64
- El backend devuelve todo como JSON al frontend
- El frontend renderiza el perfil, posts y estadísticas
```
 
### 7. Delays y rate limiting
 
Entre cada petición se introduce una pausa aleatoria de entre 2 y 4 segundos. La aleatoriedad es intencional — los bots suelen hacer peticiones en intervalos fijos y perfectos, lo cual Instagram detecta.

## 8. Limitaciones
 
- Solo funciona con perfiles **públicos**
- Instagram puede aplicar rate limiting si se hacen muchas peticiones seguidas
- Las cookies expiran — si el scraper deja de funcionar, actualiza las cookies en el `.env`
- Los endpoints internos de Instagram pueden cambiar sin previo aviso
---