# OpenSchool Platform — Staging telepítés

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](architektura.md) · [Telepítés](telepitesi-utmutato.md) · [Éles telepítés](eles-telepites.md) · **Staging** · [Környezeti változók](kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md)

A staging környezet az éles rendszer tükörképe, ahol a `develop` branch-et teszteljük deploy előtt. A staging és a production **teljesen elkülönített** — saját adatbázis, saját GitHub OAuth app, saját domain — de **ugyanazon a VPS-en** futnak.

> **Előfeltétel:** Az [éles telepítés](eles-telepites.md) (VPS, SSH, DNS, SSL) már kész kell legyen.

---

## Tartalomjegyzék

1. [Architektúra](#architektúra)
2. [GitHub OAuth app staging-hez](#1-github-oauth-app-staging-hez)
3. [Docker hálózat létrehozása](#2-docker-hálózat-létrehozása)
4. [Staging könyvtár és klónozás](#3-staging-könyvtár-és-klónozás)
5. [Környezeti változók](#4-környezeti-változók)
6. [Compose és nginx fájlok](#5-compose-és-nginx-fájlok)
7. [Production konfig frissítése](#6-production-konfig-frissítése)
8. [DNS konfiguráció](#7-dns-konfiguráció)
9. [SSL tanúsítvány bővítése](#8-ssl-tanúsítvány-bővítése)
10. [Staging indítása](#10-staging-indítása)
11. [Deploy folyamat](#11-deploy-folyamat)
12. [Staging vs Production összehasonlítás](#13-staging-vs-production-összehasonlítás)

---

## Architektúra

A staging a production mellett fut ugyanazon a VPS-en, megosztott Docker hálózaton keresztül:

```
Internet
  │
  ▼
Cloudflare (SSL termination + CDN)
  │
  ▼ HTTPS
Production nginx (docker-compose.prod.yml)
  ├── yourdomain.com → backend (prod)
  └── staging.yourdomain.com ──► openschool-net ──► Staging nginx (docker-compose.staging.yml)
                                                       └── backend (staging)
```

- A **production nginx** kezeli az SSL-t mindkét domainhez (domain nevek `envsubst` template-ből, SSL tanúsítványok domain-enként)
- A staging kéréseket az `openschool-net` Docker hálózaton keresztül proxy-zza a staging nginx konténerbe
- A **staging nginx** (`nginx-staging.conf`) csak HTTP-t szolgál ki — az SSL-t a production nginx terminálja
- Minden más (backend, DB, frontend) teljesen elkülönített

---

## 1. GitHub OAuth app staging-hez

A staging-nek **külön** GitHub OAuth alkalmazás kell (a callback URL eltér):

1. [GitHub Settings > Developer settings > OAuth Apps > New](https://github.com/settings/developers)
2. Beállítások:
   - **Application name:** `OpenSchool Staging`
   - **Homepage URL:** `https://staging.yourdomain.com`
   - **Authorization callback URL:** `https://staging.yourdomain.com/api/auth/callback`
3. Jegyezd fel a `Client ID` és `Client Secret` értékeket

---

## 2. Docker hálózat létrehozása

A production és staging nginx konténerek egy közös Docker hálózaton kommunikálnak:

```bash
docker network create openschool-net
```

> Ez a hálózat mindkét compose stack-ben `external: true`-ként van hivatkozva, tehát a compose nem hozza létre automatikusan — **előre létre kell hozni**.

---

## 3. Staging könyvtár és klónozás

```bash
# Staging könyvtár létrehozása (elkülönítve a /opt/openschool production-től)
sudo mkdir -p /opt/openschool-staging
sudo chown openschool:openschool /opt/openschool-staging

# Klónozás (develop branch)
su - openschool
cd /opt/openschool-staging
git clone -b develop git@github.com:ghemrich/openschool-platform.git .
```

---

## 4. Környezeti változók

Hozz létre `.env.staging` fájlt, majd szimlinkelj:

```bash
cd /opt/openschool-staging

# Erős jelszavak generálása
DB_PASS=$(openssl rand -base64 24)
SECRET=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 20)

cat > .env.staging << EOF
DB_USER=openschool_staging
DB_PASSWORD=$DB_PASS
DB_NAME=openschool_staging
DATABASE_URL=postgresql://openschool_staging:${DB_PASS}@db:5432/openschool_staging
SECRET_KEY=$SECRET
BASE_URL=https://staging.yourdomain.com
ENVIRONMENT=staging
ALLOWED_ORIGINS=https://staging.yourdomain.com
PROD_DOMAIN=yourdomain.com
STAGING_DOMAIN=staging.yourdomain.com
GITHUB_CLIENT_ID=staging_oauth_client_id
GITHUB_CLIENT_SECRET=staging_oauth_client_secret
GITHUB_WEBHOOK_SECRET=$WEBHOOK_SECRET
EOF

chmod 600 .env.staging
ln -sf .env.staging .env
```

> ⚠️ **Fontos:** A staging és production adatbázis **külön** kell legyen (`openschool_staging` vs `openschool`). Soha ne használj production adatokat staging-en.

---

## 5. Compose és nginx fájlok

A repóban két dedikált fájl biztosítja a staging működését:

- **`docker-compose.staging.yml`** — önálló compose fájl a staging stack-hez (saját projekt neve: `openschool-staging`, saját volume-ok, nincs publikált port — a staging nginx az `openschool-net` hálózaton érhető el a production nginx számára)
- **`nginx/nginx-staging.conf`** — HTTP-only nginx konfig (nincs SSL — a production nginx terminálja az SSL-t)

Ezek a fájlok már a repóban vannak, nem kell létrehozni.

---

## 6. Production konfig frissítése

A production stack-et is frissíteni kell, hogy a staging-et kiszolgálja:

### `docker-compose.prod.yml` — hálózat hozzáadása

Az nginx szolgáltatás csatlakozzon az `openschool-net` hálózathoz is:

```yaml
nginx:
  # ... meglévő konfig ...
  networks:
    - default
    - openschool-net

networks:
  openschool-net:
    external: true
```

### `nginx/nginx.conf.template` — staging proxy blokkok

Az nginx konfiguráció egy **template fájl** (`nginx/nginx.conf.template`), amely `envsubst`-tel kapja meg a domain neveket environment változókból. A staging server blokkok a template-ben már benne vannak — a `PROD_DOMAIN` és `STAGING_DOMAIN` változókat a `.env.prod` fájlban kell beállítani:

```ini
# .env.prod
PROD_DOMAIN=yourdomain.com
STAGING_DOMAIN=staging.yourdomain.com
```

A `docker-compose.prod.yml` az nginx konténerben az `envsubst` paranccsal rendereli a template-et:

```yaml
nginx:
  command: >
    sh -c "envsubst '$$PROD_DOMAIN $$STAGING_DOMAIN'
    < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
    && nginx -g 'daemon off;'"
```

A template-ben a domain nevek `${PROD_DOMAIN}` és `${STAGING_DOMAIN}` helyőrzőkkel szerepelnek. Az `envsubst` explicit változólistával fut, hogy az nginx saját változói (`$host`, `$request_uri` stb.) ne legyenek lecserélve.

> A `resolver 127.0.0.11` a Docker belső DNS-e. A `set $staging_backend` változóval oldja meg az nginx, hogy a staging konténer DNS neve runtime-ban legyen feloldva (nem induláskor).

---

## 7. DNS konfiguráció

Hozz létre egy `A` rekordot a staging subdomainhez:

```
staging.yourdomain.com  →  A  →  VPS_IP
```

Ha Cloudflare-t használsz: először állítsd **DNS only** módra (szürke felhő) az SSL tanúsítvány igényléshez, utána kapcsold **Proxied**-re.

---

## 8. SSL tanúsítvány a staging domainhez

A staging domain **külön** Let's Encrypt tanúsítványt kap (nem bővítjük a production certeket):

```bash
# Production nginx leállítása (80-as port felszabadítása)
cd /opt/openschool
docker compose -f docker-compose.prod.yml stop nginx

# Külön tanúsítvány a staging domainhez
sudo certbot certonly --standalone \
  -d staging.yourdomain.com

# Production nginx újraindítása
docker compose -f docker-compose.prod.yml start nginx
```

> A staging és production tanúsítványok függetlenek egymástól. Az `nginx.conf.template`-ben a staging blokk a `/etc/letsencrypt/live/${STAGING_DOMAIN}/` útvonalon keresi a certet.

---

## 9. Production újraindítása

A hálózati és nginx változtatások után újra kell indítani a production stack-et:

```bash
cd /opt/openschool
git pull origin main
docker compose -f docker-compose.prod.yml up --build -d
```

---

## 10. Staging indítása

```bash
cd /opt/openschool-staging

# Staging konténerek buildelése és indítása
docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d

# Migráció futtatása
docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head

# Ellenőrzés
curl -f https://staging.yourdomain.com/health
# → {"status": "ok"}
```

> Ha az Alembic `DuplicateTable` hibát ad (mert a SQLAlchemy modellek már létrehozták a táblákat), futtasd: `docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic stamp head`

---

## 11. Deploy folyamat

A staging deploy a `develop` branch-ről történik:

```bash
cd /opt/openschool-staging
git pull origin develop
docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head
curl -f https://staging.yourdomain.com/health
```

**CD pipeline staging deploy-jal (opcionális):**

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
          docker compose -f docker-compose.staging.yml --env-file .env.staging up --build -d
          docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend alembic upgrade head
          sleep 5
          docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T backend curl -f http://localhost:8000/health
          echo "Staging deploy successful!"
```

Ehhez a GitHub repo-ban be kell állítani:
- **Environment:** `staging` (Settings > Environments)
- **Variables:** `STAGING_HOST`
- **Secrets:** `STAGING_USER`, `STAGING_SSH_KEY`

---

## 12. Migráció tesztelés staging-en

A staging elsődleges célja az adatbázis migrációk tesztelése éles deploy előtt:

1. **Migráció generálása** a fejlesztői gépen (`alembic revision --autogenerate`)
2. **PR nyitása** `develop`-ra → CI futtatja a teszteket
3. **Merge `develop`-ba** → staging deploy (manuális vagy automatikus)
4. **Migráció futtatása staging-en** → ellenőrzés, hogy sikeres-e
5. **Funkcionális teszt** staging-en (manuális)
6. **Merge `main`-be** → production deploy

---

## 13. Staging vs Production összehasonlítás

| Szempont | Staging | Production |
|----------|---------|------------|
| Branch | `develop` | `main` |
| Domain | `staging.yourdomain.com` | `yourdomain.com` |
| Compose fájl | `docker-compose.staging.yml` | `docker-compose.prod.yml` |
| Nginx konfig | `nginx-staging.conf` (HTTP only) | `nginx.conf.template` (SSL + staging proxy, envsubst) |
| Adatbázis | `openschool_staging` | `openschool` |
| GitHub OAuth | Külön app | Külön app |
| `ENVIRONMENT` | `staging` | `production` |
| Swagger UI | Elérhető (`/docs`) | Letiltva |
| SSL | Production nginx terminálja | Közvetlen Let's Encrypt |
| Hálózat | `openschool-net` (prod nginx-hez) | `openschool-net` + default |
| Deploy | Manuális / develop push | Automatikus main push |
| Cél | Tesztelés, review | Felhasználói forgalom |
