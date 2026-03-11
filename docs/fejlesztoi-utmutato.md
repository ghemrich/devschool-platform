# Fejlesztői útmutató

> 📖 **Dokumentáció:** [Főoldal](../README.md) · [Architektúra](architektura.md) · [Telepítés](telepitesi-utmutato.md) · **Fejlesztői útmutató** · [Roadmap](jovokep-es-fejlesztesi-terv.md) · [Felhasználói útmutató](felhasznaloi-utmutato.md) · [GitHub Classroom](github-classroom-integraciot.md) · [Karbantartás](karbantartas-utmutato.md) · [Hozzájárulás](../CONTRIBUTING.md)

Ez az útmutató lépésről lépésre végigvezet az OpenSchool Platform fejlesztői környezetének felállításán.

## Előfeltételek

A fejlesztéshez az alábbi szoftverekre van szükség:

| Szoftver | Verzió | Leírás |
|----------|--------|--------|
| **Python** | 3.12+ | Backend nyelv |
| **Node.js** | 20+ | Frontend build |
| **Docker** és **Docker Compose** | latest | Lokális futtatás (PostgreSQL, nginx) |
| **Git** | 2.30+ | Verziókezelés |
| **VS Code** | latest | Ajánlott szerkesztő |

### Telepítés (Ubuntu/Debian)

```bash
# Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# Node.js 20 (NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# Docker
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER
# ⚠️ Kijelentkezés/bejelentkezés szükséges a docker csoport aktiválásához

# Git
sudo apt install git
```

---

## 1. Projekt klónozása

```bash
git clone https://github.com/ghemrich/openschool-platform.git
cd openschool-platform
```

---

## 2. Gyors indítás (`make dev-setup`)

A legegyszerűbb módja a fejlesztői környezet felállításának:

```bash
make dev-setup
```

Ez a parancs automatikusan:
- Létrehozza a Python virtuális környezetet (`.venv/`)
- Telepíti a backend függőségeket
- Telepíti a pre-commit hookokat
- Lemásolja az `.env.example` fájlt `.env`-ként
- Telepíti a frontend npm csomagokat

Ha inkább kézzel szeretnéd, olvasd tovább a következő fejezeteket.

---

## 3. Python virtuális környezet

```bash
# Venv létrehozása
python3 -m venv .venv

# Aktiválás
source .venv/bin/activate

# Függőségek telepítése
pip install --upgrade pip
pip install -r backend/requirements.txt

# Pre-commit telepítése
pip install pre-commit
```

> **Tipp:** A `.venv/` mappa a projekt gyökerében van, nem a `backend/`-ben. A VS Code automatikusan felismeri.

---

## 4. Környezeti változók

```bash
# .env fájl létrehozása a mintából
cp .env.example .env
```

A `.env` fájl tartalma fejlesztéshez:

```env
DB_USER=openschool
DB_PASSWORD=openschool
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:openschool@db:5432/openschool
SECRET_KEY=change-me-in-production
BASE_URL=http://localhost
GITHUB_CLIENT_ID=        # GitHub OAuth App Client ID
GITHUB_CLIENT_SECRET=    # GitHub OAuth App Client Secret
GITHUB_ORG=              # GitHub szervezet neve (Classroom-hoz)
GITHUB_WEBHOOK_SECRET=   # Webhook titkos kulcs
```

### GitHub OAuth App létrehozása (opcionális, login teszteléshez)

1. GitHub → Settings → Developer settings → OAuth Apps → New OAuth App
2. **Homepage URL:** `http://localhost`
3. **Authorization callback URL:** `http://localhost/api/auth/callback`
4. Másold be a Client ID-t és Client Secret-et a `.env` fájlba

---

## 5. Frontend telepítés

```bash
cd frontend
npm install
cd ..
```

---

## 6. Pre-commit hookok

A pre-commit hookok automatikusan ellenőrzik a kódot minden commit előtt (linter, formázó, stb.).

```bash
# Hookok telepítése (egyszer kell)
pre-commit install

# Vagy a Makefile-lal:
make install-hooks
```

### Mit csinálnak a hookok?

| Hook | Mit csinál |
|------|-----------|
| `trailing-whitespace` | Eltávolítja a sorvégi szóközöket |
| `end-of-file-fixer` | Biztosítja, hogy minden fájl újsorral végződjön |
| `check-yaml` | Ellenőrzi a YAML szintaxist |
| `check-added-large-files` | Figyelmeztet 500 KB-nál nagyobb fájlokra |
| `check-merge-conflict` | Megakadályozza merge conflict markerek commitolását |
| `ruff` | Python linter (hibák javítása automatikusan) |
| `ruff-format` | Python kódformázó |

