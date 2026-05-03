"""Models"""

# pylint: disable=too-few-public-methods

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base

playlist_song = Table(
    "playlist_song",
    Base.metadata,
    Column("playlist_id", ForeignKey("playlists.id")),
    Column("song_id", ForeignKey("songs.id")),
)


class User(Base):
    """Model for user"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

    songs = relationship("Song", back_populates="owner")
    playlists = relationship("Playlist", back_populates="owner")


class Artist(Base):
    """Model for artists"""

    __tablename__ = "artists"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    songs = relationship("Song", back_populates="artist")


class Song(Base):
    """Model for songs"""

    __tablename__ = "songs"

    id = Column(Integer, primary_key=True)

    title = Column(String)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    genre = Column(String)
    file_path = Column(String)

    artist = relationship("Artist", back_populates="songs")
    owner = relationship("User", back_populates="songs")

    playlists = relationship(
        "Playlist", secondary=playlist_song, back_populates="songs"
    )


class Playlist(Base):
    """Model for playlists"""

    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="playlists")

    songs = relationship("Song", secondary=playlist_song, back_populates="playlists")
