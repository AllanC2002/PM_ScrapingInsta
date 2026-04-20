"""
Instagram Public Profile Scraper — Playwright Edition
======================================================
Extrae las últimas N publicaciones de un perfil público de Instagram
usando Playwright (navegador real) + cookies de sesión.

REQUISITOS:
    pip install playwright
    playwright install chromium

CÓMO OBTENER TUS COOKIES:
    1. Abre Instagram en Chrome, inicia sesión
    2. F12 → Application → Cookies → https://www.instagram.com
    3. Copia: sessionid, csrftoken, ds_user_id, ig_did
"""

import json
import time
import sys
import random
from datetime import datetime
from playwright.sync_api import sync_playwright


# ──────────────────────────────────────────────
#  CONFIGURACIÓN — Edita estos valores
# ──────────────────────────────────────────────

COOKIES = [
    {"name": "sessionid",  "value": "3706803991%3AddWBImg9pNzSTG%3A2%3AAYiwgqTD4b-Nx0932iM_isniusy7XmTFO4QUbG5ESg",  "domain": ".instagram.com", "path": "/"},
    {"name": "csrftoken",  "value": "5smlKnZAVQuqlKwZhlRYF9BbAEuBO1j9",   "domain": ".instagram.com", "path": "/"},
    {"name": "ds_user_id", "value": "3706803991",  "domain": ".instagram.com", "path": "/"},
    {"name": "ig_did",     "value": "4B5BFE5B-41BA-475B-9589-9C7FFEFE86C6",      "domain": ".instagram.com", "path": "/"},
]

TARGET_USERNAME = "luisitocomunica"  # Perfil público a scrapear (sin @)
NUM_POSTS       = 10                 # Número de publicaciones a extraer
OUTPUT_FILE     = "posts.json"       # Archivo de salida (None para no guardar)
HEADLESS        = True               # False = ver el navegador (útil para debug)

# ──────────────────────────────────────────────


def human_delay(min_s: float = 1.5, max_s: float = 3.5):
    time.sleep(random.uniform(min_s, max_s))
 
 