### Kézi futtatás

```bash
# Összes hook futtatása az összes fájlon
pre-commit run --all-files

# Csak egy adott fájlon
pre-commit run --files backend/app/main.py
```

---

## 7. VS Code beállítás

A projekt tartalmaz előre konfigurált VS Code beállításokat (`.vscode/` mappa).

### Ajánlott kiegészítők

A VS Code automatikusan felajánlja az ajánlott kiegészítők telepítését a projekt megnyitásakor. Kézzel:

```
Ctrl+Shift+P → "Extensions: Show Recommended Extensions"
```

| Kiegészítő | Azonosító | Funkció |
|------------|-----------|---------|
| **Ruff** | `charliermarsh.ruff` | Python linter és formatter |
| **Python** | `ms-python.python` | Python támogatás, IntelliSense |
| **Python Debugger** | `ms-python.debugpy` | Python debugolás |
| **Astro** | `astro-build.astro-vscode` | Astro szintaxis, IntelliSense |
| **EditorConfig** | `editorconfig.editorconfig` | Egységes szerkesztő beállítások |
| **Docker** | `ms-azuretools.vscode-docker` | Docker fájlok, konténer kezelés |
| **GitHub Copilot** | `github.copilot` | AI kódkiegészítés |
| **GitLens** | `eamodio.gitlens` | Git történet, blame, diff |

### Beépített beállítások

A `.vscode/settings.json` automatikusan konfigurálja:

- **Python interpreter:** `.venv/bin/python`
- **Mentéskor formázás:** Ruff-fel (Python fájlokra)
- **Import rendezés:** Ruff-fel automatikusan
- **120 karakteres vonalzó:** Látható segédvonal a szerkesztőben
- **Pytest:** Automatikus teszt felfedezés
- **Fájlszűrés:** `__pycache__`, `.pytest_cache`, `pgdata` rejtve

---

## 8. Linter és formázó (Ruff)

