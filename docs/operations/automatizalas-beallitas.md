# Automatizálás és karbantartás beállítása

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](karbantartas-utmutato.md) · **Automatizálás** · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató az OpenSchool Platform automatizált karbantartásának beállítását írja le éles VPS-en. Tartalmazza a cron job-ok, monitoring, mentések, biztonsági auditok, Discord értesítések és titkos kulcsok (secrets) kezelését.

---

## Áttekintés

A karbantartási útmutató ([karbantartas-utmutato.md](karbantartas-utmutato.md)) számos ismétlődő feladatot ír le. A projekt tartalmaz egy egységes karbantartó szkriptet, ami mindet automatizálja:

| Ütemezés | Feladatok | Parancs |
|----------|-----------|---------|
| **Naponta** 02:00 | DB mentés, health check, log hibakeresés | `maintenance.sh full-daily` |
| **Hetente** V 03:00 | + lemezhasználat, Docker cleanup, DB statisztikák | `maintenance.sh full-weekly` |
| **Havonta** 1-jén 04:00 | + SSL ellenőrzés, pip-audit | `maintenance.sh full-monthly` |
| **Folyamatos** | Konténer health check-ek | Docker beépített (docker-compose.prod.yml) |
| **Folyamatos** | Függőség frissítések | GitHub Dependabot |
| **Push/PR-kor** | Lint + tesztek | GitHub Actions CI |
| **Main merge-kor** | Deploy | GitHub Actions CD |

### Ami már automatizált (nincs teendő)

- **CI/CD** — GitHub Actions kezeli a lintelést, tesztelést és deploy-t (`.github/workflows/ci.yml`, `cd.yml`)
- **Dependabot** — Heti pip frissítések, havi GitHub Actions frissítések (`.github/dependabot.yml`)
- **Konténer health check-ek** — Docker automatikusan újraindítja az egészségtelen konténereket (`docker-compose.prod.yml`)
- **Log rotáció** — Docker JSON log driver konténerenként 10MB × 3 fájlra korlátoz

### Ami szerver oldali beállítást igényel

- Cron job-ok mentésekhez, monitoringhoz és takarításhoz
- Log rotáció a karbantartási naplóhoz
- Discord webhook értesítések (opcionális)
- Titkos kulcsok (secrets) kezelése

---

## Előfeltételek

Az éles VPS-en ellenőrizd:

```bash
# Kötelező
docker --version          # Docker 24+
docker compose version    # Docker Compose v2+
curl --version            # Health check-ekhez

# Opcionális (email értesítésekhez)
apt install -y mailutils  # vagy az adott disztribúció megfelelője

# Opcionális (SSL ellenőrzéshez)
openssl version           # Általában előre telepítve
```

---

## 1. lépés — Karbantartási környezet konfigurálása

Hozz létre egy konfigurációs fájlt a VPS-en:

```bash
sudo nano /etc/openschool-maintenance.conf
```

Írd be a releváns beállításokat:

```bash
# /etc/openschool-maintenance.conf

# A projekt elérési útja (alapértelmezett: scripts/ szülőmappája)
# PROJECT_DIR=/opt/openschool

# Használandó compose fájl
# COMPOSE_FILE=/opt/openschool/docker-compose.prod.yml

# Mentés beállítások
BACKUP_DIR=/opt/openschool/backups
BACKUP_RETENTION_DAYS=30

# SSL monitoring (a saját domain-edre állítsd)
SSL_DOMAIN=yourdomain.com
SSL_WARNING_DAYS=30

# Discord webhook értesítések (lásd 5. lépés)
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Email értesítések (opcionális — mailutils szükséges)
# NOTIFY_EMAIL=admin@yourdomain.com

# Karbantartási napló helye
LOG_FILE=/var/log/openschool-maintenance.log

# Adatbázis hozzáférés (.env.prod-ból automatikusan betöltődik,
# de itt felülírható)
# DB_USER=openschool
# DB_NAME=openschool
```

> **Megjegyzés:** A szkript automatikusan betölti a `.env.prod` (vagy `.env`) fájlt a projekt könyvtárból az adatbázis hozzáférési adatokhoz. `DB_USER`/`DB_NAME` csak akkor kell ide, ha eltérnek.

