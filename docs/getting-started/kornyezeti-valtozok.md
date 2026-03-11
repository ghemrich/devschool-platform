# OpenSchool Platform — Környezeti változók referencia

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](architektura.md) · [Telepítés](telepitesi-utmutato.md) · **Környezeti változók** · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez a dokumentum az összes környezeti változót egy helyen összesíti: alkalmazás, Docker, GitHub Actions, VPS szkriptek.

---

## 1. Alkalmazás környezeti változók (`.env`)

Ezeket a `.env` fájlban kell beállítani a projekt gyökerében. A backend a `pydantic-settings` könyvtárral olvassa be (`backend/app/config.py`). A `.env.example` fájl tartalmaz mintát.

### Adatbázis

| Változó | Kötelező | Default | Leírás |
|---------|----------|---------|--------|
| `DB_USER` | Docker-hez | `openschool` | PostgreSQL felhasználónév (docker-compose használja) |
| `DB_PASSWORD` | Docker-hez | `openschool` | PostgreSQL jelszó (docker-compose használja) |
| `DB_NAME` | Docker-hez | `openschool` | Adatbázis neve (docker-compose használja) |
| `DATABASE_URL` | Igen | `sqlite:///./dev.db` | Teljes adatbázis URL. Docker-rel: `postgresql://user:pass@db:5432/dbname`. Tesztekhez: `sqlite:///./test.db` automatikusan |

> **Ha nincs `DATABASE_URL` megadva**, a backend SQLite-ot használ fejlesztéshez (`dev.db`). Docker Compose-ban a `.env` fájlból olvassa a PostgreSQL URL-t.

### Biztonság

| Változó | Kötelező | Default | Leírás |
|---------|----------|---------|--------|
| `SECRET_KEY` | **Élesben kötelező** | `change-me-in-production` | JWT token aláíró kulcs (HS256). **Éles módban nem maradhat az alapértelmezett érték** — a backend `ValueError`-t dob induláskor. Generálás: `openssl rand -hex 32` |

> **Fontos:** Ha `ENVIRONMENT=production` és a `SECRET_KEY` az alapértelmezett, a backend nem indul el.

### Alkalmazás

| Változó | Kötelező | Default | Leírás |
|---------|----------|---------|--------|
| `BASE_URL` | Nem | `http://localhost` | A platform publikus URL-je. A tanúsítvány QR kódok és verifikációs linkek ezt használják (pl. `https://school.example.com`) |
| `ENVIRONMENT` | Nem | `development` | `development`, `staging`, vagy `production` |
| `ALLOWED_ORIGINS` | Nem | `http://localhost,http://localhost:4321` | CORS engedélyezett origin-ek, vesszővel elválasztva |

### Az `ENVIRONMENT` változó hatásai

| Hatás | `development` | `staging` | `production` |
|-------|---------------|-----------|--------------|
| Log szint | `DEBUG` | `DEBUG` | `INFO` |
| Swagger UI (`/docs`) | ✅ Elérhető | ✅ Elérhető | ❌ Kikapcsolva |
| ReDoc (`/redoc`) | ✅ Elérhető | ✅ Elérhető | ❌ Kikapcsolva |
| SECRET_KEY validáció | Nem | Nem | **Kötelező megváltoztatni** |
| GITHUB_CLIENT_SECRET | Nem kötelező | Nem kötelező | **Kötelező** |
| GITHUB_WEBHOOK_SECRET | Nem kötelező | Nem kötelező | Figyelmeztetés, ha hiányzik |

### GitHub OAuth

