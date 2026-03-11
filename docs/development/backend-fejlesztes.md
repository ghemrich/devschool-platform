# Backend fejlesztés (FastAPI)

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](fejlesztoi-utmutato.md) · **Backend** · [Frontend](frontend-fejlesztes.md) · [Tesztelés](tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a backend fejlesztéséhez tartalmaz mindent: Python környezet, FastAPI szerkezet, modellek, routerek, szolgáltatások, tesztelés, migráció és linter beállítás.

> **Általános fejlesztői útmutató** (Docker, pre-commit, VS Code, Git, CI/CD, Makefile): [fejlesztoi-utmutato.md](fejlesztoi-utmutato.md)
> **Dokumentálási útmutató** (docstring-ek, API docs, README karbantartás): [dokumentacios-utmutato.md](../guides/dokumentacios-utmutato.md)

---

## 1. Python virtuális környezet

```bash
# Venv létrehozása (projekt gyökeréből)
python3 -m venv .venv

# Aktiválás
source .venv/bin/activate

# Függőségek telepítése
pip install --upgrade pip
pip install -r backend/requirements-dev.txt
```

### Függőségek struktúra

| Fájl | Tartalom | Használat |
|------|----------|-----------|
| `requirements.txt` | Produkciós csomagok (FastAPI, SQLAlchemy, stb.) | Docker build, éles deploy |
| `requirements-dev.txt` | Fejlesztői eszközök (pytest, ruff, git-cliff) | Lokális fejlesztés, CI |

A `requirements-dev.txt` első sora `-r requirements.txt`, ami automatikusan telepíti a produkciós csomagokat is.

> **Tipp:** A `.venv/` mappa a projekt gyökerében van, nem a `backend/`-ben. A VS Code automatikusan felismeri.

### Kulcs függőségek

| Csomag | Cél |
|--------|-----|
| `fastapi` | Web keretrendszer |
| `sqlalchemy` | ORM (adatbázis kezelés) |
| `alembic` | Adatbázis migrációk |
| `pydantic-settings` | Konfiguráció környezeti változókból |
| `python-jose` | JWT tokenek |
| `httpx` | HTTP kliens a GitHub API-hoz |
| `fpdf2` | Tanúsítvány PDF generálás |
| `qrcode` | QR kód generálás tanúsítványokhoz |
| `psycopg2-binary` | PostgreSQL driver |
| `pytest` | Tesztelés |

---

## 2. Könyvtárstruktúra

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
│   │   └── certificate.py    # Certificate (UUID, PDF útvonal)
│   ├── routers/
│   │   ├── admin.py          # /api/admin/* — statisztikák, felhasználók, törlés
│   │   ├── auth.py           # /api/auth/* — OAuth, bejelentkezés, profil
│   │   ├── certificates.py   # /api/me/certificates/*, /api/verify/*
│   │   ├── courses.py        # /api/courses/* — CRUD, beiratkozás, modulok
│   │   ├── dashboard.py      # /api/me/* — haladás, dashboard, sync
│   │   └── webhooks.py       # /api/webhooks/* — GitHub webhook fogadás
│   └── services/
│       ├── certificate.py    # is_course_completed() — teljesítés ellenőrzés
│       ├── pdf.py            # PDF generálás fpdf2-vel
│       ├── qr.py             # QR kód generálás
│       ├── github.py         # GitHub Actions állapot lekérdezés
│       └── progress.py       # Haladás frissítés GitHub CI alapján
├── alembic/                  # Adatbázis migrációk
├── tests/                    # pytest tesztek
├── pyproject.toml            # Ruff + pytest konfig
├── requirements.txt          # Produkciós csomagok
└── requirements-dev.txt      # Fejlesztői csomagok
```

---

## 3. Konfiguráció (`config.py`)

A `pydantic-settings` kezeli a beállításokat. A `.env` fájlból (vagy környezeti változókból) töltődnek be:

```python
class Settings(BaseSettings):
    database_url: str
    secret_key: str = "change-me-in-production"
    base_url: str = "http://localhost"
    environment: str = "development"          # development | production
    allowed_origins: str = "http://localhost"
    github_client_id: str = ""
    github_client_secret: str = ""
    github_org: str = ""
    github_webhook_secret: str = ""
```

Az `environment` beállítás hatása:

| Érték | Log szint | Swagger UI | SECRET_KEY validáció |
|-------|-----------|------------|----------------------|
| `development` | DEBUG | ✅ Elérhető (`/docs`) | Nincs |
| `production` | INFO | ❌ Kikapcsolt | Figyelmeztetés ha alapértelmezett |

---

## 4. Adatmodell

### Táblák

| Tábla | Kulcs mezők |
|-------|-------------|
| `users` | github_id, username, email, avatar_url, role (student/mentor/admin), github_token |
| `courses` | name, description |
| `modules` | course_id, name, order |
| `exercises` | module_id, name, repo_prefix, order, required, classroom_url |
| `enrollments` | user_id, course_id, enrolled_at |
| `progress` | user_id, exercise_id, status (not_started/in_progress/completed), github_repo |
| `certificates` | cert_id (UUID), user_id, course_id, issued_at, pdf_path |

### Kapcsolatok

```
User ──┬── Enrollment ── Course ── Module ── Exercise
       ├── Progress ──────────────────────── Exercise
       └── Certificate ── Course
```

### Szerepkörök

| Szerepkör | Jogosultságok |
|-----------|---------------|
| `student` | Beiratkozás kurzusokra, haladás megtekintése, tanúsítvány igénylése |
| `mentor` | Minden, amit a student + diákok haladásának megtekintése |
| `admin` | Minden + kurzusok/modulok/feladatok CRUD, felhasználók kezelése, admin panel |

---

## 5. Routerek (API végpontok)

Minden router a `backend/app/routers/` mappában van és a `main.py`-ban regisztrálva.

### `auth.py` — Autentikáció

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/auth/login` | GET | GitHub OAuth átirányítás |
| `/api/auth/callback` | GET | OAuth callback — user létrehozás/frissítés, JWT generálás |
| `/api/auth/me` | GET | Aktuális felhasználó adatai |
| `/api/auth/refresh` | POST | Új access token a refresh token cookie-ból |
| `/api/auth/logout` | POST | Refresh token cookie törlése |

**OAuth flow:** A callback végpont cseréli a GitHub kódot access tokenre, lekérdezi a felhasználó adatait, majd JWT-t generál. A token a `/login#token=eyJ...` fragment-ben tér vissza. A refresh token httpOnly cookie-ként tárolódik.

### `courses.py` — Kurzusok

| Endpoint | Metódus | Auth | Leírás |
|----------|---------|------|--------|
| `/api/courses` | GET | — | Kurzuslista (lapozható: skip, limit) |
| `/api/courses/{id}` | GET | — | Kurzus részletei (modulok, feladatok) |
| `/api/courses` | POST | admin | Kurzus létrehozása |
| `/api/courses/{id}` | PUT | admin | Kurzus szerkesztése |
| `/api/courses/{id}/modules` | POST | admin | Modul hozzáadása |
| `/api/courses/{id}/modules/{mid}/exercises` | POST | admin | Feladat hozzáadása |
| `/api/courses/{id}/enroll` | POST | user | Beiratkozás |
| `/api/courses/{id}/unenroll` | POST | user | Leiratkozás |
| `/api/courses/{id}/students` | GET | mentor | Diákok listája haladással |

### `dashboard.py` — Felhasználói haladás

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/me/dashboard` | GET | Dashboard — összes kurzus haladás összesítve |
| `/api/me/courses` | GET | Beiratkozott kurzusok listája haladással |
| `/api/me/courses/{id}/progress` | GET | Részletes haladás (modulonként, feladatonként) |
| `/api/me/courses/{id}/progress` | POST | Feladat manuális teljesítés jelölése |
| `/api/me/sync-progress` | POST | Haladás szinkronizálása GitHub CI-ból |

### `certificates.py` — Tanúsítványok

| Endpoint | Metódus | Auth | Leírás |
|----------|---------|------|--------|
| `/api/me/certificates` | GET | user | Felhasználó tanúsítványai |
| `/api/me/courses/{id}/certificate` | POST | user | Tanúsítvány igénylése (befejezett kurzus) |
| `/api/me/certificates/{cert_id}/pdf` | GET | user | PDF letöltése |
| `/api/verify/{cert_id}` | GET | — | Publikus verifikáció |

### `admin.py` — Admin panel

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/admin/stats` | GET | Platform statisztikák |
| `/api/admin/users` | GET | Felhasználók (lapozható, rendezhető) |
| `/api/admin/users/{id}/role` | PATCH | Szerepkör módosítása |
| `/api/admin/courses/{id}` | DELETE | Kurzus törlése (kaszkád) |
| `/api/admin/modules/{id}` | DELETE | Modul törlése |
| `/api/admin/exercises/{id}` | DELETE | Feladat törlése |

### `webhooks.py` — GitHub integráció

| Endpoint | Metódus | Leírás |
|----------|---------|--------|
| `/api/webhooks/github` | POST | GitHub `workflow_run` webhook fogadása |

A webhook a `workflow_run` eseményt figyeli (`action=completed`, `conclusion=success`). A repó nevéből (`{repo_prefix}-{username}`) azonosítja a feladatot és a felhasználót, majd automatikusan `completed`-re állítja a haladást.

---

## 6. Szolgáltatások (services)

| Szolgáltatás | Fájl | Felelősség |
|-------------|------|------------|
| **certificate** | `services/certificate.py` | `is_course_completed()` — ellenőrzi, hogy az összes kötelező feladat teljesítve van-e |
| **pdf** | `services/pdf.py` | Tanúsítvány PDF generálás (fpdf2) |
| **qr** | `services/qr.py` | QR kód generálás a verifikációs URL-hez |
| **github** | `services/github.py` | GitHub Actions workflow állapot lekérdezés egyéni repókhoz |
| **progress** | `services/progress.py` | `update_progress_for_user()` — GitHub CI alapján haladás frissítés |

---

## 7. Linter és formázó (Ruff)

### Konfiguráció

A beállítások a `backend/pyproject.toml` fájlban vannak:

```toml
[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

| Szabálycsoport | Mit ellenőriz |
|----------------|---------------|
| `E` | PEP 8 stílus hibák |
| `F` | Pyflakes (nem használt importok, változók) |
| `I` | Import sorrend (isort) |
| `N` | Elnevezési konvenciók (PEP 8) |
| `W` | PEP 8 figyelmeztetések |

### Használat

```bash
# Linter futtatása (csak ellenőrzés)
cd backend
ruff check .

# Linter automatikus javítással
ruff check --fix .

# Formázó (csak ellenőrzés)
ruff format --check .

# Formázó (módosítás)
ruff format .

# Mindkettő egyszerre (Makefile)
make lint     # ellenőrzés
make format   # javítás
```

---

## 8. Tesztelés (pytest)

### Tesztek futtatása

```bash
# Összes teszt
cd backend
pytest -v

# Vagy a Makefile-lal (projekt gyökeréből):
make test

# Egy adott tesztfájl
pytest tests/test_auth.py -v

# Egy adott teszt
pytest tests/test_auth.py::test_me_with_valid_token -v

# Lefedettség
pytest --cov=app --cov-report=term
```

### Tesztstruktúra

```
backend/tests/
├── conftest.py           # Közös fixture-ök (test DB, client)
├── test_admin.py         # Admin panel (statisztikák, felhasználók, törlés)
├── test_auth.py          # Autentikáció (OAuth, JWT)
├── test_certificates.py  # Tanúsítványok (PDF, QR)
├── test_classroom.py     # GitHub Classroom integráció
├── test_courses.py       # Kurzusok (CRUD, beiratkozás)
└── test_health.py        # Health endpoint
```

### Tesztírási konvenciók

- Fájlnév: `test_<modul>.py`, függvénynév: `test_<mit_tesztelünk>`
- Minden tesztfájl saját SQLite adatbázist használ (`test_<modul>.db`)
- `client` fixture: `TestClient(app)` az API hívásokhoz
- Mock-olt külső szolgáltatások (GitHub API, fájlrendszer)
- Happy path + error path lefedése

Példa:

```python
def test_list_courses_public(client):
    """Kurzuslista elérhető bejelentkezés nélkül."""
    response = client.get("/api/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## 9. Adatbázis migrációk (Alembic)

### Gyakori parancsok

```bash
cd backend

# Új migráció generálása (autogenerate a modell változásokból)
alembic revision --autogenerate -m "add user profile fields"

# Migrációk futtatása
alembic upgrade head

# Egy lépés visszavonása
alembic downgrade -1

# Jelenlegi verzió
alembic current

# Migráció történet
alembic history
```

### Migrációs fájlok

```
backend/alembic/versions/
├── 5492c9d27e5f_add_users_table.py
├── 38fa8a895630_add_course_module_exercise_enrollment_.py
├── a1b2c3d4e5f6_add_github_token_and_classroom_url.py
└── cefa39428d67_add_certificates_table_and_exercise_.py
```

> **Fontos:** Minden modell változtatáshoz (új oszlop, tábla módosítás) migráció szükséges!

### Munkafolyamat

1. Modell módosítása (`backend/app/models/`)
2. Migráció generálása: `alembic revision --autogenerate -m "leírás"`
3. Migráció ellenőrzése: `cat alembic/versions/<latest>.py`
4. Migráció futtatása: `alembic upgrade head`
5. Tesztek futtatása: `pytest`

---

## 10. Új endpoint hozzáadása (lépésről lépésre)

1. **Modell** (ha új tábla/oszlop kell): `backend/app/models/` — SQLAlchemy modell
2. **Migráció**: `alembic revision --autogenerate -m "leírás"` → `alembic upgrade head`
3. **Router**: `backend/app/routers/` — FastAPI endpoint (Pydantic schema + dependency injection)
4. **Szolgáltatás** (ha üzleti logika kell): `backend/app/services/`
5. **Router regisztrálás** (ha új fájl): `backend/app/main.py` (`app.include_router(...)`)
6. **Teszt**: `backend/tests/test_<modul>.py`
7. **Ellenőrzés**: `pytest -v && make lint`

---

## 11. Logok és hibakeresés

```bash
# Backend logok követése
docker compose logs -f backend

# Utolsó 100 sor
docker compose logs --tail=100 backend

# Hiba szűrés
docker compose logs backend | grep -i error

# PostgreSQL konzol
docker compose exec db psql -U openschool -d openschool

# Migrációs állapot
docker compose exec backend alembic current
```

### Production vs development

| Szempont | Fejlesztés | Produkció |
|----------|------------|------------|
| `ENVIRONMENT` | `development` | `production` |
| Swagger UI (`/docs`) | ✅ Elérhető | ❌ Kikapcsolt |
| uvicorn `--reload` | Igen (auto-reload) | Nem |
| Backend port (8000) | Kintről is elérhető | Csak nginx-en keresztül |
| DB port (5432) | Kintről is elérhető | Csak belső |

---

## 12. Hasznos Docker parancsok

```bash
# Backend shell
docker compose exec backend bash

# Migráció futtatása konténerben
docker compose exec backend alembic upgrade head

# PostgreSQL konzol
docker compose exec db psql -U openschool -d openschool

# Újraépítés csak a backend-re
docker compose up -d --build backend

# Adatbázis törlése és újrakezdés
docker compose down -v    # ⚠️ Töröl minden adatot!
docker compose up --build -d
```