---

## 2. lépés — Cron job-ok telepítése

### Automatikus telepítés (ajánlott)

A cron job-ok **automatikusan telepítésre/frissítésre kerülnek** minden deploy alkalmával. A CD pipeline (`cd.yml`) a deploy végén futtatja a `setup-cron.sh` szkriptet, tehát:

- **Első deploy:** a cron job-ok létrejönnek a szerveren
- **Minden további deploy:** a cron job-ok frissülnek, ha bármi változott a szkriptekben

Ehhez nincs teendőd — a `git push origin main` automatikusan kezeli.

### Egyszeri szerver provisionálás

Friss VPS-en (első alkalommal) futtasd a provisioning szkriptet, ami mindent beállít egyszerre:

```bash
# A szerveren (SSH-val belépve)
cd /opt/openschool
sudo ./scripts/provision.sh
```

Vagy távolról, SSH-n keresztül:

```bash
ssh root@your-vps 'cd /opt/openschool && ./scripts/provision.sh'
```

A `provision.sh` a következőket csinálja:
1. Létrehozza a mentési könyvtárat (`/opt/openschool/backups`)
2. Telepíti a cron job-okat + log rotációt
3. Létrehozza a konfigurációs fájlt (`/etc/openschool-maintenance.conf`)
4. Beállítja a jogosultságokat
5. Ellenőrzi a telepítést

A provisionálás után csak a konfig fájlt kell szerkeszteni:

```bash
sudo nano /etc/openschool-maintenance.conf
# → Állítsd be: DISCORD_WEBHOOK_URL, SSL_DOMAIN, stb.
```

### Manuális telepítés (alternatíva)

Ha inkább kézzel szeretnéd:

```bash
cd /opt/openschool
sudo ./scripts/setup-cron.sh
```

Ez létrehozza:
- `/etc/cron.d/openschool-maintenance` — Minden ütemezett feladat
- `/etc/logrotate.d/openschool-maintenance` — Log rotáció (hetente, 12 hétig megőrizve)

### Telepítés ellenőrzése

```bash
# Telepített cron job-ok megtekintése
cat /etc/cron.d/openschool-maintenance

# Cron futásának ellenőrzése
systemctl status cron

# Szkript manuális tesztelése
./scripts/maintenance.sh health
./scripts/maintenance.sh backup
```

### Cron job-ok eltávolítása

```bash
sudo ./scripts/setup-cron.sh --remove
```

---

## 3. lépés — Mentési könyvtár beállítása

```bash
# Mentési könyvtár létrehozása
sudo mkdir -p /opt/openschool/backups

# Tulajdonos beállítása a Docker-t futtató felhasználóra
sudo chown $(whoami):$(whoami) /opt/openschool/backups

# Teszt mentés
./scripts/maintenance.sh backup
ls -la /opt/openschool/backups/
```

### Távoli mentés (ajánlott)

A cron lokálisan ment, de érdemes máshova is másolni. Add hozzá a crontab-hoz:

```bash
# A opció: rsync másik szerverre (naponta 05:00-kor)
# Add hozzá a /etc/cron.d/openschool-maintenance fájlhoz:
0 5 * * * youruser rsync -az /opt/openschool/backups/ backup-server:/backups/openschool/

# B opció: S3-kompatibilis tárolóra feltöltés
# Telepítés: pip install awscli
# Konfiguráció: aws configure
0 5 * * * youruser aws s3 sync /opt/openschool/backups/ s3://your-bucket/openschool-backups/ --delete
```

### Mentés visszaállítás tesztelése

Futtasd rendszeresen (a karbantartási útmutató legalább félévente ajánlja):

```bash
# Elérhető mentések listázása
ls -lt /opt/openschool/backups/

# Visszaállítás teszt adatbázisba (NEM a produkciósba!)
gunzip -c /opt/openschool/backups/db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U openschool -d openschool_test
```

---

## 4. lépés — Parancsok referencia

Bármely karbantartási feladat futtatható manuálisan:

