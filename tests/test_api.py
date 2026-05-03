import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app import models, database, auth
from app.dependencies import get_db

# -----------------------
# TEST DB (ВАЖНО)
# -----------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def setup_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# -----------------------
# HELPERS
# -----------------------
def create_user(username="u1", password="p1"):
    db = TestingSessionLocal()
    user = models.User(
        username=username,
        password=auth.hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def create_song(user_id, title="Song1"):
    db = TestingSessionLocal()
    song = models.Song(
        title=title,
        artist_id=1,
        user_id=user_id,
        genre="rock",
        file_path="test.mp3",
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    db.close()
    return song


def create_playlist(user_id, name="Playlist"):
    db = TestingSessionLocal()
    playlist = models.Playlist(name=name, user_id=user_id)
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    db.close()
    return playlist


# -----------------------
# AUTH
# -----------------------
def test_register():
    r = client.post("/register", json={"username": "u1", "password": "p1"})
    assert r.status_code == 200


def test_login_wrong_password():
    create_user()

    r = client.post(
        "/login-web",
        data={"username": "u1", "password": "wrong"},
    )

    assert "Incorrect password" in r.text


def test_login_success():
    create_user()

    r = client.post(
        "/login-web",
        data={"username": "u1", "password": "p1"},
        follow_redirects=False,
    )

    assert r.status_code == 302


# -----------------------
# SONGS
# -----------------------
def test_create_song():
    user = create_user()

    client.cookies.set(
        name="access_token", value=auth.create_token({"sub": user.username})
    )
    r = client.post(
        "/songs-ui",
        data={"title": "Song", "artist": "A", "genre": "rock"},
        files={"file": ("a.mp3", b"fake", "audio/mpeg")},
        follow_redirects=False,
    )

    assert r.status_code == 302


def test_songs_ui_requires_auth():
    r = client.get("/songs-ui", follow_redirects=False)
    assert r.status_code in (302, 401)


def test_delete_song():
    user = create_user()
    song = create_song(user.id)

    client.cookies.set(
        name="access_token", value=auth.create_token({"sub": user.username})
    )
    r = client.post(
        f"/songs/{song.id}/delete",
        follow_redirects=False,
    )

    assert r.status_code == 302


# -----------------------
# PLAYLISTS
# -----------------------
def test_create_playlist():
    user = create_user()

    client.cookies.set(
        name="access_token", value=auth.create_token({"sub": user.username})
    )
    r = client.post(
        "/playlists",
        data={"name": "MyPlaylist"},
        follow_redirects=False,
    )

    assert r.status_code == 302


def test_add_song_to_playlist():
    user = create_user()
    song = create_song(user.id)
    playlist = create_playlist(user.id)

    client.cookies.set(
        name="access_token", value=auth.create_token({"sub": user.username})
    )
    r = client.post(
        "/playlists/add",
        data={"song_id": song.id, "playlist_id": playlist.id},
        follow_redirects=False,
    )

    assert r.status_code == 302


def test_delete_playlist():
    user = create_user()
    playlist = create_playlist(user.id)

    client.cookies.set(
        name="access_token", value=auth.create_token({"sub": user.username})
    )
    r = client.post(
        f"/playlists/{playlist.id}/delete",
        follow_redirects=False,
    )

    assert r.status_code == 302


# -----------------------
# RECOMMENDATIONS
# -----------------------
def test_recommendations():
    user = create_user()

    client.cookies.set(
        name="access_token", value=auth.create_token({"sub": user.username})
    )
    r = client.get(
        "/recommendations",
    )

    assert r.status_code == 200
    assert "songs" in r.json()


# -----------------------
# SECURITY
# -----------------------
def test_protected_route_no_token():
    r = client.get("/songs-ui", follow_redirects=False)
    assert r.status_code in (302, 401)