def get_user_id(page, username: str) -> str:
    """Obtiene el user_id desde la API de perfil."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
 
    result = page.evaluate(f"""
        async () => {{
            const resp = await fetch("{url}", {{
                headers: {{
                    "X-IG-App-ID": "936619743392459",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "*/*",
                }}
            }});
            return {{ status: resp.status, body: await resp.text() }};
        }}
    """)
 
    if result["status"] == 401:
        raise PermissionError("❌ No autorizado. Verifica tus cookies.")
    if result["status"] == 404:
        raise ValueError(f"❌ Usuario '{username}' no existe o es privado.")
    if result["status"] == 429:
        raise ConnectionError("❌ Rate limit (429). Espera unos minutos.")
    if result["status"] != 200:
        raise ConnectionError(f"❌ HTTP {result['status']}")
 
    data      = json.loads(result["body"])
    user      = data["data"]["user"]
    user_id   = user["id"]
    full_name = user.get("full_name", "")
    followers = user.get("edge_followed_by", {}).get("count", "?")
    followers_str = f"{followers:,}" if isinstance(followers, int) else str(followers)
    print(f"✅ Usuario encontrado: @{username} ({full_name}) — {followers_str} seguidores")
    return user_id
 
 
def fetch_posts_v1(page, username: str, user_id: str, num_posts: int) -> list:
    """
    Estrategia 1: API /api/v1/feed/user/{user_id}/
    Endpoint más moderno y estable que GraphQL.
    """
    posts  = []
    cursor = None
 
    while len(posts) < num_posts:
        url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12"
        if cursor:
            url += f"&max_id={cursor}"
 
        result = page.evaluate(f"""
            async () => {{
                const resp = await fetch("{url}", {{
                    headers: {{
                        "X-IG-App-ID": "936619743392459",
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "*/*",
                    }}
                }});
                return {{ status: resp.status, body: await resp.text() }};
            }}
        """)
 
        if result["status"] == 429:
            print("  ⚠️  Rate limit. Esperando 60s...")
            time.sleep(60)
            continue
 
        if result["status"] != 200 or not result["body"].strip():
            raise ConnectionError(f"❌ Error en feed API: HTTP {result['status']}")
 
        data  = json.loads(result["body"])
        items = data.get("items", [])
 
        for item in items:
            posts.append(parse_post_v1(item))
            if len(posts) >= num_posts:
                break
 
        print(f"  📄 {len(items)} posts obtenidos (total: {len(posts)})")
 
        if not data.get("more_available") or not items:
            break
 
        cursor = data.get("next_max_id")
        human_delay(2, 5)
 
    return posts[:num_posts]
 
 
def parse_post_v1(item: dict) -> dict:
    """Parsea un item del endpoint /api/v1/feed/user/"""
    # Caption
    caption = ""
    cap_obj = item.get("caption")
    if cap_obj and isinstance(cap_obj, dict):
        caption = cap_obj.get("text", "")
 
    # Tipo
    media_type = item.get("media_type", 1)
    type_map   = {1: "Imagen", 2: "Video", 8: "Carrusel"}
    post_type  = type_map.get(media_type, "Desconocido")
 
    # Fecha
    timestamp = item.get("taken_at", 0)
    fecha     = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M UTC") if timestamp else "?"
 
    # Imagen
    imagen_url = ""
    if "image_versions2" in item:
        candidates = item["image_versions2"].get("candidates", [])
        if candidates:
            imagen_url = candidates[0].get("url", "")
 
    # Shortcode / URL
    code = item.get("code", item.get("shortcode", ""))
    pk   = item.get("pk", "")
 
    return {
        "id":          str(pk),
        "shortcode":   code,
        "url":         f"https://www.instagram.com/p/{code}/" if code else "",
        "tipo":        post_type,
        "fecha":       fecha,
        "likes":       item.get("like_count", 0),
        "comentarios": item.get("comment_count", 0),
        "caption":     caption[:300] + ("..." if len(caption) > 300 else ""),
        "imagen_url":  imagen_url,
    }
 
 
def print_posts(posts: list, username: str):
    print(f"\n{'═'*60}")
    print(f"  📸 Últimas {len(posts)} publicaciones de @{username}")
    print(f"{'═'*60}\n")
 
    for i, post in enumerate(posts, 1):
        print(f"  [{i:02d}] {post['tipo']} — {post['fecha']}")
        print(f"       🔗 {post['url']}")
        print(f"       ❤️  {post['likes']:,} likes   💬 {post['comentarios']:,} comentarios")
        if post["caption"]:
            snippet = post["caption"][:120]
            print(f"       📝 {snippet}{'...' if len(post['caption']) > 120 else ''}")
        print()
 
 
def save_to_json(posts: list, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"💾 Posts guardados en '{filename}'")
 
 
def main():
    username = sys.argv[1] if len(sys.argv) > 1 else TARGET_USERNAME
    n        = int(sys.argv[2]) if len(sys.argv) > 2 else NUM_POSTS
 
    print(f"\n🎭 Instagram Scraper — Playwright Edition")
    print(f"🔍 Objetivo: @{username} ({n} posts)\n")
 
    if "TU_SESSION_ID_AQUI" in COOKIES[0]["value"]:
        print("⚠️  ADVERTENCIA: Estás usando cookies de ejemplo.")
        print("    Edita la sección COOKIES del script con tus valores reales.\n")
 
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
 
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="es-ES",
        )
 
        context.add_cookies(COOKIES)
        page = context.new_page()
 
        print("🌐 Abriendo Instagram...")
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        human_delay(2, 4)
 
        try:
            user_id = get_user_id(page, username)
 
            print(f"\n⏳ Descargando posts con API v1...\n")
            posts = fetch_posts_v1(page, username, user_id, n)
 
            print_posts(posts, username)
 
            if OUTPUT_FILE:
                save_to_json(posts, OUTPUT_FILE)
 
        except (PermissionError, ValueError, ConnectionError) as e:
            print(e)
            sys.exit(1)
        except KeyError as e:
            print(f"❌ Estructura inesperada en la respuesta. Clave faltante: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            sys.exit(1)
        finally:
            browser.close()
 
 
if __name__ == "__main__":
    main()