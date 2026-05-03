"""CRUD"""

from sqlalchemy.orm import Session
from . import models


def create_song(db: Session, song):
    """Create song"""
    db_song = models.Song(**song.dict())
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


def get_songs(db: Session):
    """Get song from DB"""
    return db.query(models.Song).all()
