# Backend fejlesztés

A FastAPI backend fejlesztéséhez szükséges minden: struktúra, routerek, szolgáltatások, tesztelés, linter, migrációk.

## Könyvtárstruktúra

```
backend/
├── app/
│   ├── main.py              # FastAPI alkalmazás, router regisztráció
│   ├── config.py             # Beállítások (pydantic-settings, .env olvasás)
│   ├── database.py           # SQLAlchemy engine, session, Base
│   ├── auth/
│   │   ├── jwt.py            # Token létrehozás és ellenőrzés (HS256)
│   │   └── dependencies.py   # get_current_user, require_role
│   ├── models/
│   │   ├── user.py           # User (github_id, role, stb.)
│   │   ├── course.py         # Course, Module, Exercise, Enrollment, Progress
│   │   ├── certificate.py    # Certificate (UUID, PDF útvonal)
│   │   └── promotion.py      # PromotionRule, PromotionRuleRequirement, PromotionLog
│   ├── routers/
│   │   ├── admin.py          # /api/admin/*
│   │   ├── auth.py           # /api/auth/*
│   │   ├── certificates.py   # /api/me/certificates/*, /api/verify/*
│   │   ├── courses.py        # /api/courses/*
│   │   ├── dashboard.py      # /api/me/*
│   │   └── webhooks.py       # /api/webhooks/*
│   └── services/
│       ├── certificate.py    # is_course_completed()
│       ├── discord.py        # Discord webhook értesítések
│       ├── discord_bot.py    # Discord Bot — szerepkör szinkronizáció
│       ├── pdf.py            # PDF generálás fpdf2-vel
│       ├── promotion.py      # check_and_promote() — automatikus előléptetés
│       ├── qr.py             # QR kód generálás
│       ├── github.py         # GitHub Actions állapot + org meghívás
│       └── progress.py       # Haladás frissítés GitHub CI alapján
├── alembic/                  # Adatbázis migrációk
├── tests/                    # pytest tesztek
├── pyproject.toml            # Ruff + pytest konfig
├── requirements.txt          # Produkciós csomagok
└── requirements-dev.txt      # Fejlesztői csomagok (-r requirements.txt + teszt, lint)
```

## Konfiguráció (`config.py`)

A `pydantic-settings` kezeli a `.env` fájlból betöltött beállításokat:

```python
class Settings(BaseSettings):
    database_url: str
    secret_key: str = "change-me-in-production"
    base_url: str = "http://localhost"
    environment: str = "development"
    allowed_origins: str = "http://localhost"
    github_client_id: str = ""
    github_client_secret: str = ""
    github_org: str = ""
    github_org_admin_token: str = ""
    github_webhook_secret: str = ""
    discord_webhook_url: str = ""
```

Az `environment` hatása:

| Érték | Log szint | Swagger UI | SECRET_KEY validáció |
|-------|-----------|------------|----------------------|
| `development` | DEBUG | Elérhető (`/docs`) | Nincs |
| `staging` | DEBUG | Kikapcsolt | ValueError ha alapértelmezett |
| `production` | INFO | Kikapcsolt | ValueError ha alapértelmezett |

## Routerek

Minden router a `backend/app/routers/`-ben van, a `main.py`-ban regisztrálva.

