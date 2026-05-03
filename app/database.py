"""Database"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./songs.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SESSION_LOCAL = sessionmaker(bind=engine)

Base = declarative_base()