| Változó | Kötelező | Default | Leírás |
|---------|----------|---------|--------|
| `GITHUB_CLIENT_ID` | Bejelentkezéshez | `""` | GitHub OAuth App Client ID. Létrehozás: [github.com/settings/developers](https://github.com/settings/developers) |
| `GITHUB_CLIENT_SECRET` | Bejelentkezéshez | `""` | GitHub OAuth App Client Secret. **Élesben kötelező** |
| `GITHUB_ORG` | Nem | `""` | GitHub szervezet neve a repók kereséséhez. Ha üres, a felhasználó saját fiókja alatt keres |
| `GITHUB_WEBHOOK_SECRET` | Ajánlott | `""` | Webhook HMAC-SHA256 aláíró kulcs. Ha üres, webhook aláírás ellenőrzés kikapcsolt. Generálás: `openssl rand -hex 20` |

---

## 2. Docker Compose változók

A `docker-compose.yml` és `docker-compose.prod.yml` a `.env` fájlból olvassa ezeket.

| Változó | Használat | Leírás |
|---------|-----------|--------|
| `DB_USER` | PostgreSQL init + backend | Adatbázis felhasználó |
| `DB_PASSWORD` | PostgreSQL init + backend | Adatbázis jelszó |
| `DB_NAME` | PostgreSQL init + backend | Adatbázis neve |
| `DATABASE_URL` | Backend container | Teljes connection string |
| `SECRET_KEY` | Backend container | JWT kulcs |
| `BASE_URL` | Backend container | Publikus URL |
| `ENVIRONMENT` | Backend container | Környezet típus |
| `ALLOWED_ORIGINS` | Backend container | CORS beállítás |
| `GITHUB_CLIENT_ID` | Backend container | OAuth azonosító |
| `GITHUB_CLIENT_SECRET` | Backend container | OAuth titkos kulcs |
| `GITHUB_ORG` | Backend container | Szervezet |
| `GITHUB_WEBHOOK_SECRET` | Backend container | Webhook secret |

---

## 3. GitHub Actions secrets

A CI/CD workflow-k (`ci.yml`, `cd.yml`) ezeket a GitHub repository secrets-ből olvassák.

| Secret | Workflow | Kötelező | Leírás |
|--------|----------|----------|--------|
| `DISCORD_WEBHOOK_CI` | `ci.yml`, `cd.yml` | Nem | Discord webhook URL CI/CD értesítésekhez. Ha nincs megadva, az értesítés átugródik |
| `STAGING_HOST` | `cd.yml` | Staging-hez | Staging szerver SSH host |
| `VPS_HOST` | `cd.yml` | Deploy-hoz | Éles szerver SSH host |

> **Beállítás:** GitHub repó → Settings → Secrets and variables → Actions → New repository secret

### SSH kulcs beállítás a CD-hez

A `cd.yml` az `appleboy/ssh-action@v1` akciót használja. A cél szerveren az SSH kulcs alapú hitelesítést kell beállítani — lásd [Automatizálás](../operations/automatizalas-beallitas.md) és [Telepítés](telepitesi-utmutato.md).

---

## 4. VPS szkriptek konfigurációja

A szerver oldali szkriptek (`scripts/maintenance.sh`, `scripts/backup.sh`) egy külön konfigurációs fájlt használnak:

**Fájl:** `/etc/openschool-maintenance.conf`

| Változó | Default | Leírás |
|---------|---------|--------|
| `PROJECT_DIR` | `/opt/openschool` | Projekt könyvtár a szerveren |
| `BACKUP_DIR` | `/opt/openschool-backups` | Biztonsági mentések helye |
| `DISCORD_WEBHOOK` | `""` | Discord webhook URL ops monitoring értesítésekhez (backup hiba, health check, stb.) |
| `CERT_DOMAIN` | `""` | Domain név az SSL tanúsítvány lejárat ellenőrzéshez |
| `RETENTION_DAYS` | `30` | Régi backup-ok megtartási ideje napokban |
| `LOG_FILE` | `/var/log/openschool-maintenance.log` | Karbantartási napló fájl útvonala |

> **Telepítés:** A `scripts/bootstrap-vps.sh` és `scripts/provision.sh` szkriptek automatikusan létrehozzák ezt a fájlt.

---

## 5. Környezet beállítás lépésről lépésre

### Fejlesztés (helyi)

```bash
# 1. .env fájl létrehozása a mintából
cp .env.example .env

# 2. GitHub OAuth App létrehozása (https://github.com/settings/developers)
#    - Homepage URL: http://localhost
#    - Callback URL: http://localhost/api/auth/callback
#    Másold be a Client ID-t és Client Secret-et a .env-be

# 3. Indítás
make up
```

### Éles (VPS)

```bash
# 1. .env fájl szerkesztése
nano .env

# 2. Kötelező módosítások:
SECRET_KEY=<openssl rand -hex 32 kimenet>
BASE_URL=https://school.example.com
ENVIRONMENT=production
ALLOWED_ORIGINS=https://school.example.com
GITHUB_CLIENT_ID=<OAuth App ID>
GITHUB_CLIENT_SECRET=<OAuth App Secret>
GITHUB_WEBHOOK_SECRET=<openssl rand -hex 20 kimenet>
DATABASE_URL=postgresql://openschool:<erős-jelszó>@db:5432/openschool
DB_PASSWORD=<erős-jelszó>
```

---

## 6. Változók validációja

A `backend/app/config.py` fájlban a `Settings` osztály Pydantic `model_validator`-t használ:

| Feltétel | Eredmény |
|----------|----------|
| `ENVIRONMENT=production` + `SECRET_KEY=change-me-in-production` | **ValueError** — a backend nem indul el |
| `ENVIRONMENT=production` + `GITHUB_CLIENT_SECRET` üres | **ValueError** — a backend nem indul el |
| `ENVIRONMENT=production` + `GITHUB_WEBHOOK_SECRET` üres | **Warning** — a backend elindul, de webhook aláírás nem ellenőrzött |
