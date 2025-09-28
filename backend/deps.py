# deps.py
# A tiny FastAPI dependency that hands a DB Session to each request and closes it after.

from typing import Generator
from db import SessionLocal  # Our Session factory

def get_db() -> Generator:
    """
    Yield a database session for the duration of the request, then close it.
    """
    db = SessionLocal()   # Open a new Session (DB connection wrapper)
    try:
        yield db          # Give it to the route handler
    finally:
        db.close()        # Always close to free resources