```bash
cd /opt/openschool

# Health check — konténer állapot, /health endpoint, DB elérhetőség
./scripts/maintenance.sh health

# Adatbázis mentés — gzip-elt dump, régi mentések törlése
./scripts/maintenance.sh backup

# Lemezhasználat — fájlrendszer + Docker használat + mentések mérete
./scripts/maintenance.sh disk

# Docker takarítás — régi image-ek, build cache törlése (>30 nap)
./scripts/maintenance.sh docker-cleanup

# SSL ellenőrzés — hány nap van a tanúsítvány lejáratáig (SSL_DOMAIN szükséges)
./scripts/maintenance.sh ssl-check

# Biztonsági audit — pip-audit futtatása a backend konténerben
./scripts/maintenance.sh security-audit

# Log hibák — utolsó 500 sor átvizsgálása hibák/kivételek után
./scripts/maintenance.sh log-errors

# DB státusz — aktív kapcsolatok, tábla méretek, migráció verzió
./scripts/maintenance.sh db-status

# Összetett parancsok
./scripts/maintenance.sh full-daily    # health + backup + log-errors
./scripts/maintenance.sh full-weekly   # daily + disk + cleanup + db-status
./scripts/maintenance.sh full-monthly  # weekly + ssl + security-audit
```

---

## 5. lépés — Discord értesítések beállítása

A karbantartó szkript Discord webhook-on keresztül értesít, ha valami elromlik (mentés hiba, kritikus lemezhasználat, SSL lejárat, health check hiba).

### Discord webhook létrehozása

1. Nyisd meg a Discord szervert, ahol az értesítéseket szeretnéd kapni
2. Menj a kívánt csatorna beállításaiba: **Csatorna szerkesztése → Integrációk → Webhookok**
3. Kattints a **Új webhook** gombra
4. Adj nevet (pl. `OpenSchool Monitoring`)
5. Opcionálisan állíts be profilképet
6. Kattints a **Webhook URL másolása** gombra
7. Mentsd el a beállításokat

### Webhook konfigurálása a szerveren

Írd be a webhook URL-t a konfigurációs fájlba:

```bash
sudo nano /etc/openschool-maintenance.conf
```

```bash
# Discord webhook értesítések
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijk...
```

### Tesztelés

```bash
# Kézi teszt — a health check küld értesítést, ha baj van
./scripts/maintenance.sh health

# Direkt webhook teszt
curl -s -X POST "$DISCORD_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"content": "**[OpenSchool]** Teszt értesítés — a monitoring működik!"}'
```

### Mikor küld értesítést?

| Esemény | Webhook üzenet |
|---------|---------------|
| Mentés sikertelen | DB nem elérhető, backup hiba |
| Health check hiba | Konténer leállt, /health nem válaszol |
| Lemezhasználat ≥90% | Kritikus lemezhasználat figyelmeztetés |
| SSL lejár ≤30 napon belül | Tanúsítvány lejárati figyelmeztetés |
| SSL lejárt | Azonnali riasztás |

### Discord csatorna ajánlás

Érdemes egy dedikált `#ops-alerts` vagy `#monitoring` csatornát létrehozni a szerveren, ahol csak az automatizált értesítések jelennek meg. Így nem keverednek a többi üzenettel, és könnyen konfigurálhatsz rá Discord értesítési szabályokat (pl. `@here` mention).

---

## 6. lépés — Titkos kulcsok (secrets) kezelése

A produkciós környezetben számos érzékeny adat van: adatbázis jelszavak, JWT secret, GitHub OAuth kulcsok. Ezeket biztonságosan kell kezelni.

### A) Docker Secrets (ajánlott Docker Swarm nélkül is)

A legegyszerűbb módszer: a titkokat `.env.prod` fájlban tárolni, megfelelő jogosultságokkal:

```bash
# .env.prod létrehozása (ha még nincs)
sudo nano /opt/openschool/.env.prod

# Szigorú jogosultságok beállítása — csak a tulajdonos olvashatja
sudo chmod 600 /opt/openschool/.env.prod
sudo chown root:root /opt/openschool/.env.prod
```

### B) Erős secret-ek generálása

```bash
# JWT / SECRET_KEY generálás (legalább 32 karakter)
openssl rand -hex 32

# Adatbázis jelszó generálás
openssl rand -base64 24

# GitHub webhook secret generálás
openssl rand -hex 20
```

### C) Titkos kulcsok kezelése `pass`-szal (ajánlott)

