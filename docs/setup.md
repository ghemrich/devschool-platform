# Telepítés és beállítás

A helyi fejlesztői környezet felállítása.

## Előfeltételek

- Python 3.12+
- Node.js 20+
- Docker és Docker Compose v2
- Git
- GitHub fiók (OAuth-hoz)

Ubuntu/Debian telepítés:

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip git docker.io docker-compose-v2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs
sudo usermod -aG docker $USER
# Kijelentkezés/bejelentkezés szükséges a docker csoport aktiválásához
```

## Gyors indítás (Docker)

```bash
git clone git@github.com:ghemrich/openschool-platform.git
cd openschool-platform
cp .env.example .env
# Szerkeszd a .env-et a GitHub OAuth adataiddal (lásd lent)

docker compose up --build -d
curl http://localhost/health
# → {"status": "ok"}
```

Szolgáltatások:

| Szolgáltatás | Port | Leírás |
|---|---|---|
| nginx | 80 | Reverse proxy |
| backend | 8000 | FastAPI API (belső) |
| db | 5432 | PostgreSQL 16 |
| frontend | — | React + Vite build (SPA) |

Makefile parancsok:

```bash
make up          # docker compose up --build -d
make down        # docker compose down
make test        # pytest futtatás
make migrate     # alembic upgrade head
make lint        # ruff + ESLint ellenőrzés
make format      # ruff + Prettier formázás
make dev-setup   # teljes dev környezet (venv, npm, hooks, .env)
make logs        # docker compose logs -f
make clean       # __pycache__, .pytest_cache törlése
make changelog   # CHANGELOG.md generálása (git-cliff)
```

## Gyors indítás (Docker nélkül)

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt

cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:4321
```

## GitHub OAuth beállítás