### `auth.py` — Autentikáció

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/auth/login` | GET | GitHub OAuth átirányítás |
| `/api/auth/callback` | GET | OAuth callback — user létrehozás/frissítés, JWT, org meghívás |
| `/api/auth/me` | GET | Aktuális felhasználó adatai |
| `/api/auth/me` | PATCH | Profil frissítés (Discord ID) |
| `/api/auth/refresh` | POST | Új access token a refresh token cookie-ból |
| `/api/auth/logout` | POST | Refresh token cookie törlése |

Az OAuth callback cseréli a GitHub kódot access tokenre, lekérdezi a profilt, JWT-t generál. Ha `GITHUB_ORG` + `GITHUB_ORG_ADMIN_TOKEN` konfigurálva van, automatikusan meghívja a felhasználót az org-ba. Tokenek httpOnly cookie-kban. Rate limiting: 10 kérés/perc a login/callback végpontokon.

### `courses.py` — Kurzusok

| Endpoint | Metódus | Auth | Leírás |
|----------|---------|------|--------|
| `/api/courses` | GET | — | Kurzuslista (lapozható) |
| `/api/courses/{id}` | GET | — | Kurzus részletei (modulok, feladatok) |
| `/api/courses` | POST | admin | Kurzus létrehozása |
| `/api/courses/{id}` | PUT | admin | Kurzus szerkesztése |
| `/api/courses/{id}/modules` | POST | admin | Modul hozzáadása |
| `/api/courses/{id}/modules/{mid}/exercises` | POST | admin | Feladat hozzáadása |
| `/api/courses/classroom/classrooms` | GET | admin | GitHub Classroom-ok listázása |
| `/api/courses/classroom/classrooms/{cid}/assignments` | GET | admin | Assignment-ek listázása |
| `/api/courses/{id}/modules/{mid}/import-classroom` | POST | admin | Classroom assignment-ek importálása (backfill támogatással) |
| `/api/courses/{id}/enroll` | POST | user | Beiratkozás |
| `/api/courses/{id}/unenroll` | POST | user | Leiratkozás |
| `/api/courses/{id}/students` | GET | mentor | Tanulók haladással |
| `/api/courses/{id}/students/{uid}/exercises` | GET | mentor | Diák feladatrészletei Classroom linkekkel |

### `dashboard.py` — Haladás

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/me/dashboard` | GET | Dashboard — kurzusok haladás-összesítéssel |
| `/api/me/courses` | GET | Beiratkozott kurzusok |
| `/api/me/courses/{id}/progress` | GET | Részletes haladás (modulonként) |
| `/api/me/courses/{id}/progress` | POST | Feladat manuális teljesítés jelölése |
| `/api/me/sync-progress` | POST | Haladás szinkronizálás GitHub CI-ból |

### `certificates.py` — Tanúsítványok

| Endpoint | Metódus | Auth | Leírás |
|----------|---------|------|--------|
| `/api/me/certificates` | GET | user | Felhasználó tanúsítványai |
| `/api/me/courses/{id}/certificate` | POST | user | Tanúsítvány igénylése |
| `/api/me/certificates/{cert_id}/pdf` | GET | user | PDF letöltése |
| `/api/verify/{cert_id}` | GET | — | Publikus verifikáció |

### `admin.py` — Admin panel

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/admin/stats` | GET | Platform statisztikák |
| `/api/admin/users` | GET | Felhasználók (lapozható, rendezhető) |
| `/api/admin/users/{id}/role` | PATCH | Szerepkör módosítása |
| `/api/admin/promotion-rules` | GET/POST | Előléptetési szabályok |
| `/api/admin/promotion-rules/{id}` | GET/PATCH/DELETE | Szabály kezelés |
| `/api/admin/promotion-log` | GET | Előléptetési napló |
| `/api/admin/courses/{id}` | DELETE | Kurzus törlés (kaszkád) |
| `/api/admin/modules/{id}` | DELETE | Modul törlés |
| `/api/admin/exercises/{id}` | DELETE | Feladat törlés |

### `webhooks.py` — GitHub webhook

A `POST /api/webhooks/github` a `workflow_run` eseményt figyeli (`action=completed`, `conclusion=success`). A repó nevéből (`{repo_prefix}-{username}`) azonosítja a feladatot és felhasználót, majd `completed`-re állítja a haladást.

## Szolgáltatások

| Szolgáltatás | Fájl | Felelősség |
|-------------|------|------------|
| certificate | `services/certificate.py` | `is_course_completed()` — kötelező feladatok teljesítés-ellenőrzése |
| pdf | `services/pdf.py` | Tanúsítvány PDF generálás (fpdf2) |
| qr | `services/qr.py` | QR kód a verifikációs URL-hez |
| github | `services/github.py` | GitHub Actions workflow állapot + `invite_user_to_org()` |
| progress | `services/progress.py` | `update_progress_for_user()` — GitHub CI alapú haladásfrissítés |
| promotion | `services/promotion.py` | `check_and_promote()` — tanúsítvány-alapú automatikus előléptetés |
| discord | `services/discord.py` | Webhook értesítések: `notify_enrollment()`, `notify_certificate()`, `notify_promotion()` |
| discord_bot | `services/discord_bot.py` | Bot API: `sync_discord_role()`, `lookup_discord_member()` |

## Linter (Ruff)

Konfiguráció: `backend/pyproject.toml`.

```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