A [`pass`](https://www.passwordstore.org/) egy Unix szabványos, GPG-alapú jelszókezelő. A titkokat titkosítva tárolja, és Git-ben is biztonságosan verzionálható.

#### Telepítés és inicializálás

```bash
# Telepítés
sudo apt install -y pass gnupg

# GPG kulcs generálás (ha még nincs)
gpg --full-generate-key
# Válaszd: RSA and RSA, 4096 bit, nem jár le
# Jegyezd meg a GPG key ID-t (pl. ABCD1234EFGH5678)

# pass inicializálás a GPG kulccsal
pass init "ABCD1234EFGH5678"
```

#### Titkos kulcsok tárolása

```bash
# Titkos kulcsok hozzáadása
pass insert openschool/db-password
pass insert openschool/secret-key
pass insert openschool/github-client-secret
pass insert openschool/github-webhook-secret
pass insert openschool/discord-webhook-url

# Generálás + tárolás egyben (32 karakteres jelszó)
pass generate openschool/secret-key 32
pass generate openschool/db-password 24
```

#### Titkos kulcsok használata a deploy-ban

```bash
# .env.prod generálása a pass-ból
cat > /opt/openschool/.env.prod << EOF
DB_USER=openschool
DB_PASSWORD=$(pass openschool/db-password)
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:$(pass openschool/db-password)@db:5432/openschool
SECRET_KEY=$(pass openschool/secret-key)
ENVIRONMENT=production
GITHUB_CLIENT_ID=$(pass openschool/github-client-id)
GITHUB_CLIENT_SECRET=$(pass openschool/github-client-secret)
GITHUB_WEBHOOK_SECRET=$(pass openschool/github-webhook-secret)
EOF

chmod 600 /opt/openschool/.env.prod
```

#### Titkos kulcsok mentése

A `pass` store egy Git repo (`~/.password-store/`). Biztonságosan menthető privát Git szerverre:

```bash
# Pass store verzionálása
cd ~/.password-store
git remote add origin git@private-server:password-store.git
git push -u origin main
```

### D) GitHub Secrets (CI/CD-hez)

A CI/CD pipeline-ban használt titkos kulcsokat GitHub Secrets-ben tárold:

1. Menj a repository **Settings → Secrets and variables → Actions** oldalra
2. Kattints **New repository secret**
3. Az alábbi titkokat add hozzá:

| Secret név | Leírás | Hol használja |
|------------|--------|---------------|
| `VPS_HOST` | VPS IP vagy domain | CD deploy |
| `VPS_USER` | SSH felhasználó | CD deploy |
| `VPS_SSH_KEY` | SSH privát kulcs | CD deploy |
| `STAGING_HOST` | Staging szerver (opcionális) | CD staging deploy |
| `STAGING_USER` | Staging SSH felhasználó | CD staging deploy |
| `STAGING_SSH_KEY` | Staging SSH kulcs | CD staging deploy |

> **Fontos:** Soha ne commitolj titkos kulcsot Git-be! A `.env` és `.env.prod` fájlok a `.gitignore`-ban vannak.

### E) Secret rotáció ütemezés

| Titok | Rotáció gyakorisága | Generálási parancs |
|-------|---------------------|-------------------|
| `SECRET_KEY` (JWT) | Negyedévente | `openssl rand -hex 32` |
| DB jelszó | Negyedévente | `openssl rand -base64 24` |
| GitHub OAuth | Évente | GitHub Developer Settings regenerálás |
| `GITHUB_WEBHOOK_SECRET` | Negyedévente | `openssl rand -hex 20` |
| SSH kulcsok | Évente | `ssh-keygen -t ed25519` |
| Discord webhook | Szükség esetén | Discord csatorna beállítások |

Secret rotáció lépései:

1. Új titok generálása
2. Frissítés a `pass`-ban: `pass edit openschool/<titok-neve>`
3. `.env.prod` újragenerálása (lásd fent)
4. Szolgáltatások újraindítása: `docker compose -f docker-compose.prod.yml up -d`
5. Működés ellenőrzése: `./scripts/maintenance.sh health`
6. GitHub Secrets frissítése (ha szükséges)

---

## 7. lépés — SSL automatikus megújítás Let's Encrypt-tel (opcionális)

Ha Let's Encrypt-et használsz SSL-hez, állítsd be az automatikus megújítást:

```bash
# Certbot telepítése
sudo apt install -y certbot

# Tanúsítvány lekérése (ha még nincs)
sudo certbot certonly --standalone -d yourdomain.com

# Auto-megújítás ellenőrzése (certbot általában beállítja):
sudo systemctl status certbot.timer

# Vagy manuálisan cron-ba (naponta kétszer, a Let's Encrypt ajánlása szerint)
echo "0 */12 * * * root certbot renew --quiet --deploy-hook 'docker compose -f /opt/openschool/docker-compose.prod.yml restart nginx'" \
  | sudo tee -a /etc/cron.d/openschool-maintenance
```

A `maintenance.sh ssl-check` parancs figyeli a tanúsítvány lejáratát és N nappal előtte figyelmeztet (alapértelmezés: 30 nap), biztonsági hálóként az auto-megújítás mellett is.

---

## Teljes cron ütemezés referencia

A beállítás után ezek a feladatok futnak automatikusan:

```
┌──────────── Perc
│  ┌───────── Óra
│  │  ┌────── Hónap napja
│  │  │  ┌─── Hónap
│  │  │  │ ┌─ Hét napja
│  │  │  │ │
0  2  *  * *   full-daily    → mentés, health check, log vizsgálat
0  3  *  * 0   full-weekly   → + lemez, cleanup, DB statisztikák (vasárnap)
0  4  1  * *   full-monthly  → + SSL, biztonsági audit (hónap eleje)

Folyamatos (Docker által kezelt):
  - Backend health check 30 másodpercenként (/health endpoint)
  - DB elérhetőség ellenőrzés 10 másodpercenként (pg_isready)
  - Nginx health check 30 másodpercenként

Folyamatos (GitHub által kezelt):
  - Dependabot: heti pip, havi Actions
  - CI: minden push/PR-kor (lint + teszt)
  - CD: minden main merge-kor (deploy)
```

---

## Karbantartási rendszer monitorozása

```bash
# Karbantartási napló megtekintése
tail -f /var/log/openschool-maintenance.log

# Utolsó futások eredményei
grep -E '\[(OK|WARN|ERROR)\]' /var/log/openschool-maintenance.log | tail -20

# Cron futásának ellenőrzése
grep -i openschool /var/log/syslog | tail -10

# Mentés frissessége (legyen <24 órás)
ls -lt /opt/openschool/backups/ | head -5
```

---

## Hibaelhárítás

| Probléma | Ellenőrzés | Megoldás |
|----------|-----------|----------|
| Cron nem fut | `systemctl status cron` | `sudo systemctl start cron` |
| Mentés sikertelen | `maintenance.sh backup` manuálisan | `DB_USER`/`DB_NAME` ellenőrzése a `.env.prod`-ban |
| Jogosultság hiba | `ls -la scripts/maintenance.sh` | `chmod +x scripts/maintenance.sh` |
| SSL check kihagyva | `SSL_DOMAIN` a conf-ban | `SSL_DOMAIN=yourdomain.com` beállítása |
| Discord nem küld | Webhook URL ellenőrzése | `curl -X POST` teszt (lásd 5. lépés) |
| Docker cleanup hiba | `docker system df` | Docker daemon + lemez ellenőrzése |
| Napló túl nagy | `/etc/logrotate.d/` ellenőrzése | `sudo logrotate -f /etc/logrotate.d/openschool-maintenance` |

---

## Negyedéves manuális feladatok

Néhány feladat nem automatizálható teljesen és emberi átvizsgálást igényel:

1. **Secret rotáció** — `SECRET_KEY`, DB jelszó, GitHub OAuth, webhook secret frissítése (lásd 6. lépés E pont)
2. **Biztonsági checklist** — Negyedéves checklist futtatása: [karbantartas-utmutato.md § 8](karbantartas-utmutato.md)
3. **Mentés visszaállítás teszt** — Ellenőrizd, hogy a mentések tényleg visszaállíthatók
4. **Függőségek major frissítései** — Breaking change-es Dependabot PR-ok átnézése
5. **Python verzió** — Új Python verziók ellenőrzése (félévente)
