"""
Instagram Scraper — Backend FastAPI
=====================================
Expone un endpoint REST que el frontend React consume.

INSTALACIÓN:
    pip install fastapi uvicorn playwright python-dotenv
    playwright install chromium

EJECUTAR:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import json
import time
import random
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# ── Cargar variables de entorno ──────────────────
load_dotenv()

app = FastAPI(title="Instagram Scraper API")

# CORS — permite que el frontend React (puerto 5173) se comunique con el backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos ──────────────────────────────────────

class ScrapeRequest(BaseModel):
    username: str
    num_posts: int = 10


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


# ── Helpers ──────────────────────────────────────

def get_cookies() -> list[dict]:
    """Lee las cookies desde las variables de entorno."""
    sessionid  = os.getenv("IG_SESSIONID", "")
    csrftoken  = os.getenv("IG_CSRFTOKEN", "")
    ds_user_id = os.getenv("IG_DS_USER_ID", "")
    ig_did     = os.getenv("IG_DID", "")

    if not sessionid or sessionid == "TU_SESSION_ID_AQUI":
        raise HTTPException(
            status_code=500,
            detail="Cookies no configuradas. Edita el archivo backend/.env con tus cookies reales."
        )

    return [
        {"name": "sessionid",  "value": sessionid,  "domain": ".instagram.com", "path": "/"},
        {"name": "csrftoken",  "value": csrftoken,   "domain": ".instagram.com", "path": "/"},
        {"name": "ds_user_id", "value": ds_user_id,  "domain": ".instagram.com", "path": "/"},
        {"name": "ig_did",     "value": ig_did,       "domain": ".instagram.com", "path": "/"},
    ]


def human_delay(min_s=1.5, max_s=3.5):
    time.sleep(random.uniform(min_s, max_s))


def ig_fetch(page, url: str) -> dict:
    """Hace fetch() desde el contexto del navegador autenticado."""
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


def scrape_profile(username: str, num_posts: int) -> dict:
    """Lógica principal de scraping usando Playwright."""
    cookies = get_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="es-ES",
        )
        context.add_cookies(cookies)
        page = context.new_page()

        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        human_delay(2, 3)

        # ── 1. Obtener info del perfil ──
        profile_result = ig_fetch(
            page,
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        )

        if profile_result["status"] == 404:
            raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado o es privado.")
        if profile_result["status"] == 401:
            raise HTTPException(status_code=401, detail="Cookies inválidas o expiradas.")
        if profile_result["status"] == 429:
            raise HTTPException(status_code=429, detail="Rate limit de Instagram. Espera unos minutos.")
        if profile_result["status"] != 200:
            raise HTTPException(status_code=500, detail=f"Error de Instagram: HTTP {profile_result['status']}")

        profile_data = json.loads(profile_result["body"])
        user         = profile_data["data"]["user"]
        user_id      = user["id"]

        # ── 2. Obtener posts ──
        posts    = []
        cursor   = None

        while len(posts) < num_posts:
            url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12"
            if cursor:
                url += f"&max_id={cursor}"

            feed_result = ig_fetch(page, url)

            if feed_result["status"] == 429:
                raise HTTPException(status_code=429, detail="Rate limit alcanzado. Espera unos minutos.")
            if feed_result["status"] != 200 or not feed_result["body"].strip():
                raise HTTPException(status_code=500, detail="Error al obtener el feed del usuario.")

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

        return {
            "username":    username,
            "full_name":   user.get("full_name", ""),
            "followers":   user.get("edge_followed_by", {}).get("count", 0),
            "following":   user.get("edge_follow", {}).get("count", 0),
            "bio":         user.get("biography", ""),
            "profile_pic": user.get("profile_pic_url_hd", user.get("profile_pic_url", "")),
            "posts":       posts[:num_posts],
        }


def parse_post(item: dict) -> dict:
    caption    = ""
    cap_obj    = item.get("caption")
    if cap_obj and isinstance(cap_obj, dict):
        caption = cap_obj.get("text", "")

    media_type = item.get("media_type", 1)
    type_map   = {1: "Imagen", 2: "Video", 8: "Carrusel"}
    post_type  = type_map.get(media_type, "Desconocido")

    timestamp  = item.get("taken_at", 0)
    fecha      = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M UTC") if timestamp else "?"

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


# ── Endpoints ────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "Instagram Scraper API activa 🚀"}


@app.get("/scrape/{username}", response_model=ProfileResponse)
def scrape(username: str, num_posts: int = 10):
    """
    Scrapea un perfil público de Instagram.
    - username: nombre de usuario (sin @)
    - num_posts: cantidad de posts a obtener (default 10)
    """
    return scrape_profile(username.strip().lower(), num_posts)