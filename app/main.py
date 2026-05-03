"""All ports"""

# pylint: disable=missing-function-docstring,too-many-arguments,too-many-positional-arguments,unused-argument

from uuid import uuid4

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Cookie,
    Request,
    Form,
    UploadFile,
    File,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

from jose import jwt

from .database import Base, engine
from . import models, schemas, crud, auth, dependencies
from .business.recommendations import recommend_songs

templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_user_from_cookie(
    access_token: str = Cookie(None), db: Session = Depends(dependencies.get_db)
):
    if access_token is None:
        return None

    payload = jwt.decode(access_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    username = payload.get("sub")

    if username is None:
        print("none")
        return None

    res = db.query(models.User).filter_by(username=username).first()
    print(res)
    return res


@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_user_from_cookie)):
    print("USER:", user)

    return templates.TemplateResponse(
        request, "index.html", {"request": request, "user": user}
    )


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    hashed = auth.hash_password(user.password)
    db_user = models.User(username=user.username, password=hashed)
    db.add(db_user)
    db.commit()
    return {"msg": "user created"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    db_user = db.query(models.User).filter_by(username=user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = auth.create_token({"sub": db_user.username})
    return {"access_token": token}


@app.post("/login-web")
def login_web(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(dependencies.get_db),
):
    user = db.query(models.User).filter_by(username=username).first()

    if not user:
        return templates.TemplateResponse(
            request, "login.html", {"error": f"There is no user '{username}'"}
        )

    if not auth.verify_password(password, user.password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Incorrect password. Try again"}
        )

    token = auth.create_token({"sub": user.username})

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")

    return response


def get_current_user_from_cookie(
    access_token: str = Cookie(None), db: Session = Depends(dependencies.get_db)
):
    if not access_token:
        return None

    payload = jwt.decode(access_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    username = payload.get("sub")

    return db.query(models.User).filter_by(username=username).first()


@app.post("/songs")
def create_song(song: schemas.SongCreate, db: Session = Depends(dependencies.get_db)):
    return crud.create_song(db, song)


@app.get("/songs")
def read_songs(db: Session = Depends(dependencies.get_db)):
    return crud.get_songs(db)


@app.get("/songs-ui", response_class=HTMLResponse)
def songs_ui(
    request: Request,
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    if not user:
        return RedirectResponse("/login", status_code=302)

    songs = db.query(models.Song).filter_by(user_id=user.id).all()

    return templates.TemplateResponse(
        request, "songs.html", {"request": request, "songs": songs, "user": user}
    )


@app.post("/songs-ui")
def create_song_ui(
    request: Request,
    title: str = Form(...),
    artist: str = Form(...),
    genre: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    if not user:
        return RedirectResponse("/login", status_code=302)

    artist_obj = db.query(models.Artist).filter_by(name=artist).first()
    if not artist_obj:
        artist_obj = models.Artist(name=artist)
        db.add(artist_obj)
        db.commit()
        db.refresh(artist_obj)

    filename = f"{uuid4()}.mp3"
    file_path = f"app/static/audio/{filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    song = models.Song(
        title=title,
        artist_id=artist_obj.id,
        genre=genre,
        file_path=file_path,
        user_id=user.id,
    )

    db.add(song)
    db.commit()

    return RedirectResponse("/songs-ui", status_code=302)


@app.post("/songs/{song_id}/delete")
def delete_song(
    song_id: int,
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    song = db.query(models.Song).filter_by(id=song_id, user_id=user.id).first()

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    db.delete(song)
    db.commit()

    return RedirectResponse(url="/songs-ui", status_code=302)


@app.get("/me")
def protected(token: str, db: Session = Depends(dependencies.get_db)):
    user = dependencies.get_current_user(token, db)
    return {"user": user.username}


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})


@app.post("/register-web", response_class=HTMLResponse)
def register_web(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(dependencies.get_db),
):
    existing = db.query(models.User).filter_by(username=username).first()

    if existing:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"request": request, "error": f"User '{username}' already exists"},
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "request": request,
                "error": "Password shall contain at least 8 characters",
            },
        )

    hashed = auth.hash_password(password)
    new_user = models.User(username=username, password=hashed)

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        request,
        "register.html",
        {"request": request, "success": "Registration succeeded! You can login now."},
    )


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response


@app.post("/playlists")
def create_playlist(
    name: str = Form(...),
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    if not user:
        return RedirectResponse("/login", status_code=302)

    playlist = models.Playlist(name=name, user_id=user.id)

    db.add(playlist)
    db.commit()

    return RedirectResponse("/songs-ui", status_code=302)


@app.post("/playlists/add")
def add_song_to_playlist(
    song_id: int = Form(...),
    playlist_id: int = Form(...),
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    playlist = (
        db.query(models.Playlist).filter_by(id=playlist_id, user_id=user.id).first()
    )
    song = db.query(models.Song).filter_by(id=song_id, user_id=user.id).first()

    if not playlist or not song:
        return RedirectResponse("/songs-ui", status_code=302)

    playlist.songs.append(song)
    db.commit()

    return RedirectResponse(f"/playlists/{playlist_id}", status_code=302)


@app.post("/playlists/{playlist_id}/delete")
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    playlist = (
        db.query(models.Playlist).filter_by(id=playlist_id, user_id=user.id).first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    db.delete(playlist)
    db.commit()

    return RedirectResponse(url="/songs-ui", status_code=302)


@app.get("/playlists/{playlist_id}", response_class=HTMLResponse)
def playlist_page(
    request: Request,
    playlist_id: int,
    db: Session = Depends(dependencies.get_db),
    user=Depends(get_user_from_cookie),
):
    playlist = (
        db.query(models.Playlist).filter_by(id=playlist_id, user_id=user.id).first()
    )

    if not playlist:
        return RedirectResponse("/songs-ui", status_code=302)

    return templates.TemplateResponse(
        request,
        "playlist.html",
        {"request": request, "user": user, "playlist": playlist},
    )


@app.get("/recommendations")
def get_recommendations(
    db: Session = Depends(dependencies.get_db), user=Depends(get_user_from_cookie)
):
    songs = recommend_songs(db, user.id)

    return {
        "songs": [
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist.name,
                "genre": s.genre,
                "file": s.file_path,
            }
            for s in songs
        ]
    }
