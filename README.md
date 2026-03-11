# OpenSchool Platform

[![CI](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Nyílt forráskódú oktatási platform, ahol a diákok valódi fejlesztői eszközökkel tanulnak programozni.

> **Az open source nem feature — az open source a tanterv.**

Nem csak a szoftver nyílt: a tananyag, az eszközök, az értékelés, a platform kódja — minden látható, minden módosítható.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Adatbázis:** PostgreSQL
- **Frontend:** Astro (statikus oldal generátor)
- **Infrastruktúra:** Docker Compose, nginx, GitHub Actions

## Gyors indítás

### Előfeltételek

- Docker és Docker Compose
- Python 3.12+ (lokális fejlesztéshez)

### Futtatás Docker-rel

```bash
# .env fájl létrehozása
cp .env.example .env

# Indítás
docker compose up --build -d

# Ellenőrzés
curl http://localhost:8000/health
```

### Lokális fejlesztés

```bash
# Virtuális környezet
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Tesztek futtatása
pytest -v

# Linter
ruff check . && ruff format --check .
```

### Makefile parancsok

```bash
make up       # Docker Compose indítás
make down     # Docker Compose leállítás
make test     # Tesztek futtatása
make migrate  # Alembic migrációk futtatása
make lint     # Ruff linter és formatter ellenőrzés
```

## Projekt struktúra

```
openschool-platform/
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci.yml
├── Makefile
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   └── routers/
│   └── tests/
├── frontend/
└── nginx/
```

## API Endpoints

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/health` | GET | Health check |
| `/api/auth/login` | GET | GitHub OAuth bejelentkezés |
| `/api/auth/callback` | GET | OAuth callback |
| `/api/auth/me` | GET | Aktuális felhasználó adatai |
| `/api/auth/refresh` | POST | Token frissítés |
| `/api/courses` | GET | Kurzusok listázása |
| `/api/courses/{id}` | GET | Kurzus részletei |
| `/api/me/dashboard` | GET | Felhasználói dashboard |
| `/api/me/certificates` | GET | Tanúsítványok listája |
| `/api/verify/{cert_id}` | GET | Tanúsítvány publikus verifikáció |

## Hozzájárulás

Szívesen fogadjuk a hozzájárulásokat! Olvasd el a [CONTRIBUTING.md](CONTRIBUTING.md) fájlt a részletekért.

## Dokumentáció

| Dokumentum | Leírás |
|---|---|
| [Architektúra](docs/architektura.md) | Rendszer felépítés, adatmodell, auth folyamat, API struktúra |
| [Telepítési útmutató](docs/telepitesi-utmutato.md) | Helyi fejlesztés, staging, éles VPS telepítés, SSL, backup |
| [Fejlesztői útmutató](docs/fejlesztoi-utmutato.md) | Python venv, VS Code, pre-commit, Ruff, pytest, Docker, CI/CD, logok |
| [Jövőkép és fejlesztési terv](docs/jovokep-es-fejlesztesi-terv.md) | Kurzusok, megvalósított funkciók, roadmap |
| [Felhasználói útmutató](docs/felhasznaloi-utmutato.md) | Oldalak, gombok, felhasználói folyamatok, admin panel |
| [GitHub Classroom integráció](docs/github-classroom-integraciot.md) | Feladatok összekötése, repo_prefix, webhook, tanári útmutató |
| [Karbantartás](docs/karbantartas-utmutato.md) | Függőségkezelés, monitoring, backup, biztonsági audit, incidenskezelés |
| [Hozzájárulás](CONTRIBUTING.md) | Fork, branch stratégia, PR küldés, kódstílus |

A `good first issue` címkéjű [issue-k](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) ideálisak kezdőknek.

## Licensz

A projekt az [MIT License](LICENSE) alatt érhető el.
