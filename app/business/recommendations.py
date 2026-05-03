from sqlalchemy.orm import Session
from app import models


def recommend_songs(db: Session, user_id: int, limit: int = 10):
    user_genres = (
        db.query(models.Song.genre)
        .filter(models.Song.user_id == user_id)
        .distinct()
        .all()
    )

    genres = [g[0] for g in user_genres if g[0]]

    if not genres:
        return db.query(models.Song).limit(limit).all()

    songs = (
        db.query(models.Song)
        .filter(models.Song.genre.in_(genres))
        .filter(models.Song.user_id != user_id)
        .limit(limit)
        .all()
    )

    return songs
