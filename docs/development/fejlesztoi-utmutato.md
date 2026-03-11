# Fejlesztői útmutató

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · **Fejlesztői útmutató** · [Backend](backend-fejlesztes.md) · [Frontend](frontend-fejlesztes.md) · [Tesztelés](tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a közös fejlesztői környezet felállítását és a megosztott eszközöket írja le. A backend és frontend specifikus részletekért lásd:

- **[Backend fejlesztés](backend-fejlesztes.md)** — Python venv, FastAPI routerek, modellek, szolgáltatások, Ruff, pytest, Alembic migrációk
- **[Frontend fejlesztés](frontend-fejlesztes.md)** — Astro projekt, oldalak, komponensek, kliens oldali JS, stílusok, admin panel

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

## 3. Python és Frontend telepítés

### Backend (Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements-dev.txt
```

Részletek: [Backend fejlesztés — 1. Python virtuális környezet](backend-fejlesztes.md#1-python-virtuális-környezet)

### Frontend (Node.js)

```bash
cd frontend
npm install
cd ..
```

Részletek: [Frontend fejlesztés — 1. Telepítés és indítás](frontend-fejlesztes.md#1-telepítés-és-indítás)

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

## 5. Pre-commit hookok

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

## 6. VS Code beállítás

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

## 7. Linter, tesztek és migrációk

Ezek a témák a backend fejlesztési útmutatóban vannak részletesen leírva:

| Téma | Referencia |
|------|-----------|
| **Ruff** (linter + formázó) | [Backend — 7. Linter és formázó](backend-fejlesztes.md#7-linter-és-formázó-ruff) |
| **pytest** (tesztelés) | [Backend — 8. Tesztelés](backend-fejlesztes.md#8-tesztelés-pytest) |
| **Alembic** (migrációk) | [Backend — 9. Adatbázis migrációk](backend-fejlesztes.md#9-adatbázis-migrációk-alembic) |

Gyors parancsok:

```bash
make lint       # Ruff ellenőrzés (nem módosít)
make format     # Ruff formázás (módosít)
make test       # pytest futtatása
make migrate    # Alembic migrációk futtatása
```

---

## 8. Változásnapló (git-cliff)

A projekt [git-cliff](https://git-cliff.org/)-et használja a `CHANGELOG.md` automatikus generálásához a commit történetből. A conventional commit prefixek (`feat:`, `fix:`, `refactor:`, stb.) alapján csoportosítja a változásokat.

### Konfiguráció

A beállítások a `cliff.toml` fájlban vannak a projekt gyökerében. A konfiguráció határozza meg:

| Beállítás | Leírás |
|-----------|--------|
| `commit_parsers` | Commit prefix → kategória hozzárendelés (🚀 Features, 🐛 Bug Fixes, stb.) |
| `conventional_commits` | Conventional commit formátum értelmezése |
| `sort_commits` | Commit sorrend a changelog-ban |
| `postprocessors` | `<REPO>` placeholder cseréje a GitHub URL-re |

### Felismert commit prefixek

| Prefix | Kategória |
|--------|-----------|
| `feat:` | 🚀 Features |
| `fix:` | 🐛 Bug Fixes |
| `refactor:` | 🚜 Refactor |
| `docs:` | 📚 Documentation |
| `test:` | 🧪 Testing |
| `perf:` | ⚡ Performance |
| `chore:`, `ci:` | ⚙️ Miscellaneous Tasks |
| `security:` | 🛡️ Security |
| `revert:` | ◀️ Revert |

### Használat

```bash
# CHANGELOG.md újragenerálása a teljes commit történetből
git-cliff -o CHANGELOG.md

# Előnézet (stdout-ra, fájl módosítás nélkül)
git-cliff

# Csak az utolsó tag óta történt változások
git-cliff --latest

# Csak az unreleased változások
git-cliff --unreleased
```

### Mikor kell futtatni?

A `CHANGELOG.md`-t **nem kell minden commitnál** frissíteni. Az ajánlott munkafolyamat:

1. Fejlesztés során használj conventional commit prefixeket (lásd [Karbantartás — Commit konvenciók](../operations/karbantartas-utmutato.md))
2. Release előtt futtasd: `git-cliff -o CHANGELOG.md`
3. Commitold a frissített CHANGELOG-ot a release commit részeként
4. Tageld a release-t: `git tag v1.0.0`

### Telepítés

Ha a `git-cliff` nincs telepítve a gépen:

```bash
pip install git-cliff
```

---

## 9. Docker fejlesztés

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

## 10. Projektstruktúra

```
openschool-platform/
├── .editorconfig              # Szerkesztő beállítások
├── .env.example               # Környezeti változók mintája
├── .github/
│   ├── dependabot.yml         # Dependabot konfig
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml             # CI: tesztek futtatása
│       └── cd.yml             # CD: VPS deploy
├── .pre-commit-config.yaml    # Pre-commit hookok
├── .vscode/
│   ├── extensions.json        # Ajánlott VS Code kiegészítők
│   └── settings.json          # Workspace beállítások
├── CHANGELOG.md               # Automatikus változásnapló (git-cliff)
├── CONTRIBUTING.md            # Hozzájárulási útmutató
├── LICENSE                    # MIT licenc
├── Makefile                   # Fejlesztői parancsok
├── README.md                  # Projekt leírás
├── cliff.toml                 # git-cliff konfiguráció
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
│   │   ├── services/          # Üzleti logika (PDF, QR, GitHub, progress)
│   ├── tests/                 # Pytest tesztek
│   │   └── conftest.py        # Közös test fixture-ök
│   ├── pyproject.toml         # Ruff + pytest konfig
│   ├── requirements.txt       # Produkciós Python függőségek
│   └── requirements-dev.txt   # Fejlesztői függőségek (teszt, lint)
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Astro komponensek
│   │   ├── layouts/           # Astro layout-ok
│   │   ├── lib/               # Kliens oldali JS modulok
│   │   ├── pages/             # Oldalak (routing)
│   │   │   └── admin/         # Admin oldalak (dashboard, users, courses)
│   │   └── styles/            # CSS stílusok
│   ├── public/                # Statikus fájlok
│   ├── astro.config.mjs       # Astro konfiguráció
│   ├── package.json           # Node.js függőségek
│   └── tsconfig.json          # TypeScript konfig
│
├── nginx/
│   └── nginx.conf             # Nginx reverse proxy konfig
│
├── scripts/
│   └── backup.sh              # Biztonsági mentés szkript
│
├── tesztek/                   # Kurzus tesztek (modul-01..07)
│   ├── conftest.py
│   └── modul-01..07/
│
└── docs/
    ├── getting-started/               # Architektúra, telepítés, env változók
    ├── development/                   # Fejlesztői, backend, frontend, tesztelés
    ├── reference/                     # API referencia, adatbázis séma
    ├── operations/                    # Karbantartás, automatizálás
    ├── integrations/                  # GitHub Classroom, Discord
    ├── guides/                        # Felhasználói útm., dokumentálás
    └── jovokep-es-fejlesztesi-terv.md # Roadmap
```

---

## 11. Fejlesztési munkafolyamat

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

# 8. Dokumentáció frissítése
#    → docstring-ek az új függvényekhez
#    → docs/ releváns fájlok frissítése (api-referencia.md, stb.)
#    Lásd: docs/guides/dokumentacios-utmutato.md

# 9. Ellenőrzés
pytest -v                          # tesztek
ruff check . && ruff format .      # linter + formázás

# 10. Commit (pre-commit hookok automatikusan futnak)
git add .
git commit -m "feat: add user profile page"

# 11. Push és PR
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

## 12. CI/CD pipeline

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

## 13. Logok és hibakeresés

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

## 14. Makefile parancsok összefoglalása

```bash
# Fejlesztés
make dev-setup     # Teljes fejlesztői környezet felállítása (venv, npm, hooks, .env)
make up            # Docker szolgáltatások indítása
make down          # Docker szolgáltatások leállítása
make test          # Tesztek futtatása
make lint          # Linter ellenőrzés (nem módosít)
make format        # Kód formázása (módosít)
make migrate       # Adatbázis migrációk futtatása
make install-hooks # Pre-commit hookok telepítése
make clean         # __pycache__, .pytest_cache, *.pyc törlése
make logs          # Docker logok követése (tail=100)
make changelog     # CHANGELOG.md generálása (git-cliff)

# Karbantartás (lásd: ../operations/automatizalas-beallitas.md)
make maintenance-health   # Health check
make maintenance-backup   # Adatbázis mentés
make maintenance-daily    # Teljes napi karbantartás
make maintenance-weekly   # Teljes heti karbantartás
make maintenance-monthly  # Teljes havi karbantartás
make install-cron         # Cron job-ok telepítése (sudo)
make security-check       # Biztonsági ellenőrzés
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
