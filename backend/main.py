"""
INSTALACIÓN:
    pip install fastapi uvicorn playwright python-dotenv requests
    playwright install chromium

EJECUTAR:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import json
import time
import random
import os
import requests as req_lib
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel #para definir restricciones de los datos que se reciben y se envían en los endpoints, como un contrato de lo que se espera
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Instagram Scraper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000", "http://127.0.0.1:5173","http://localhost:5500","http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Post(BaseModel):
    id: str
    shortcode: str
    url: str
    tipo: str
    fecha: str
    likes: int
    comentarios: int
    caption: str
    imagen_url: str

class ProfileResponse(BaseModel):
    username: str
    full_name: str
    followers: int
    following: int
    bio: str
    profile_pic: str
    posts: list[Post]


def get_cookies() -> list[dict]: #Lee las credenciales del entorno y las devuelve en el formato que Playwright entiende para configurar las cookies de la sesión de Instagram. Estas cookies son necesarias para acceder a los endpoints privados de Instagram y evitar bloqueos por parte de la plataforma.
    sessionid  = os.getenv("IG_SESSIONID", "")
    csrftoken  = os.getenv("IG_CSRFTOKEN", "")
    ds_user_id = os.getenv("IG_DS_USER_ID", "")
    ig_did     = os.getenv("IG_DID", "")

    if not sessionid or sessionid == "TU_SESSION_ID_AQUI":
        raise HTTPException(status_code=500, detail="Cookies no configuradas en backend/.env")

    return [
        {"name": "sessionid",  "value": sessionid,  "domain": ".instagram.com", "path": "/"},
        {"name": "csrftoken",  "value": csrftoken,   "domain": ".instagram.com", "path": "/"},
        {"name": "ds_user_id", "value": ds_user_id,  "domain": ".instagram.com", "path": "/"},
        {"name": "ig_did",     "value": ig_did,       "domain": ".instagram.com", "path": "/"},
    ]


def human_delay(min_s=1.5, max_s=3.5):
    time.sleep(random.uniform(min_s, max_s))


def ig_fetch(page, url: str) -> dict: #Ejecuta una petición HTTP desde dentro del navegador Chrome Por qué: Si la petición viene de Python directamente, Instagram la identifica como automatizada
    result = page.evaluate(f"""
        async () => {{
            const resp = await fetch({json.dumps(url)}, {{
                headers: {{
                    "X-IG-App-ID": "936619743392459",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "*/*",
                }}
            }});
            return {{ status: resp.status, body: await resp.text() }};
        }}
    """)
    return result


def fetch_image_base64(img_url: str) -> str:
    """
    Descarga una imagen de Instagram desde el backend (sin CORS)
    y la devuelve como data URL base64 lista para usar en <img src="...">.
    """
    if not img_url:
        return ""
    try: #user agent es para identificarse como navegador real y evitar bloqueos simples de bots. Referer es para evitar bloqueos por CORS.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.instagram.com/",
        }
        r = req_lib.get(img_url, headers=headers, timeout=10)
        if r.status_code == 200:
            mime = r.headers.get("Content-Type", "image/jpeg").split(";")[0]
            b64  = __import__("base64").b64encode(r.content).decode()
            return f"data:{mime};base64,{b64}"
    except Exception:
        pass
    return ""


def scrape_profile(username: str, num_posts: int) -> dict:
    cookies = get_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, #sin interfaz gráfica no abre la ventana del navegador
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"] #oculta que es un navegador automatizado (osea controlado por bot)
        )
        #Estucutra en playwrigth es browser -> context -> page. El context es como una sesión de navegador, donde se pueden configurar cookies, user agent, etc. El page es la pestaña donde se navega y se hacen las acciones.
        context = browser.new_context(
            viewport={"width": 1280, "height": 800}, #tamaño de la ventana del navegador, no es necesario pero ayuda a evitar bloqueos
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " #identificarse como navegador real
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="es-ES",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        page.goto("https://www.instagram.com/", wait_until="domcontentloaded") #espera a que se cargue el HTML inicial, no espera a que carguen las imágenes ni los scripts
        human_delay(2, 3) #simula el tiempo que tarda un humano en leer la página y evitar bloqueos por actividad sospechosa

        # Perfil 
        profile_result = ig_fetch(
            page,
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        )

        if profile_result["status"] == 404:
            raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado o es privado.")
        if profile_result["status"] == 401:
            raise HTTPException(status_code=401, detail="Cookies inválidas o expiradas.")
        if profile_result["status"] == 429:
            raise HTTPException(status_code=429, detail="Rate limit. Espera unos minutos.")
        if profile_result["status"] != 200:
            raise HTTPException(status_code=500, detail=f"Error Instagram: HTTP {profile_result['status']}")

        profile_data = json.loads(profile_result["body"]) #json.loads convierte el string JSON a un diccionario de Python
        user         = profile_data["data"]["user"] #estructura del JSON de Instagram
        user_id      = user["id"]

        # Posts 
        posts  = []
        cursor = None

        while len(posts) < num_posts:
            url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12" #endpoint para obtener el feed de un usuario, count es la cantidad de posts a obtener por página (máximo 12)
            if cursor:
                url += f"&max_id={cursor}" #cursor para paginar, indica desde qué post seguir obteniendo (el id del último post obtenido en la página anterior)

            feed_result = ig_fetch(page, url)

            if feed_result["status"] == 429:
                raise HTTPException(status_code=429, detail="Rate limit alcanzado.")
            if feed_result["status"] != 200 or not feed_result["body"].strip():
                raise HTTPException(status_code=500, detail="Error al obtener el feed.")

            feed_data = json.loads(feed_result["body"])
            items     = feed_data.get("items", [])

            for item in items:
                posts.append(parse_post(item))
                if len(posts) >= num_posts:
                    break

            if not feed_data.get("more_available") or not items:
                break

            cursor = feed_data.get("next_max_id")
            human_delay(2, 4)

        browser.close()

    # Convertir imágenes a base64 (fuera del browser, sin CORS) 
    raw_profile_pic = user.get("profile_pic_url_hd", user.get("profile_pic_url", ""))
    profile_pic_b64 = fetch_image_base64(raw_profile_pic)

    for post in posts:
        if post["imagen_url"]:
            post["imagen_url"] = fetch_image_base64(post["imagen_url"])

    return {
        "username":    username,
        "full_name":   user.get("full_name", ""),
        "followers":   user.get("edge_followed_by", {}).get("count", 0),
        "following":   user.get("edge_follow", {}).get("count", 0),
        "bio":         user.get("biography", ""),
        "profile_pic": profile_pic_b64,
        "posts":       posts[:num_posts],
    }


def parse_post(item: dict) -> dict:
    caption = ""
    cap_obj = item.get("caption")
    if cap_obj and isinstance(cap_obj, dict):
        caption = cap_obj.get("text", "")

    media_type = item.get("media_type", 1)
    type_map   = {1: "Imagen", 2: "Video", 8: "Carrusel"}
    post_type  = type_map.get(media_type, "Desconocido")

    timestamp = item.get("taken_at", 0)
    fecha     = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M UTC") if timestamp else "?"

    imagen_url = ""
    if "image_versions2" in item:
        candidates = item["image_versions2"].get("candidates", [])
        if candidates:
            imagen_url = candidates[0].get("url", "")

    code = item.get("code", item.get("shortcode", ""))

    return {
        "id":          str(item.get("pk", "")),
        "shortcode":   code,
        "url":         f"https://www.instagram.com/p/{code}/" if code else "",
        "tipo":        post_type,
        "fecha":       fecha,
        "likes":       item.get("like_count", 0),
        "comentarios": item.get("comment_count", 0),
        "caption":     caption[:300] + ("..." if len(caption) > 300 else ""),
        "imagen_url":  imagen_url,
    }


# ── Endpoints ─────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "Instagram Scraper API activa"}


@app.get("/scrape/{username}", response_model=ProfileResponse)
def scrape(username: str, num_posts: int = 10):
    return scrape_profile(username.strip().lower(), num_posts)