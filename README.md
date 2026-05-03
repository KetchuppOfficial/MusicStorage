# REST service

A simple REST service for storing your favorite songs.

## Installation

### Clone the repository

```bash
git clone https://github.com/KetchuppOfficial/MusicStorage.git
```

### Create a virtual environment and install dependencies

Make user you've changed the current directory to the one of the project.

```bash
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
```

### Run the application

```bash
.venv/bin/uvicorn app.main:app --reload
```
