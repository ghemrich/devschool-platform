# OpenSchool Platform — Telepítési útmutató

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](architektura.md) · **Telepítés** · [Környezeti változók](kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a helyi fejlesztést, a staging és az éles (production) üzembe helyezést ismerteti.

---

## Tartalomjegyzék

1. [Előfeltételek](#előfeltételek)
2. [Helyi fejlesztés (Docker)](#helyi-fejlesztés-docker)
3. [Helyi fejlesztés (Docker nélkül)](#helyi-fejlesztés-docker-nélkül)
4. [Környezeti változók](#környezeti-változók)
5. [Adatbázis és migrációk](#adatbázis-és-migrációk)
6. [GitHub OAuth beállítás](#github-oauth-beállítás)
7. [Tesztek futtatása](#tesztek-futtatása)
8. [Staging telepítés](#staging-telepítés)
9. [Éles telepítés (VPS)](#éles-telepítés-vps)
10. [SSL/TLS Let's Encrypt-tel](#ssltls-lets-encrypttel)
11. [Biztonsági mentés](#biztonsági-mentés)
12. [CI/CD Pipeline](#cicd-pipeline)
13. [Hibaelhárítás](#hibaelhárítás)

---

## Előfeltételek

- **Docker** 24+ és **Docker Compose** v2
- **Python** 3.12+ (helyi fejlesztéshez Docker nélkül)
- **Node.js** 20+ (frontend fejlesztéshez)
- **Git**
- **GitHub fiók** (OAuth alkalmazás létrehozásához)

---

## Helyi fejlesztés (Docker)

A leggyorsabb módja a teljes rendszer elindításának:

```bash
# Repó klónozása
git clone git@github.com:ghemrich/openschool-platform.git
cd openschool-platform

# Környezeti fájl létrehozása
cp .env.example .env
# Szerkeszd a .env fájlt a GitHub OAuth adataiddal (lásd "GitHub OAuth beállítás")

# Összes szolgáltatás indítása (backend, db, nginx, frontend)
docker compose up --build -d

# Ellenőrzés
curl http://localhost/health
# → {"status": "ok"}

# Logok megtekintése
docker compose logs -f backend
```

**Futó szolgáltatások:**

| Szolgáltatás | Port | Leírás                      |
|-------------|------|-----------------------------|
| nginx       | 80   | Reverse proxy (belépési pont)|
| backend     | 8000 | FastAPI API (belső)          |
| db          | 5432 | PostgreSQL 16                |
| frontend    | —    | Astro build (statikus fájlok)|

**Hasznos parancsok:**

```bash
make up        # docker compose up --build -d
make down      # docker compose down
make test      # pytest futtatás
make migrate   # alembic migrációk futtatása
make lint      # ruff ellenőrzés + formázás
```

---

## Helyi fejlesztés (Docker nélkül)

Backend fejlesztéshez:

```bash
cd backend

# Virtuális környezet létrehozása
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Függőségek telepítése (produkció)
pip install -r requirements.txt
# Vagy fejlesztéshez (teszt, lint eszközökkel):
# pip install -r requirements-dev.txt

# Környezeti változók beállítása (vagy .env fájl a backend/ könyvtárban)
export DATABASE_URL="postgresql://openschool:openschool@localhost:5432/openschool"
export SECRET_KEY="change-me-in-production"
export BASE_URL="http://localhost"

# Migrációk futtatása
alembic upgrade head

# Szerver indítása
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend fejlesztéshez:

```bash
cd frontend
npm install
npm run dev    # Astro dev szerver: http://localhost:4321
npm run build  # Statikus fájlok buildelése
```

---

## Környezeti változók

Hozz létre egy `.env` fájlt a projekt gyökérkönyvtárában (soha ne commitold):

```bash
# Adatbázis
DB_USER=openschool
DB_PASSWORD=openschool
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:openschool@db:5432/openschool

# Biztonság
SECRET_KEY=change-me-in-production    # JWT aláíró kulcs — élesben random 64 karakteres stringet használj

# Platform
BASE_URL=http://localhost              # Tanúsítványok és QR kódok URL-jéhez
                                       # Élesben: https://yourdomain.com
ENVIRONMENT=development                # development vagy production
ALLOWED_ORIGINS=http://localhost,http://localhost:4321  # CORS engedélyezett eredetek

# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

| Változó | Kötelező | Leírás |
|---------|----------|--------|
| `DATABASE_URL` | Igen | PostgreSQL kapcsolati string |
| `SECRET_KEY` | Igen | JWT aláíró kulcs — élesben **egyedi és véletlenszerű** legyen |
| `BASE_URL` | Igen | A platform publikus URL-je (tanúsítványokhoz, QR kódokhoz) |
| `GITHUB_CLIENT_ID` | Igen | GitHub OAuth App kliens azonosító |
| `GITHUB_CLIENT_SECRET` | Igen | GitHub OAuth App kliens titkos kulcs |
| `GITHUB_ORG` | Nem | GitHub szervezet neve (Classroom integrációhoz) |
| `GITHUB_WEBHOOK_SECRET` | Nem | GitHub webhook titkos kulcs (Classroom webhookhoz) |
| `DB_USER` | Igen | PostgreSQL felhasználónév (docker-compose használja) |
| `DB_PASSWORD` | Igen | PostgreSQL jelszó (docker-compose használja) |
| `DB_NAME` | Igen | PostgreSQL adatbázisnév (docker-compose használja) |
| `ENVIRONMENT` | Nem | `development` vagy `production` — élesben kikapcsolja a Swagger UI-t |
| `ALLOWED_ORIGINS` | Nem | CORS engedélyezett eredetek, vesszővel elválasztva (pl. `https://yourdomain.com`) |

---

## Adatbázis és migrációk

A projekt **Alembic**-et használ az adatbázis migrációkhoz.

```bash
# Összes függőben lévő migráció futtatása
cd backend
alembic upgrade head

# Új migráció létrehozása modell módosítás után
alembic revision --autogenerate -m "leírás a változásról"

# Aktuális migrációs állapot ellenőrzése
alembic current

# Egy lépés visszavonása
alembic downgrade -1
```

Docker-en keresztül:

```bash
docker compose exec backend alembic upgrade head
```

---

## GitHub OAuth beállítás

1. Nyisd meg a [GitHub Developer Settings](https://github.com/settings/developers) oldalt
2. Kattints a **New OAuth App** gombra
3. Töltsd ki:
   - **Application name:** `OpenSchool` (vagy bármilyen név)
   - **Homepage URL:** `http://localhost` (vagy az éles domain)
   - **Authorization callback URL:** `http://localhost/api/auth/callback`
4. Kattints a **Register application** gombra
5. Másold ki a **Client ID**-t és generálj **Client Secret**-et
6. Add hozzá a `.env` fájlhoz:
   ```
   GITHUB_CLIENT_ID=Ov23li...
   GITHUB_CLIENT_SECRET=25a23e268e...
   ```

> **Fontos:** Éles környezethez hozz létre külön OAuth App-ot az éles domain-nel mint callback URL: `https://yourdomain.com/api/auth/callback`

---

## Tesztek futtatása

```bash
cd backend

# Összes teszt futtatása
pytest -v

# Adott tesztfájl futtatása
pytest tests/test_auth.py -v

# Lefedettségi riporttal
pytest --cov=app --cov-report=term-missing
```

A CI pipeline minden push és PR esetén automatikusan futtatja a teszteket.

---

## Staging telepítés

A staging környezet az éles rendszer tükörképe, ahol a `develop` branch-et teszteljük deploy előtt. A staging és a production környezet **teljesen elkülönített** — saját adatbázis, saját GitHub OAuth app, saját domain.

### 1. GitHub OAuth app staging-hez

A staging-nek **külön** GitHub OAuth alkalmazás kell (a callback URL eltér):

1. [GitHub Settings > Developer settings > OAuth Apps > New](https://github.com/settings/developers)
2. Beállítások:
   - **Application name:** `OpenSchool Staging`
   - **Homepage URL:** `https://staging.yourdomain.com`
   - **Authorization callback URL:** `https://staging.yourdomain.com/api/auth/callback`
3. Jegyezd fel a `Client ID` és `Client Secret` értékeket

### 2. Szerver előkészítése

Staging futhat ugyanazon a VPS-en (eltérő portokon) vagy külön szerveren:

```bash
# Projekt könyvtár (elkülönítve a production-től)
sudo mkdir -p /opt/openschool-staging
sudo chown $USER:$USER /opt/openschool-staging
cd /opt/openschool-staging

# Klónozás (develop branch)
git clone -b develop git@github.com:ghemrich/openschool-platform.git .
```

### 3. Környezeti változók

Hozz létre `.env.staging` fájlt a szerveren:

```bash
DATABASE_URL=postgresql://openschool_staging:STAGING_JELSZO@db:5432/openschool_staging
SECRET_KEY=$(openssl rand -hex 32)
BASE_URL=https://staging.yourdomain.com
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
GITHUB_CLIENT_ID=staging_oauth_client_id
GITHUB_CLIENT_SECRET=staging_oauth_client_secret
GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 20)
DB_USER=openschool_staging
DB_PASSWORD=STAGING_JELSZO
DB_NAME=openschool_staging
```

> ⚠️ **Fontos:** A staging és production adatbázis **külön** kell legyen. Soha ne használj production adatokat staging-en felhasználói adatvédelmi okokból.

### 4. DNS konfiguráció

Hozz létre egy `A` rekordot a DNS szolgáltatónál:

```
staging.yourdomain.com  →  A  →  VPS_IP
```

Ha ugyanazon a VPS-en fut mint a production, az nginx reverse proxy megoldja a routolást a domain alapján.

### 5. Indítás

```bash
cd /opt/openschool-staging

# Telepítés a production compose fájllal, staging env-vel
docker compose -f docker-compose.prod.yml --env-file .env.staging up --build -d

# Migráció futtatása
docker compose -f docker-compose.prod.yml --env-file .env.staging exec -T backend alembic upgrade head

# Ellenőrzés
docker compose -f docker-compose.prod.yml --env-file .env.staging ps
curl -f http://localhost:8000/health
```

> **Megjegyzés:** Ha a production és staging ugyanazon a gépen fut, a staging-nek eltérő portokat kell használnia. Ezt a `docker-compose.prod.yml` felülírásával oldhatod meg:
> ```bash
> # docker-compose.staging.yml (override)
> services:
>   nginx:
>     ports:
>       - "8080:80"
>   backend:
>     ports:
>       - "8001:8000"
> ```
> Indítás: `docker compose -f docker-compose.prod.yml -f docker-compose.staging.yml --env-file .env.staging up --build -d`

### 6. Deploy folyamat

A staging deploy a `develop` branch-ről történik:

```bash
cd /opt/openschool-staging
git pull origin develop
docker compose -f docker-compose.prod.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.prod.yml --env-file .env.staging exec -T backend alembic upgrade head
curl -f http://localhost:8000/health
```

**Automatizálás (opcionális):** A CD pipeline kibővíthető staging deploy-jal a `develop` branch-re:

```yaml
# .github/workflows/cd.yml — staging job hozzáadása
staging-deploy:
  runs-on: ubuntu-latest
  needs: test
  if: github.ref == 'refs/heads/develop' && vars.STAGING_HOST != ''
  environment: staging
  steps:
    - name: Deploy to staging
      uses: appleboy/ssh-action@v1
      with:
        host: ${{ vars.STAGING_HOST }}
        username: ${{ secrets.STAGING_USER }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          set -e
          cd /opt/openschool-staging
          git pull origin develop
          docker compose -f docker-compose.prod.yml --env-file .env.staging up --build -d
          docker compose -f docker-compose.prod.yml --env-file .env.staging exec -T backend alembic upgrade head
          sleep 5
          curl -f http://localhost:8000/health
          echo "Staging deploy successful!"
```

Ehhez a GitHub repo-ban be kell állítani:
- **Environment:** `staging` (Settings > Environments)
- **Variables:** `STAGING_HOST`
- **Secrets:** `STAGING_USER`, `STAGING_SSH_KEY`

### 7. Migráció tesztelés staging-en

A staging elsődleges célja az adatbázis migrációk tesztelése éles deploy előtt:

1. **Migráció generálása** a fejlesztői gépen (`alembic revision --autogenerate`)
2. **PR nyitása** `develop`-ra → CI futtatja a teszteket
3. **Merge `develop`-ba** → staging deploy (manuális vagy automatikus)
4. **Migráció futtatása staging-en** → ellenőrzés, hogy sikeres-e
5. **Funkcionális teszt** staging-en (manuális)
6. **Merge `main`-be** → production deploy

### 8. Staging vs Production összehasonlítás

| Szempont | Staging | Production |
|----------|---------|------------|
| Branch | `develop` | `main` |
| Domain | `staging.yourdomain.com` | `yourdomain.com` |
| Adatbázis | `openschool_staging` | `openschool` |
| GitHub OAuth | Külön app | Külön app |
| `ENVIRONMENT` | `staging` | `production` |
| Swagger UI | Elérhető (`/docs`) | Letiltva |
| Deploy | Manuális / develop push | Automatikus main push |
| Cél | Tesztelés, review | Felhasználói forgalom |

---

## Éles telepítés (VPS)

### Automatizált telepítés (ajánlott)

A teljes VPS beállítás automatizálható egyetlen szkripttel:

```bash
# SSH belépés a VPS-re
ssh root@your-vps-ip

# Automatizált bootstrap futtatása — végigvezet minden lépésen:
# Docker, tűzfal, repo klónozás, .env.prod generálás, SSL, seed data, cron
curl -fsSL https://raw.githubusercontent.com/ghemrich/openschool-platform/main/scripts/bootstrap-vps.sh -o bootstrap-vps.sh
bash bootstrap-vps.sh
```

A szkript interaktívan kérdezi a domain-t, GitHub OAuth adatokat, és automatikusan:
- Telepíti a Dockert + tűzfalat (UFW: 22, 80, 443 nyitva)
- Létrehozza a deploy usert és a projekt könyvtárat
- Klónozza a repót és erős jelszavakkal generálja a `.env.prod`-ot
- Elindítja a szolgáltatásokat és futtatja a migrációkat
- Beállítja a Let's Encrypt SSL-t
- Telepíti a karbantartási cron job-okat (`provision.sh`)

A bootstrap után futtasd a biztonsági ellenőrzést:

```bash
./scripts/security-check.sh
```

> A telepítés részleteit lásd alább, ha manuálisan szeretnéd elvégezni.

### Manuális telepítés

#### 1. Szerver előkészítése

```bash
# SSH belépés a VPS-re
ssh user@your-vps-ip

# Docker telepítése (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Jelentkezz ki és be, hogy a csoport érvényre jusson

# Docker Compose plugin telepítése
sudo apt-get install docker-compose-plugin

# Projekt könyvtár létrehozása
sudo mkdir -p /opt/openschool
sudo chown $USER:$USER /opt/openschool
cd /opt/openschool
```

### 2. Klónozás és konfigurálás

```bash
git clone git@github.com:ghemrich/openschool-platform.git .

# Éles környezeti fájl létrehozása
cp .env.example .env
nano .env
```

Éles értékek beállítása:

```bash
DATABASE_URL=postgresql://openschool:NAGYON_EROS_JELSZO@db:5432/openschool
SECRET_KEY=$(openssl rand -hex 32)
BASE_URL=https://yourdomain.com
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
GITHUB_CLIENT_ID=production_client_id
GITHUB_CLIENT_SECRET=production_client_secret
GITHUB_WEBHOOK_SECRET=$(openssl rand -hex 20)
DB_USER=openschool
DB_PASSWORD=NAGYON_EROS_JELSZO
DB_NAME=openschool
```

### 3. DNS konfiguráció

Irányítsd a domaint a VPS IP-címére:

| Típus | Név | Érték |
|-------|-----|-------|
| A | `yourdomain.com` | `VPS_IP_CÍM` |
| A | `www` | `VPS_IP_CÍM` |

Várd meg a DNS propagációt (akár 48 óra, általában percek).

### 4. Szolgáltatások indítása

```bash
docker compose -f docker-compose.prod.yml up --build -d

# Migrációk futtatása
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Ellenőrzés
curl http://localhost/health
```

### 5. Kezdeti adatok betöltése (opcionális)

```bash
docker compose exec db psql -U openschool -d openschool <<'SQL'
INSERT INTO courses (name, description) VALUES
  ('Python Alapok', '13 hetes bevezető kurzus a Python programozásba.'),
  ('Backend FastAPI', '25 hetes backend fejlesztő kurzus FastAPI keretrendszerrel.'),
  ('Projekt Labor', 'A OpenSchool platform felépítése az alapoktól az éles üzemig.');
SQL
```

---

## SSL/TLS Let's Encrypt-tel

### A) Certbot standalone (legegyszerűbb)

```bash
# Certbot telepítése
sudo apt-get install certbot

# nginx ideiglenes leállítása
docker compose -f docker-compose.prod.yml stop nginx

# Tanúsítvány igénylése
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# A tanúsítvány fájlok itt lesznek:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Frissítsd az `nginx/nginx.conf` fájlt SSL-hez:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # ... meglévő location blokkok ...
}
```

Csatold a tanúsítványokat a `docker-compose.prod.yml`-ben:

```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

### B) Reverse proxy Caddy-vel vagy Traefik-kel

Ha automatikus SSL-t szeretnél, fontold meg az nginx cseréjét [Caddy](https://caddyserver.com/)-re, amely automatikusan kezeli a Let's Encrypt-et.

### Automatikus megújítás

```bash
# Megújítás tesztelése
sudo certbot renew --dry-run

# Cron job hozzáadása az automatikus megújításhoz
echo "0 3 * * * certbot renew --quiet && docker compose -f /opt/openschool/docker-compose.prod.yml restart nginx" | sudo tee /etc/cron.d/certbot-renew
```

---

## Biztonsági mentés

A `scripts/backup.sh` szkript biztonsági mentést készít:

```bash
# Kézi futtatás
./scripts/backup.sh

# Napi cron job beállítása (hajnali 3-kor fut)
echo "0 3 * * * /opt/openschool/scripts/backup.sh" | crontab -
```

A szkript:
- `pg_dump`-pal menti a PostgreSQL adatbázist
- `.sql.gz` formátumra tömöríti
- `/opt/openschool/backups/` mappába menti
- 30 napnál régebbi mentéseket törli

### Kézi mentés

```bash
docker compose exec db pg_dump -U openschool openschool | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Visszaállítás mentésből

```bash
gunzip < backup_20260310.sql.gz | docker compose exec -T db psql -U openschool openschool
```

---

## CI/CD Pipeline

### CI (Folyamatos integráció)

Minden push (`main`, `develop`) és PR esetén fut:

1. **Lint lépés** — `ruff check` és `ruff format --check` ellenőrzés
2. **Teszt lépés** — `pytest -v --tb=short` (csak ha a lint sikeres)

A tesztek SQLite-ot használnak, nem igényelnek PostgreSQL-t.

### CD (Folyamatos telepítés)

Push esetén a `main` ágra — **csak ha a tesztek sikeresek és a `VPS_HOST` be van állítva**:

1. Tesztek futtatása (gate)
2. SSH kapcsolat a VPS-hez
3. `git pull origin main`
4. Docker konténerek újraépítése
5. Alembic migrációk futtatása
6. Health check (`curl -f http://localhost:8000/health`)

Szükséges GitHub beállítások:

| Típus | Név | Leírás |
|-------|--------|--------|
| Variable | `VPS_HOST` | VPS IP-cím vagy hosztnév (Settings → Variables) |
| Secret | `VPS_USER` | SSH felhasználónév a VPS-en |
| Secret | `VPS_SSH_KEY` | Privát SSH kulcs a VPS eléréséhez |

Beállítás:
1. GitHub repó → Settings → Environments → `production` létrehozása
2. Settings → Secrets and variables → Actions → Secrets-be: `VPS_USER`, `VPS_SSH_KEY`
3. Settings → Secrets and variables → Actions → Variables-be: `VPS_HOST`
4. A következő push a `main`-re automatikusan telepít

---

## Hibaelhárítás

### Docker jogosultsági hiba

```bash
sudo usermod -aG docker $USER
# Jelentkezz ki és be (vagy indítsd újra a terminált)
```

### A 80-as port foglalt

```bash
# Keresd meg, mi használja a 80-as portot
sudo lsof -i :80
# Állítsd le, vagy módosítsd az nginx portot a docker-compose.yml-ben
```

### Adatbázis kapcsolódási hiba

```bash
# Ellenőrizd, hogy a db konténer fut-e
docker compose ps db
# Nézd meg a db logokat
docker compose logs db
```

### Frontend változások nem látszanak

```bash
# Frontend újraépítése
docker compose up --build frontend
# nginx újraindítása az új statikus fájlok betöltéséhez
docker compose restart nginx
```

### OAuth callback hiba

- Ellenőrizd a `GITHUB_CLIENT_ID` és `GITHUB_CLIENT_SECRET` értékeket a `.env`-ben
- Győződj meg róla, hogy az OAuth callback URL egyezik: `http://localhost/api/auth/callback` (fejlesztés) vagy `https://yourdomain.com/api/auth/callback` (éles)
- Nézd meg a backend logokat: `docker compose logs backend`

### Tanúsítvány PDF nem generálódik

- Ellenőrizd, hogy a `backend/data/` könyvtár létezik és írható
- Nézd meg a backend logokat a PDF generálási hibákért

---

## Éles rendszer biztonsági ellenőrzőlista

A biztonsági ellenőrzőlista futtatható automatikusan is:

```bash
./scripts/security-check.sh
```

Ez ellenőrzi a SECRET_KEY erősségét, ENVIRONMENT beállítást, CORS konfigurációt, DB jelszót, .env.prod jogosultságokat, HTTPS-t, tűzfalat, konténer állapotot, Swagger UI elérhetőségét, mentések frissességét és cron job-okat.

Manuális ellenőrzőlista:

| Elem | Ellenőrzés |
|------|------------|
| `SECRET_KEY` | Egyedi, véletlenszerű, legalább 32 karakter (`openssl rand -hex 32`) |
| `ENVIRONMENT` | `production` értékre állítva (kikapcsolja a Swagger UI-t) |
| `ALLOWED_ORIGINS` | Csak az éles domain(ek) vannak felsorolva |
| `GITHUB_WEBHOOK_SECRET` | Be van állítva, megegyezik a GitHub webhook konfigurációval |
| `DB_PASSWORD` | Erős, egyedi jelszó (nem az alapértelmezett) |
| HTTPS | Let's Encrypt tanúsítvány bekonfigurálva, HTTP→HTTPS átirányítás |
| OAuth callback | Az éles domain-re mutat (`https://yourdomain.com/api/auth/callback`) |
| Backup | Napi `pg_dump` cron job beállítva |
| Tűzfal | Csak 80/443 port nyitva kívülről, PostgreSQL (5432) nem elérhető |
| DNS | A domain A rekord a VPS IP-re mutat |