```bash
ruff check .          # ellenőrzés
ruff check --fix .    # automatikus javítás
ruff format .         # formázás
make lint             # mind (backend + frontend)
make format           # mind javítás
```

## Tesztelés

```bash
cd backend
pytest -v                                    # összes teszt
pytest tests/test_auth.py -v                 # egy fájl
pytest tests/test_auth.py::test_me -v        # egy teszt
pytest --cov=app --cov-report=term           # lefedettség
make test                                    # projekt gyökeréből
```

### Tesztstruktúra

```
backend/tests/
├── conftest.py           # Közös fixture-ök (test DB, client, user fixtures)
├── test_admin.py         # Admin panel (11 teszt)
├── test_auth.py          # OAuth, JWT (8 teszt)
├── test_certificates.py  # Tanúsítványok, PDF, QR (12 teszt)
├── test_classroom.py     # GitHub Classroom webhook + import + mentor (19 teszt)
├── test_courses.py       # Kurzus CRUD, beiratkozás (14 teszt)
├── test_discord.py       # Discord webhook értesítések (8 teszt)
├── test_discord_sync.py  # Discord szerepkör szinkronizáció (20 teszt)
├── test_health.py        # Health endpoint
└── test_promotion.py     # Előléptetési rendszer (19 teszt)
```

### Teszt adatbázis

A tesztek **SQLite**-ot használnak (nem PostgreSQL-t). Minden teszt előtt a `setup_db` fixture újra létrehozza és utána törli a teljes sémát — a tesztek nem függenek egymástól.

### Felhasználó fixture-ök

| Fixture | Szerepkör | GitHub ID | Username |
|---------|-----------|-----------|----------|
| `student` | student | 11111 | `student1` |
| `admin` | admin | 22222 | `admin1` |
| `mentor` | mentor | 33333 | `mentor1` |

### Hitelesítés tesztekben

```python
from app.auth.jwt import create_access_token

def test_protected(client, student):
    token = create_access_token(student.id)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
```

### Tesztírási konvenciók

- Fájlnév: `test_<modul>.py`, függvény: `test_<mit_tesztelünk>`
- Happy path + error path egyaránt
- Mock-olt külső szolgáltatások (GitHub API, fájlrendszer)

## Adatbázis migrációk (Alembic)

```bash
cd backend
alembic revision --autogenerate -m "leírás"  # új migráció
alembic upgrade head                          # futtatás
alembic downgrade -1                          # visszavonás
alembic current                               # állapot

# Docker-ben:
docker compose exec backend alembic upgrade head
```

Minden modell változtatáshoz migráció szükséges. Munkafolyamat: modell módosítás → `alembic revision --autogenerate` → ellenőrzés → `alembic upgrade head` → `pytest`.

## Új endpoint hozzáadása

1. **Modell** (ha kell): `backend/app/models/`
2. **Migráció**: `alembic revision --autogenerate` → `alembic upgrade head`
3. **Router**: `backend/app/routers/` (Pydantic schema + dependency injection)
4. **Szolgáltatás** (ha üzleti logika kell): `backend/app/services/`
5. **Router regisztrálás** (ha új fájl): `backend/app/main.py`
6. **Teszt**: `backend/tests/test_<modul>.py`
7. **Ellenőrzés**: `pytest -v && make lint`
