# db.py
# Sets up a connection to a local SQLite file and a Session factory.

from sqlalchemy import create_engine                 # Creates the DB engine (connection manager)
from sqlalchemy.orm import sessionmaker, DeclarativeBase  # Session factory + Base class for models

# Connection string for SQLite.
# "sqlite:///mood.db" -> store a file named mood.db in the current folder.
DATABASE_URL = "sqlite:///mood.db"

# Create the SQLAlchemy Engine that knows how to talk to SQLite.
# check_same_thread=False is needed for SQLite when used in web apps during dev.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal is a *factory* that makes Session objects.
# Each request will use one Session to talk to the DB, then close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our ORM model classes will inherit from.
class Base(DeclarativeBase):
    pass
