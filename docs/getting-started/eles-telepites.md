# OpenSchool Platform — Éles telepítés (VPS)

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](architektura.md) · [Telepítés](telepitesi-utmutato.md) · **Éles telepítés** · [Staging](staging-telepites.md) · [Környezeti változók](kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md)

Ez a dokumentum az éles (production) környezet beüzemelését ismerteti VPS-en: szerver előkészítés, SSH biztonság, DNS, SSL, CI/CD pipeline és hibaelhárítás.

---

## Tartalomjegyzék

1. [Éles telepítés](#éles-telepítés)
2. [SSH biztonság](#ssh-biztonság)
3. [DNS és Cloudflare konfiguráció](#dns-és-cloudflare-konfiguráció)
4. [SSL/TLS Let's Encrypt-tel](#ssltls-lets-encrypttel)
5. [Deploy SSH kulcs CI/CD-hez](#deploy-ssh-kulcs-cicd-hez)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Hibaelhárítás](#hibaelhárítás)
8. [Biztonsági ellenőrzőlista](#biztonsági-ellenőrzőlista)

---

## Éles telepítés

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
ssh root@your-vps-ip

# Rendszerfrissítés és alap csomagok
apt-get update && apt-get install -y curl git ufw

# Docker telepítése (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh

# Docker Compose plugin telepítése (ha nincs benne)
apt-get install -y docker-compose-plugin
```

#### 1b. Tűzfal beállítása (UFW)

```bash
# Tűzfal engedélyezése — csak SSH, HTTP és HTTPS portok
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Ellenőrzés
ufw status
```

> A PostgreSQL port (5432) **nem** szabad kívülről elérhető legyen — a Docker-en belül érik el a szolgáltatások.

#### 1c. Deploy felhasználó létrehozása

Ne futtasd a szolgáltatásokat root-ként — hozz létre egy dedikált deploy felhasználót:

```bash
# Deploy felhasználó létrehozása
useradd -m -s /bin/bash openschool

# Docker csoport hozzáadása (konténerek kezeléshez)
usermod -aG docker openschool

# Projekt könyvtár létrehozása és birtokba adása
mkdir -p /opt/openschool
chown openschool:openschool /opt/openschool
```

A deploy felhasználónak **nem kell** sudo jogosultság. A Docker csoport tagság elég a konténerek kezeléséhez.

### 2. Klónozás és konfigurálás

```bash
# Váltás a deploy felhasználóra
su - openschool
cd /opt/openschool

git clone git@github.com:ghemrich/openschool-platform.git .
```

#### `.env.prod` fájl létrehozása

Az éles környezeti fájl neve `.env.prod` (nem `.env`), és szimlinkelve lesz:

```bash
# Erős jelszavak generálása
DB_PASS=$(openssl rand -base64 24)
SECRET=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 20)

# .env.prod fájl létrehozása
cat > .env.prod << EOF
DB_USER=openschool
DB_PASSWORD=$DB_PASS
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:${DB_PASS}@db:5432/openschool
SECRET_KEY=$SECRET
BASE_URL=https://yourdomain.com
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com
GITHUB_CLIENT_ID=production_client_id
GITHUB_CLIENT_SECRET=production_client_secret
GITHUB_WEBHOOK_SECRET=$WEBHOOK_SECRET
PROD_DOMAIN=yourdomain.com
STAGING_DOMAIN=staging.yourdomain.com
EOF

# Jogosultsagok (csak a tulajdonos olvashatja)
chmod 600 .env.prod

# Szimlink létrehozása a docker-compose kompatibilitáshoz
ln -sf .env.prod .env
```

> ⚠️ **Fontos:** A `.env.prod` fájl tartalmazza az összes titkos kulcsot. Soha ne commitold, és állítsd `chmod 600`-ra.

### 3. DNS konfiguráció

Irányítsd a domaint a VPS IP-címére:

| Típus | Név | Érték |
|-------|-----|-------|
| A | `yourdomain.com` | `VPS_IP_CÍM` |
| A | `www` | `VPS_IP_CÍM` |

Várd meg a DNS propagációt (akár 48 óra, általában percek).

### 4. Szolgáltatások indítása

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d

# Migrációk futtatása
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head

# Ellenőrzés
curl http://localhost/health
```

### 5. Kezdeti adatok betöltése (opcionális)

```bash
docker compose exec db psql -U openschool -d openschool <<'SQL'
INSERT INTO courses (name, description) VALUES
  ('Python Alapok', '13 hetes bevezető kurzus a Python programozásba.'),
  ('Backend FastAPI', '25 hetes backend fejlesztő kurzus FastAPI keretrendszerrel.'),
  ('Projekt Labor', 'Az OpenSchool platform felépítése az alapoktól az éles üzemig.');
SQL
```

### 6. Következő lépések

Az éles üzembe helyezés után:
- **SSH biztonság** — [lásd alább](#ssh-biztonság)
- **DNS és SSL** — [lásd alább](#dns-és-cloudflare-konfiguráció)
- **Karbantartás és backup** — lásd [Automatizálás](../operations/automatizalas-beallitas.md)
- **Staging környezet** — lásd [Staging telepítés](staging-telepites.md)

---

## SSH biztonság

Az éles szerveren az SSH jelszavas bejelentkezést **ki kell kapcsolni** — csak kulcs alapú hitelesítés engedélyezett. Ez megakadályozza a brute-force támadásokat.

### 1. SSH kulcs másolása a VPS-re

Ha még nincs SSH kulcsod, generálj egyet a helyi gépen:

```bash
# Kulcs generálása (ha még nincs)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Kulcs másolása a VPS-re (jelszóval kell bejelentkezni ehhez utoljára)
ssh-copy-id root@VPS_IP
```

### 2. Jelszavas bejelentkezés letiltása

Miután a kulcs alapú bejelentkezés működik, tiltsd le a jelszavas hozzáférést:

```bash
ssh root@VPS_IP

# sshd_config módosítása
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' /etc/ssh/sshd_config

# SSH szolgáltatás újraindítása
systemctl restart sshd
```

### 3. Ellenőrzés

```bash
# Egy másik terminálból próbálj meg jelszóval belépni — el kell utasítania
ssh -o PubkeyAuthentication=no root@VPS_IP
# → Permission denied (publickey).
```

> ⚠️ **Fontos:** Ne zárd be az aktuális SSH munkamenetet, amíg nem ellenőrizted, hogy a kulcs alapú bejelentkezés működik egy másik terminálból! Ha elrontod, kizárhatod magad a szerverről.

---

## DNS és Cloudflare konfiguráció

Ha Cloudflare-t használsz DNS szolgáltatóként és CDN/DDoS védelemként:

### 1. DNS rekord beállítása

Cloudflare Dashboard → DNS → Records:

| Típus | Név | Tartalom | Proxy |
|-------|-----|----------|-------|
| A | `@` (vagy `yourdomain.com`) | `VPS_IP_CÍM` | Proxied (narancssárga felhő) |

### 2. SSL/TLS mód

Cloudflare Dashboard → SSL/TLS → Overview:

- **Full (Strict)** — ez az ajánlott beállítás
- Ez megköveteli, hogy az origin szerveren (VPS) érvényes SSL tanúsítvány legyen (Let's Encrypt)
- Cloudflare HTTPS-sel csatlakozik a VPS-hez, a látogatók is HTTPS-t kapnak

> ⚠️ **Ne használj "Flexible" módot** éles környezetben! Flexible módban a Cloudflare és a VPS közötti forgalom titkosítatlan HTTP — ez biztonsági kockázat.

### 3. SSL/TLS módok összehasonlítása

| Mód | Cloudflare → Origin | Tanúsítvány kell? | Biztonság |
|-----|---------------------|-------------------|----------|
| Off | HTTP | Nem | ❌ Nincs titkosítás |
| Flexible | HTTP | Nem | ⚠️ Félig titkosított |
| Full | HTTPS | Bármilyen (self-signed is) | ✅ Titkosított |
| **Full (Strict)** | **HTTPS** | **Érvényes (Let's Encrypt)** | **✅✅ Ajánlott** |

### 4. SSL tanúsítvány igénylés Cloudflare mögül

A Let's Encrypt certbot standalone módja **nem működik** aktív Cloudflare proxyval, mert a Cloudflare elkapja a HTTP kéréseket. A megoldás:

1. **Ideiglenesen kapcsold ki** a Cloudflare proxyt (narancssárga felhő → szürke felhő / "DNS only")
2. Futtasd a certbot-ot (lásd [SSL/TLS Let's Encrypt-tel](#ssltls-lets-encrypttel))
3. **Kapcsold vissza** a Cloudflare proxyt (szürke → narancssárga felhő)
4. Állítsd az SSL módot **Full (Strict)**-re

> **Megjegyzés:** A tanúsítvány megújításkor is ideiglenesen ki kell kapcsolni a Cloudflare proxyt, vagy használj DNS-01 challenge-t (lásd alább az automatikus megújításnál).

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

Frissítsd az `nginx/nginx.conf.template` fájlt SSL-hez:

```nginx
# HTTP — /health átengedi (Docker healthcheck-hez), minden mást HTTPS-re irányít
server {
    listen 80;

    location /health {
        proxy_pass http://backend/health;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS — fő kiszolgáló
server {
    listen 443 ssl;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... meglévő location blokkok (api, health, verify, stb.) ...
}
```

> **Fontos:** A port 80-as szerver blokkban a `/health` endpoint továbbra is elérhető marad — ez szükséges a Docker healthcheck és a belső monitoring számára. Minden más kérést HTTPS-re irányít.

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

> **Cloudflare használata esetén:** A standalone megújításhoz az nginx-t le kell állítani és a Cloudflare proxyt ideiglenesen ki kell kapcsolni. Alternatívaként a `certbot` DNS-01 challenge pluginja (pl. `certbot-dns-cloudflare`) képes megújítani a tanúsítványt a Cloudflare proxy kikapcsolása nélkül:
>
> ```bash
> # Cloudflare DNS plugin telepítése
> apt-get install python3-certbot-dns-cloudflare
>
> # API token fájl létrehozása (Cloudflare Dashboard → API Tokens → Edit zone DNS)
> cat > /etc/letsencrypt/cloudflare.ini << EOF
> dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN
> EOF
> chmod 600 /etc/letsencrypt/cloudflare.ini
>
> # Tanúsítvány igénylése DNS-01 challenge-sel (proxy maradhat bekapcsolva)
> certbot certonly --dns-cloudflare \
>   --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
>   -d yourdomain.com
> ```

---

## Deploy SSH kulcs CI/CD-hez

A GitHub Actions CD pipeline SSH-val csatlakozik a VPS-hez. Ehhez egy dedikált SSH kulcspár kell a deploy felhasználóhoz.

### 1. SSH kulcspár generálása a VPS-en

```bash
# Deploy felhasználóként
su - openschool

# Ed25519 kulcspár generálása (jelszó nélkül a CI/CD automatizáláshoz)
ssh-keygen -t ed25519 -C "deploy@openschool" -f ~/.ssh/id_ed25519 -N ""

# Publikus kulcs hozzáadása az authorized_keys-hez
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Privát kulcs tartalmának kiíratása (ezt kell a GitHub Secrets-be másolni)
cat ~/.ssh/id_ed25519
```

### 2. GitHub Actions titkok beállítása

GitHub repó → Settings → Secrets and variables → Actions:

**Secrets** (Settings → Secrets → New repository secret):

| Név | Érték |
|-----|-------|
| `VPS_USER` | `openschool` |
| `VPS_SSH_KEY` | A privát kulcs teljes tartalma (`-----BEGIN OPENSSH PRIVATE KEY-----` ... `-----END OPENSSH PRIVATE KEY-----`) |

**Variables** (Settings → Variables → New repository variable):

| Név | Érték |
|-----|-------|
| `VPS_HOST` | A VPS IP-címe (pl. `194.99.21.209`) |

### 3. Tesztelés

Push-olj a `main` ágra, és ellenőrizd, hogy a CD pipeline sikeresen csatlakozik és deploy-ol:

```bash
git push origin main
# → GitHub Actions → CD workflow → ellenőrizd a deploy lépést
```

> **Megjegyzés:** A `VPS_HOST` változó (nem secret!) vezérli, hogy a CD pipeline egyáltalán lefut-e. Ha nincs beállítva, a deploy lépés kihagyásra kerül.

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

### VPS újratelepítés után SSH host key hiba

Ha a VPS-t újratelepítették, az SSH kliens régi host key-t fog találni, és megtagadja a kapcsolatot:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

Megoldás:

```bash
# Régi host key törlése a helyi gépről
ssh-keygen -R VPS_IP

# Újra csatlakozás (elfogadja az új host key-t)
ssh root@VPS_IP
```

### Alembic migráció hiba: tábla már létezik

Ha a SQLAlchemy modellek automatikusan létrehozták a táblákat az `alembic upgrade head` előtt:

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "users" already exists
```

Megoldás — jelöld meg az aktuális állapotot a legutolsó migrációval:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic stamp head
```

Ez nem futtat migrációkat, csak beállítja az Alembic verziót, hogy szinkronban legyen a tényleges adatbázis állapottal.

### Cloudflare 522 Connection Timed Out

Ha a domain Cloudflare mögül 522 hibát ad:

1. **Konténerek futnak?** — `docker compose -f docker-compose.prod.yml ps`
2. **Portok nyitva?** — `sudo ufw status` (80 és 443 kell)
3. **SSL mód helyes?** — Cloudflare SSL/TLS → Full (Strict) módban a VPS-en HTTPS (port 443) kell
4. **nginx elérhető?** — `curl -v http://localhost/health` a VPS-ről
5. **Cloudflare proxy aktív?** — DNS rekordnál narancssárga felhő (Proxied) kell

Gyakori ok: Cloudflare Full/Full (Strict) módban a 443-as porton próbál csatlakozni, de az nginx-ben nincs SSL konfigurálva vagy a 443-as port nincs nyitva a tűzfalon.

---

## Biztonsági ellenőrzőlista

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
| SSH | Jelszavas bejelentkezés letiltva, csak kulcs alapú hitelesítés |
| Cloudflare SSL | Full (Strict) mód beállítva (ha Cloudflare-t használsz) |
