from fastapi import FastAPI, Query, Depends, HTTPException    
from typing import Dict, List, Any                              
from sqlalchemy.orm import Session                             
from db import engine, Base             
from deps import get_db                 
from models import MoodLog, FavoriteTrack 

app = FastAPI(title="Mood to Music API", version="0.4.0")  

Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> Dict[str, Any]:
    """
    Helpful landing so visiting http://127.0.0.1:8000/ shows something.
    """
    return {
        "ok": True,
        "message": "Use /health, /docs, or /recommendations?mood=happy&limit=5"
    }

@app.get("/health")
def health() -> Dict[str, str]:
    """Simple health check."""
    return {"status": "ok"}

# Spotify Recs
@app.get("/recommendations")
def recommendations(
    mood: str = Query(..., description="Mood like happy/sad/calm/angry"),
    limit: int = Query(5, ge=1, le=20, description="How many tracks to return (1-20)")
) -> Dict[str, Any]:
    """
    Returns Spotify tracks for the given mood.
    If anything goes wrong (e.g., token error), returns a clear error JSON.
    """
    mood_key = mood.lower()

    # Import inside the route so a missing/invalid .env doesn't crash app startup.
    try:
        from spotify_client import get_recommendations_for_mood
    except Exception as e:
        return {"mood": mood_key, "tracks": [], "error": f"Spotify not configured: {e}"}

    try:
        tracks: List[Dict[str, Any]] = get_recommendations_for_mood(mood_key, limit=limit)
        return {"mood": mood_key, "tracks": tracks}
    except Exception as e:
        return {"mood": mood_key, "tracks": [], "error": str(e)}

# Mood Logs
@app.post("/moods/log")
def log_mood(
    payload: Dict[str, Any],           
    db: Session = Depends(get_db),    
) -> Dict[str, Any]:

    mood = (payload.get("mood") or "").strip().lower()
    if not mood:
        raise HTTPException(status_code=400, detail="Field 'mood' is required.")

    top = payload.get("top_track") or {}

    log = MoodLog(
        mood=mood,
        top_track_title=top.get("title"),
        top_track_artist=top.get("artist"),
        top_track_external_url=top.get("external_url"),
        top_track_cover_url=top.get("cover_url"),
        top_track_preview_url=top.get("preview_url"),
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "id": log.id,
        "mood": log.mood,
        "created_at": log.created_at.isoformat(),
        "top_track": {
            "title": log.top_track_title,
            "artist": log.top_track_artist,
            "external_url": log.top_track_external_url,
            "cover_url": log.top_track_cover_url,
            "preview_url": log.top_track_preview_url,
        }
    }

@app.get("/moods/recent")
def recent_moods(
    limit: int = Query(20, ge=1, le=100, description="How many rows to return"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Return the most recent mood logs, newest first.
    """
    rows = (
        db.query(MoodLog)
          .order_by(MoodLog.created_at.desc())
          .limit(limit)
          .all()
    )

    items: List[Dict[str, Any]] = []
    for r in rows:
        items.append({
            "id": r.id,
            "mood": r.mood,
            "created_at": r.created_at.isoformat(),
            "top_track": {
                "title": r.top_track_title,
                "artist": r.top_track_artist,
                "external_url": r.top_track_external_url,
                "cover_url": r.top_track_cover_url,
                "preview_url": r.top_track_preview_url,
            }
        })
    return {"items": items}

# Favorites
@app.post("/favorites/add")
def add_favorite(
    track: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Save a track as a favorite.
    Expected JSON:
    {
      "title": "...",     # required
      "artist": "...",    # required
      "external_url": "...",
      "cover_url": "...",
      "preview_url": "..."
    }
    """
    title = (track.get("title") or "").strip()
    artist = (track.get("artist") or "").strip()
    if not title or not artist:
        raise HTTPException(status_code=400, detail="Fields 'title' and 'artist' are required.")

    fav = FavoriteTrack(
        title=title,
        artist=artist,
        external_url=track.get("external_url"),
        cover_url=track.get("cover_url"),
        preview_url=track.get("preview_url"),
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)

    return {
        "id": fav.id,
        "title": fav.title,
        "artist": fav.artist,
        "external_url": fav.external_url,
        "cover_url": fav.cover_url,
        "preview_url": fav.preview_url,
        "saved_at": fav.saved_at.isoformat(),
    }

@app.get("/favorites")
def list_favorites(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    List all favorite tracks, newest first.
    """
    rows = db.query(FavoriteTrack).order_by(FavoriteTrack.saved_at.desc()).all()
    items: List[Dict[str, Any]] = []
    for r in rows:
        items.append({
            "id": r.id,
            "title": r.title,
            "artist": r.artist,
            "external_url": r.external_url,
            "cover_url": r.cover_url,
            "preview_url": r.preview_url,
            "saved_at": r.saved_at.isoformat(),
        })
    return {"items": items}

@app.delete("/favorites/{fav_id}")
def delete_favorite(
    fav_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Delete a favorite by ID.
    """
    fav = db.query(FavoriteTrack).filter(FavoriteTrack.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"ok": True, "deleted_id": fav_id}

# Stats
@app.get("/stats/summary")
def stats_summary(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Return simple counts per mood.
    """
    rows = db.query(MoodLog).all()
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r.mood] = counts.get(r.mood, 0) + 1

    by_mood = [{"mood": m, "count": c} for m, c in counts.items()]
    by_mood.sort(key=lambda x: x["count"], reverse=True)

    return {"total": len(rows), "by_mood": by_mood}
    
from fastapi.middleware.cors import CORSMiddleware  

app = FastAPI(title="Mood to Music API", version="0.4.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