A projekt [Ruff](https://docs.astral.sh/ruff/)-ot használ Python linterként és formázóként.

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

## 9. Tesztelés (pytest)

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

# Részletes kimenet hibánál
pytest -v --tb=long
```

### Tesztstruktúra

```
backend/tests/
├── test_admin.py         # Admin panel (statisztikák, felhasználók, törlés)
├── test_auth.py          # Autentikáció (OAuth, JWT)
├── test_certificates.py  # Tanúsítványok (PDF, QR)
├── test_classroom.py     # GitHub Classroom integráció
├── test_courses.py       # Kurzusok (CRUD, beiratkozás)
└── test_health.py        # Health endpoint
```

### Tesztírási konvenciók

- A tesztfájlok neve: `test_<modú>.py`
- A tesztfüggvények neve: `test_<mit_tesztelünk>`
- Minden tesztfájl saját SQLite adatbázist használ (`test_<modul>.db`)
- Fixture-ök az adott tesztfájl elején definiálva
- `client` fixture: `TestClient(app)` az API hívásokhoz
- Mock-olt külső szolgáltatások (GitHub API, fájlrendszer)

Példa:

```python
def test_list_courses_public(client):
    """Kurzuslista elérhető bejelentkezés nélkül."""
    response = client.get("/api/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## 10. Adatbázis és migrációk (Alembic)

### Migráció létrehozása

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
├── 001_initial.py
├── cefa39428d67_....py
└── a1b2c3d4e5f6_add_github_token_and_classroom_url.py
```

> **Fontos:** Minden modell változtatáshoz (új oszlop, tábla módosítás) migráció szükséges!

---

## 11. Docker fejlesztés

### Szolgáltatások indítása

```bash
# Összes szolgáltatás build + indítás
make up
# vagy:
docker compose up --build -d

# Logok követése
docker compose logs -f backend

# Leállítás
make down
# vagy:
docker compose down
```

### Docker Compose szolgáltatások

| Szolgáltatás | Port | Leírás |
|-------------|------|--------|
| `backend` | 8000 | FastAPI szerver |
| `db` | 5432 | PostgreSQL 16 |
| `nginx` | 80 | Reverse proxy + frontend |
| `frontend` | — | Astro build (nginx-be másolva) |

### Hasznos Docker parancsok

```bash
# Backend shell
docker compose exec backend bash

# Migráció futtatása konténerben
docker compose exec backend alembic upgrade head

# PostgreSQL konzol
docker compose exec db psql -U openschool -d openschool

# Újraépítés egy szolgáltatásra
docker compose up -d --build backend

# Adatbázis törlése és újrakezdés
docker compose down -v    # ⚠️ Töröl minden adatot!
docker compose up --build -d
```

---

## 12. Projektstruktúra

```
openschool-platform/
├── .editorconfig              # Szerkesztő beállítások
├── .env.example               # Környezeti változók mintája
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml             # CI: tesztek futtatása
│       └── cd.yml             # CD: VPS deploy
├── .pre-commit-config.yaml    # Pre-commit hookok
├── .vscode/
│   ├── extensions.json        # Ajánlott VS Code kiegészítők
│   └── settings.json          # Workspace beállítások
├── Makefile                   # Fejlesztői parancsok
├── CONTRIBUTING.md            # Hozzájárulási útmutató
├── docker-compose.yml         # Lokális Docker környezet
├── docker-compose.prod.yml    # Éles Docker környezet
│
├── backend/
│   ├── alembic/               # Adatbázis migrációk
│   ├── app/
│   │   ├── main.py            # FastAPI alkalmazás belépési pont
│   │   ├── config.py          # Beállítások (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy session
│   │   ├── auth/              # JWT + OAuth logika
│   │   ├── models/            # SQLAlchemy modellek
│   │   ├── routers/           # API végpontok
│   │   │   ├── admin.py       # Admin panel
│   │   │   ├── auth.py        # OAuth + JWT
│   │   │   ├── certificates.py
│   │   │   ├── courses.py     # CRUD + beiratkozás
│   │   │   ├── dashboard.py   # Haladás
│   │   │   └── webhooks.py    # GitHub webhookok
│   │   └── services/          # Üzleti logika (PDF, QR, GitHub)
│   ├── tests/                 # Pytest tesztek
│   ├── pyproject.toml         # Ruff + pytest konfig
│   └── requirements.txt       # Python függőségek
│
├── frontend/
│   ├── src/
│   │   ├── layouts/           # Astro layout-ok
│   │   └── pages/             # Oldalak (routing)
│       ├── admin/         # Admin oldalak (dashboard, users, courses)
│   ├── public/                # Statikus fájlok
│   ├── astro.config.mjs       # Astro konfiguráció
│   ├── package.json           # Node.js függőségek
│   └── tsconfig.json          # TypeScript konfig
│
├── nginx/
│   └── nginx.conf             # Nginx reverse proxy konfig
│
└── docs/
    ├── architektura.md           # Rendszer architektúra
│   ├── fejlesztoi-utmutato.md   # ← Ez a dokumentum
    ├── jovokep-es-fejlesztesi-terv.md
    └── telepitesi-utmutato.md    # Üzemeltetési útmutató
```

---

## 13. Fejlesztési munkafolyamat

### Új funkció hozzáadása (példa)

```bash
# 1. Friss develop branch
git checkout develop
git pull origin develop

# 2. Feature branch létrehozása
git checkout -b feature/user-profile

# 3. Backend modell módosítás
#    → backend/app/models/user.py szerkesztése

# 4. Migráció létrehozása
cd backend
alembic revision --autogenerate -m "add user profile fields"

# 5. Tesztek írása
#    → backend/tests/test_user_profile.py

# 6. API végpont létrehozása
#    → backend/app/routers/users.py

# 7. Frontend oldal
#    → frontend/src/pages/profile.astro

# 8. Ellenőrzés
pytest -v                          # tesztek
ruff check . && ruff format .      # linter + formázás

# 9. Commit (pre-commit hookok automatikusan futnak)
git add .
git commit -m "feat: add user profile page"

# 10. Push és PR
git push origin feature/user-profile
# → GitHub-on Pull Request nyitása develop-ba
```

### Branch elnevezés

| Prefix | Mikor használd | Példa |
|--------|---------------|-------|
| `feature/` | Új funkció | `feature/user-profile` |
| `fix/` | Hibajavítás | `fix/login-redirect` |
| `docs/` | Dokumentáció | `docs/api-guide` |
| `test/` | Teszt kiegészítés | `test/certificate-edge-cases` |

### Commit üzenetek

[Conventional Commits](https://www.conventionalcommits.org/) formátumot követünk:

```
feat: add user profile page
fix: correct OAuth redirect URL
docs: update developer setup guide
test: add certificate edge case tests
refactor: extract PDF generation service
chore: update dependencies
```

---

## 14. CI/CD pipeline

### CI (minden push és PR esetén)

A `.github/workflows/ci.yml` automatikusan:

1. **Lint lépés** — `ruff check` és `ruff format --check`
2. **Teszt lépés** — `pytest -v --tb=short` (csak ha a lint sikeres)

### CD (main branch push)

A `.github/workflows/cd.yml` automatikusan:

1. Tesztek futtatása (gate — deploy csak sikeres tesztek után)
2. SSH kapcsolat a VPS-hez
3. `git pull origin main`
4. Docker konténerek újraépítése
5. Migrációk futtatása
6. Health check

### CI/CD állapot ellenőrzése

Mindig ellenőrizd, hogy a CI zöld, mielőtt merge-ölsz:

1. **GitHub webes felület:** Repó → Actions fül → válaszd ki a workflow futtatást
2. **PR-ben:** A build státusz a PR alján látható (zöld pipák / piros X-ek)
3. **Badge (opcionális):** A README-be tehetsz CI badge-et:
   ```markdown
   ![CI](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml/badge.svg)
   ```

Ha a CI piros:
- Kattints a hibás lépésre a részletes logokért
- A lint hibák formázási problémák — futtasd: `make format`
- Teszt hibák — futtasd lokálisan: `make test`

---

## 15. Logok és hibakeresés

### Backend logok

```bash
# Logok követése valós időben
docker compose logs -f backend

# Utolsó 100 sor
docker compose logs --tail=100 backend

# Minden szolgáltatás logjai
docker compose logs -f

# Adatbázis logok
docker compose logs db
```

### Konténer állapot

```bash
# Futó szolgáltatások állapota
docker compose ps

# Egy konténer részletes információi
docker compose inspect backend

# Erőforrás-használat
docker stats
```

### Adatbázis debug

```bash
# PostgreSQL konzol
docker compose exec db psql -U openschool -d openschool

# Táblák listázása
\dt

# Felhasználók megnézése
SELECT id, username, role FROM users;

# Migrációs állapot
docker compose exec backend alembic current
```

### Production vs development különbségek

| Szempont | Fejlesztés | Produkció |
|----------|------------|------------|
| Docker Compose fájl | `docker-compose.yml` | `docker-compose.prod.yml` |
| Környezeti fájl | `.env` | `.env.prod` |
| `ENVIRONMENT` | `development` | `production` |
| Swagger UI (`/docs`) | ✅ Elérhető | ❌ Kikapcsolt |
| uvicorn `--reload` | Igen (auto-reload) | Nem |
| Backend port (8000) | Kintől is elérhető | Csak belső |
| DB port (5432) | Kintől is elérhető | Csak belső |
| Health check | Nincs | 30s interval |
| Restart policy | Nincs | `always` |
| Log rotáció | Nincs | 10MB / 3 fájl |

---

## 15. Makefile parancsok összefoglalása

```bash
make dev-setup     # Teljes fejlesztői környezet felállítása
make up            # Docker szolgáltatások indítása
make down          # Docker szolgáltatások leállítása
make test          # Tesztek futtatása
make lint          # Linter ellenőrzés (nem módosít)
make format        # Kód formázása (módosít)
make migrate       # Adatbázis migrációk futtatása
make install-hooks # Pre-commit hookok telepítése
```

---

## Hibaelhárítás

### „Permission denied" Docker parancsoknál

```bash
# Adj hozzá magad a docker csoporthoz
sudo usermod -aG docker $USER
# Majd jelentkezz ki és be, vagy:
newgrp docker
```

### „Module not found" Python importnál

```bash
# Ellenőrizd, hogy a venv aktív-e
which python
# Várt: .../openschool-platform/.venv/bin/python

# Ha nem, aktiváld:
source .venv/bin/activate
```

### Pre-commit hook hiba commitnál

```bash
# A hookok automatikusan javítják a formázási hibákat.
# Ilyenkor a commit megszakad, de a fájlok javítva lesznek.
# Csak add hozzá újra és commitolj:
git add .
git commit -m "feat: az üzenet"
```

### Adatbázis kapcsolati hiba

```bash
# Ellenőrizd, hogy a db konténer fut-e
docker compose ps

# Ha nem, indítsd el
docker compose up -d db

# Lokális fejlesztéshez a DATABASE_URL legyen:
# postgresql://openschool:openschool@localhost:5432/openschool
# (localhost, nem db!)
```

### Port foglalt (8000 vagy 80)

```bash
# Melyik folyamat használja a portot?
sudo lsof -i :8000
sudo lsof -i :80

# Folyamat leállítása
sudo kill <PID>
```
