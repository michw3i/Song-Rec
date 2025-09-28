from datetime import datetime                          
from sqlalchemy import Column, Integer, String, DateTime 
from db import Base                                     

# Table 1: mood_logs
class MoodLog(Base):
    __tablename__ = "mood_logs"       

    id = Column(Integer, primary_key=True, index=True)  
    mood = Column(String, nullable=False, index=True)  

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False) 

    # Optional snapshot of the top track you picked
    top_track_title = Column(String, nullable=True)
    top_track_artist = Column(String, nullable=True)
    top_track_external_url = Column(String, nullable=True)
    top_track_cover_url = Column(String, nullable=True)
    top_track_preview_url = Column(String, nullable=True)

# Table 2: favorite_tracks
class FavoriteTrack(Base):
    __tablename__ = "favorite_tracks"

    id = Column(Integer, primary_key=True, index=True)  

    title = Column(String, nullable=False)              # Track title (required)
    artist = Column(String, nullable=False)             # Artist(s) (required)
    external_url = Column(String, nullable=True)        # Spotify track URL
    cover_url = Column(String, nullable=True)           # Album art URL
    preview_url = Column(String, nullable=True)         # 30s preview MP3 (or None)

    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False)

