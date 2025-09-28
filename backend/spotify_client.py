import os
import base64
import time
from typing import Dict, List, Any
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment (.env)
loaded = load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
if not loaded:
    load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise RuntimeError(
        "Missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET. "
        "Create backend/.env with those keys (no quotes)."
    )

# Requests session helper
def _new_session() -> requests.Session:
    s = requests.Session()
    s.trust_env = False  
    return s

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "mood-music/spotify-only/0.4",
}

_token_cache: Dict[str, Any] = {"access_token": None, "expires_at": 0}

def _get_basic_auth_header() -> str:
    creds = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    return "Basic " + base64.b64encode(creds.encode("utf-8")).decode("ascii")

def get_access_token() -> str:
    now = int(time.time())
    if _token_cache["access_token"] and now < (_token_cache["expires_at"] - 60):
        return _token_cache["access_token"]

    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": _get_basic_auth_header(),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    with _new_session() as s:
        resp = s.post(token_url, headers=headers, data=data, timeout=15, allow_redirects=False)

    if resp.status_code != 200:
        raise RuntimeError(f"Spotify token request failed: {resp.status_code} {resp.text[:200]}")

    js = resp.json()
    _token_cache["access_token"] = js["access_token"]
    _token_cache["expires_at"] = int(time.time()) + int(js["expires_in"])
    return _token_cache["access_token"]

# Mood → rec hints
MOOD_MAP: Dict[str, Dict[str, Any]] = {
    "happy": {"seed_genres": "pop,dance,electronic", "target_valence": 0.9, "target_energy": 0.7, "target_danceability": 0.7},
    "sad":   {"seed_genres": "acoustic,piano,classical", "target_valence": 0.2, "target_energy": 0.3, "target_danceability": 0.3},
    "calm":  {"seed_genres": "ambient,classical,chill", "target_valence": 0.5, "target_energy": 0.2, "target_danceability": 0.2},
    "angry": {"seed_genres": "rock,metal,punk", "target_valence": 0.3, "target_energy": 0.95, "target_danceability": 0.5},
}

def _normalize_spotify_tracks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in data.get("tracks", []):
        title = item.get("name", "")
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        preview_url = item.get("preview_url")
        external_url = item.get("external_urls", {}).get("spotify")
        images = item.get("album", {}).get("images", [])
        cover_url = images[0]["url"] if images else None
        out.append({
            "title": title,
            "artist": artists,
            "preview_url": preview_url,
            "external_url": external_url,
            "cover_url": cover_url,
        })
    return out

def _normalize_search_tracks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    items = data.get("tracks", {}).get("items", [])
    for item in items:
        title = item.get("name", "")
        artists = ", ".join(a.get("name", "") for a in item.get("artists", []))
        preview_url = item.get("preview_url")
        external_url = item.get("external_urls", {}).get("spotify")
        images = item.get("album", {}).get("images", [])
        cover_url = images[0]["url"] if images else None
        out.append({
            "title": title,
            "artist": artists,
            "preview_url": preview_url,
            "external_url": external_url,
            "cover_url": cover_url,
        })
    return out

def _try_recommendations(mood_key: str, limit: int, token: str) -> List[Dict[str, Any]]:
    cfg = MOOD_MAP.get(
        mood_key,
        {"seed_genres": "pop", "target_valence": 0.6, "target_energy": 0.6, "target_danceability": 0.6}
    )
    url = "https://api.spotify.com/v1/recommendations"
    params = {
        "limit": str(limit),
        "seed_genres": cfg["seed_genres"],
        "target_valence": str(cfg["target_valence"]),
        "target_energy": str(cfg["target_energy"]),
        "target_danceability": str(cfg["target_danceability"]),
        "market": "US",  
    }
    headers = {**DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}

    req = requests.Request("GET", url, headers=headers, params=params).prepare()
    print("DEBUG Spotify Recs URL =>", req.url)

    with _new_session() as s:
        resp = s.send(req, timeout=15, allow_redirects=False)

    if resp.status_code != 200:
        short = (resp.text or "")[:200]
        raise RuntimeError(f"recs {resp.status_code} {short}")

    return _normalize_spotify_tracks(resp.json())

def _try_search(mood_key: str, limit: int, token: str) -> List[Dict[str, Any]]:
    q_map = {
        "happy": "happy upbeat pop",
        "sad": "sad acoustic",
        "calm": "calm ambient",
        "angry": "angry rock",
    }
    q = q_map.get(mood_key, "pop")

    url = "https://api.spotify.com/v1/search"
    params = {
        "q": q,
        "type": "track",
        "limit": str(limit),
        "market": "US",
    }
    headers = {**DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}

    req = requests.Request("GET", url, headers=headers, params=params).prepare()
    print("DEBUG Spotify Search URL =>", req.url)

    with _new_session() as s:
        resp = s.send(req, timeout=15, allow_redirects=False)

    if resp.status_code != 200:
        short = (resp.text or "")[:200]
        raise RuntimeError(f"search {resp.status_code} {short}")

    return _normalize_search_tracks(resp.json())

def get_recommendations_for_mood(mood: str, limit: int = 10) -> List[Dict[str, Any]]:
    mood_key = mood.lower()
    token = get_access_token()

    try:
        return _try_recommendations(mood_key, limit, token)
    except Exception as e1:
        print("WARN: /v1/recommendations failed ->", e1)
        try:
            return _try_search(mood_key, limit, token)
        except Exception as e2:
            raise RuntimeError(f"Spotify failed (recs & search): {e1} | {e2}")