1. [GitHub Developer Settings](https://github.com/settings/developers) → **New OAuth App**
2. **Homepage URL:** `http://localhost`
3. **Authorization callback URL:** `http://localhost/api/auth/callback`
4. Másold a Client ID-t és Client Secret-et a `.env` fájlba

Élesben külön OAuth App kell az éles domain-nel: `https://yourdomain.com/api/auth/callback`

## Környezeti változók

A `.env` fájl a projekt gyökerében (soha ne commitold). Minta: `.env.example`.

### Alkalmazás

| Változó | Kötelező | Default | Leírás |
|---|---|---|---|
| `DATABASE_URL` | Igen | `sqlite:///./dev.db` | PostgreSQL URL. Docker-rel: `postgresql://user:pass@db:5432/dbname` |
| `SECRET_KEY` | Élesben | `change-me-in-production` | JWT aláíró kulcs. Generálás: `openssl rand -hex 32`. Production/staging módban nem maradhat az alapértelmezett — a backend ValueError-t dob |
| `BASE_URL` | Nem | `http://localhost` | Publikus URL (tanúsítvány QR kódokhoz, verifikációs linkekhez) |
| `ENVIRONMENT` | Nem | `development` | `development`, `staging`, vagy `production` |
| `ALLOWED_ORIGINS` | Nem | `http://localhost,http://localhost:4321` | CORS origins, vesszővel elválasztva |

### Docker Compose

| Változó | Leírás |
|---|---|
| `DB_USER` | PostgreSQL felhasználó (default: `openschool`) |
| `DB_PASSWORD` | PostgreSQL jelszó (default: `openschool`) |
| `DB_NAME` | Adatbázis neve (default: `openschool`) |

### GitHub OAuth

| Változó | Kötelező | Leírás |
|---|---|---|
| `GITHUB_CLIENT_ID` | Bejelentkezéshez | OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | Bejelentkezéshez | OAuth App Client Secret. Élesben kötelező |
| `GITHUB_ORG` | Classroom-hoz | GitHub szervezet neve |
| `GITHUB_ORG_ADMIN_TOKEN` | Classroom-hoz | PAT (classic) `admin:org` + `repo` scope-pal. A szerver ezzel kérdezi le a tanulók repóinak CI állapotát és hívja meg őket az org-ba. [Létrehozás](https://github.com/settings/tokens) |
| `GITHUB_WEBHOOK_SECRET` | Ajánlott | HMAC-SHA256 webhook kulcs. Nélküle a webhook végpont elutasít minden kérést (kivéve ha `WEBHOOK_SKIP_VERIFY=true`). Generálás: `openssl rand -hex 20` |
| `WEBHOOK_SKIP_VERIFY` | Nem | Ha `true`, webhook aláírás ellenőrzés kikapcsol. **Csak fejlesztéshez!** |

### Discord

| Változó | Leírás |
|---|---|
| `DISCORD_WEBHOOK_URL` | Webhook URL platform értesítésekhez (beiratkozás, tanúsítvány). Ha üres, átugródik |
| `DISCORD_BOT_TOKEN` | Bot token a szerepkör szinkronizációhoz. [Developer Portal](https://discord.com/developers/applications) → Bot → Reset Token |
| `DISCORD_GUILD_ID` | Szerver ID. Fejlesztői mód → jobb klikk szerverre → ID másolása |
| `DISCORD_ROLE_MAP` | Szerepkör leképezés: `"student:ROLE_ID,mentor:ROLE_ID,admin:ROLE_ID"` |

### ENVIRONMENT változó hatásai

| Hatás | development | staging | production |
|---|---|---|---|
| Log szint | DEBUG | DEBUG | INFO |
| Swagger UI (`/docs`) | Elérhető | Kikapcsolva | Kikapcsolva |
| SECRET_KEY validáció | Nincs | Kötelező megváltoztatni | Kötelező megváltoztatni |
| GITHUB_CLIENT_SECRET | Nem kötelező | Kötelező | Kötelező |
| GITHUB_WEBHOOK_SECRET | Nem kötelező | Ajánlott | Kötelező |

### GitHub Actions secrets/variables

A CI/CD workflow-k a GitHub repo beállításaiból olvassák:

**Variables** (Settings → Actions → Variables):

| Variable | Leírás |
|---|---|
| `VPS_HOST` | Éles szerver SSH host |
| `STAGING_HOST` | Staging szerver SSH host |

**Secrets** (Settings → Actions → Secrets):

| Secret | Leírás |
|---|---|
| `VPS_USER` / `VPS_SSH_KEY` | Éles szerver SSH hozzáférés |
| `STAGING_USER` / `STAGING_SSH_KEY` | Staging szerver SSH hozzáférés |
| `DISCORD_WEBHOOK_CI` | Discord webhook CI/CD értesítésekhez |

### VPS karbantartási konfig

A szerver oldali szkriptek `/etc/openschool-maintenance.conf` fájlt használják:

| Változó | Default | Leírás |
|---|---|---|
| `PROJECT_DIR` | `/opt/openschool` | Projekt könyvtár |
| `BACKUP_DIR` | `/opt/openschool-backups` | Mentések helye |
| `DISCORD_WEBHOOK` | — | Ops monitoring webhook |
| `CERT_DOMAIN` | — | Domain név SSL ellenőrzéshez |
| `RETENTION_DAYS` | `30` | Mentések megtartása napokban |
| `LOG_FILE` | `/var/log/openschool-maintenance.log` | Karbantartási napló |

### Validáció

A `backend/app/config.py` Pydantic validátorral ellenőrzi induláskor:

- `ENVIRONMENT=production` + alapértelmezett SECRET_KEY → **ValueError, nem indul**
- `ENVIRONMENT=production` + üres GITHUB_CLIENT_SECRET → **ValueError, nem indul**
- `ENVIRONMENT=production` + üres GITHUB_WEBHOOK_SECRET → **ValueError, nem indul**
- Üres GITHUB_ORG_ADMIN_TOKEN → org meghívás és haladás szinkronizálás kimarad, `POST /api/me/sync-progress` → 400

## Adatbázis és migrációk

A projekt Alembic-et használ:

```bash
cd backend
alembic upgrade head                              # migrációk futtatása
alembic revision --autogenerate -m "leírás"       # új migráció generálása
alembic downgrade -1                              # visszavonás
alembic current                                   # állapot

# Docker-ben:
docker compose exec backend alembic upgrade head
```

## VS Code beállítás

A `.vscode/` mappa előre konfigurált: Python interpreter (`.venv`), mentéskor formázás (Ruff, Prettier), 120 karakteres vonalzó, pytest felfedezés.

Ajánlott kiegészítők (automatikusan felajánlja):

| Kiegészítő | Funkció |
|---|---|
| Ruff (`charliermarsh.ruff`) | Python linter/formatter |
| Python (`ms-python.python`) | IntelliSense |
| ESLint (`dbaeumer.vscode-eslint`) | TS/React linter |
| Docker (`ms-azuretools.vscode-docker`) | Docker kezelés |
| GitLens (`eamodio.gitlens`) | Git történet |

## Pre-commit hookok

```bash
pre-commit install    # vagy: make install-hooks
```

A hookok automatikusan futnak commit előtt: trailing whitespace, YAML ellenőrzés, ruff lint+format, ESLint, Prettier, TypeScript. Ha egy hook javít valamit, a commit megszakad — `git add .` és próbáld újra.

## Hibaelhárítás

**„Permission denied" Docker-nél** — `sudo usermod -aG docker $USER`, majd kijelentkezés/bejelentkezés.

**„Module not found" Python import** — Ellenőrizd: `which python` → `.venv/bin/python`. Ha nem, `source .venv/bin/activate`.

**Port foglalt (8000 vagy 80)** — `sudo lsof -i :8000`, majd `sudo kill <PID>`.

**Adatbázis kapcsolati hiba** — `docker compose ps` → ha a db nem fut: `docker compose up -d db`. Lokálisan `localhost`-ot használj, nem `db`-t.
