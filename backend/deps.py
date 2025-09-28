from typing import Generator
from db import SessionLocal  

def get_db() -> Generator:
    """
    Yield a database session for the duration of the request, then close it.
    """
    db = SessionLocal()   
    try:
        yield db         
    finally:
        db.close()       
