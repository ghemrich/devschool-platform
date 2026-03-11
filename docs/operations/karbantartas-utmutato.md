# Karbantartás és minőségbiztosítás

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · **Karbantartás** · [Automatizálás](automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a OpenSchool Platform hosszú távú karbantartásához, minőségbiztosításához és üzemeltetéséhez szükséges folyamatokat és gyakorlatokat írja le.

---

## 1. Fejlesztési munkafolyamat

### Branch stratégia

```
main          ← stabil, éles verzió (CD automatikusan deploy-ol)
develop       ← integráció, CI fut rajta
feature/xyz   ← új funkciók
fix/xyz       ← hibajavítások
```

### PR folyamat

1. Feature branch létrehozása `develop`-ról
2. Fejlesztés + tesztek írása
3. `ruff check` és `ruff format` futtatása lokálisan
4. PR nyitása → CI automatikusan futtatja a lint + test lépéseket
5. Code review (legalább 1 jóváhagyás)
6. Merge `develop`-ba → végső tesztelés
7. `develop` → `main` merge → CD automatikusan deploy-ol

### Commit konvenciók

```
feat: új funkció hozzáadása
fix: hibajavítás
docs: dokumentáció frissítése
chore: karbantartás, függőségek
ci: CI/CD pipeline változások
refactor: kód átstrukturálás
test: teszt hozzáadás/módosítás
security: biztonsági javítás
```

> **Fontos:** Ezeket a prefixeket a `git-cliff` eszköz használja a `CHANGELOG.md` automatikus generálásához. Részletek: [Fejlesztői útmutató — 8. Változásnapló](../development/fejlesztoi-utmutato.md#8-változásnapló-git-cliff)

## 2. Függőségkezelés

### Dependabot

A projekt Dependabot-ot használ automatikus függőség-frissítéshez (`.github/dependabot.yml`):

- **pip csomagok:** heti frissítés, `dependencies` címke
- **GitHub Actions:** havi frissítés, `dependencies` címke

Dependabot PR-ok kezelése:

1. PR megnyílik automatikusan
2. CI tesztek futnak
3. Changelog és breaking changes ellenőrzése
4. Merge ha zöld + nincs breaking change

### Manuális frissítés

```bash
# Elavult csomagok listázása
pip list --outdated

# Biztonsági audit
pip-audit

# Frissítés
pip install --upgrade <csomag>
# Produkciós csomag → requirements.txt kézzel frissítsd
# Fejlesztői csomag → requirements-dev.txt kézzel frissítsd

# Tesztek futtatása frissítés után (kötelező!)
pytest
```

### Biztonsági audit ütemezés

| Feladat | Gyakoriság |
|---------|-----------|
| Dependabot PR-ok review | Hetente |
| `pip-audit` futtatás | Havonta |
| GitHub Security Advisories ellenőrzés | Havonta |
| Python verzió frissítés | Félévente |

## 3. Tesztelés és minőségkapuk

### Minőségkapu táblázat

| Szint | Eszköz | Parancs | Elvárt |
|-------|--------|---------|--------|
| Lint | ruff | `ruff check backend/` | 0 hiba |
| Formázás | ruff | `ruff format --check backend/` | 0 eltérés |
| Unit tesztek | pytest | `pytest` | 100% pass |
| Lefedettség | pytest-cov | `pytest --cov=app --cov-report=term` | ≥80% |
| Biztonsági audit | pip-audit | `pip-audit` | 0 vulnerability |

### Tesztelési gyakorlatok

- Minden új endpoint-hoz teszteset írása
- Minden bugfix-hez regressziós teszt
- Happy path + error path lefedése
- Adatbázis tesztek: in-memory SQLite fixture használata

### CI pipeline (automatikus)

```
Push/PR → Lint (ruff check + format) → Tesztek (pytest) → [main branch] → Deploy
```

## 4. Telepítés és üzemeltetés

### Deployment checklist

Mielőtt élesbe megy egy új verzió:

- [ ] Minden teszt zöld (`pytest`)
- [ ] Lint hibamentes (`ruff check` + `ruff format --check`)
- [ ] Környezeti változók beállítva (`.env`)
- [ ] `ENVIRONMENT=production` beállítva
- [ ] `ALLOWED_ORIGINS` tartalmazza az éles domain-t
- [ ] Adatbázis migráció futtatva (`alembic upgrade head`)
- [ ] Docker image-ek újraépítve
- [ ] Nginx konfiguráció ellenőrizve (security headers)
- [ ] SSL tanúsítvány érvényes
- [ ] Healthcheck endpoint válaszol (`/health`)

### Éles deploy folyamat

```bash
# VPS-en (SSH-val)
cd /opt/openschool
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Ellenőrzés
docker compose -f docker-compose.prod.yml ps
curl -s http://localhost:8000/health
docker compose -f docker-compose.prod.yml logs --tail=20 backend
```

### Rollback

```bash
# Előző verzióra visszaállás
git log --oneline -5              # utolsó 5 commit
git checkout <commit-hash>        # visszaállás
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## 5. Monitorozás

### Healthcheck

A backend `/health` endpoint-ja automatikusan monitorozott a Docker healthcheck által:

```yaml
# docker-compose.prod.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

### Log ellenőrzés

```bash
# Backend logok (strukturált JSON formátum production-ben)
docker compose -f docker-compose.prod.yml logs --tail=50 backend

# Nginx logok (access + error)
docker compose -f docker-compose.prod.yml logs --tail=50 nginx

# Valós idejű log követés
docker compose -f docker-compose.prod.yml logs -f backend

# Hiba szűrés
docker compose -f docker-compose.prod.yml logs backend | grep -i error
```

### Rendszeres ellenőrzések

| Feladat | Gyakoriság | Parancs/Módszer |
|---------|-----------|-----------------|
| Healthcheck válasz | Folyamatos | Docker automatikus |
| Log review | Naponta | `docker logs --tail=100 backend` |
| Lemezhasználat | Hetente | `df -h` + `docker system df` |
| Container állapot | Naponta | `docker compose ps` |
| SSL lejárat | Havonta | `openssl s_client -connect domain:443` |

### Docker karbantartás

```bash
# Nem használt image-ek törlése
docker image prune -a --filter "until=720h"  # 30 napnál régebbiek

# Nem használt volume-ok (vigyázat: adatvesztés!)
docker volume ls
# Csak biztonságos: docker volume prune --filter "label!=keep"

# Rendszer szintű takarítás
docker system df          # használat áttekintése
docker system prune -f    # nem használt objektumok törlése
```

## 6. Adatbázis karbantartás

### Backup

> **Ajánlott:** Használd a `scripts/maintenance.sh backup` parancsot, ami automatikusan kezeli a hozzáférési adatokat, tömörítést és a régi mentések törlését. Részletek: [Automatizálás — 3. lépés](automatizalas-beallitas.md#3-lépés--mentési-könyvtár-beállítása)

```bash
# Ajánlott módszer (a .env fájlból olvassa a DB_USER/DB_NAME értékeket)
./scripts/maintenance.sh backup

# Manuális backup
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U openschool openschool > backup_$(date +%Y%m%d).sql

# Backup visszaállítás
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U openschool openschool < backup_20260311.sql
```

### Automatikus backup (cron)

A projekt tartalmaz automatikus cron job-okat, amelyek a `maintenance.sh` szkriptet használják. Részletek: [Automatizálás — 2. lépés](automatizalas-beallitas.md#2-lépés--cron-jobok-telepítése)

```bash
# Cron job-ok telepítése
sudo ./scripts/setup-cron.sh

# Vagy egyszerűbben: Makefile-lal
make install-cron
```

### Migráció munkafolyamat

```bash
# 1. Modell módosítása (backend/app/models/)
# 2. Migráció generálása
cd backend
alembic revision --autogenerate -m "leírás"

# 3. Migráció ellenőrzése
cat alembic/versions/<latest>.py

# 4. Migráció futtatása (dev)
alembic upgrade head

# 5. Tesztelés
pytest

# 6. Éles futtatás (deploy után automatikus, vagy manuálisan)
docker compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head
```

### Adatbázis állapot ellenőrzés

```bash
# Gyors ellenőrzés (maintenance szkript)
./scripts/maintenance.sh db-status

# Aktuális migráció verzió
docker compose -f docker-compose.prod.yml exec backend alembic current

# Tábla méretek
docker compose -f docker-compose.prod.yml exec db \
  psql -U openschool -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
  FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;"

# Aktív kapcsolatok
docker compose -f docker-compose.prod.yml exec db \
  psql -U openschool -c "SELECT count(*) FROM pg_stat_activity;"
```

## 7. Incidenskezelés

### Hibaelhárítási folyamat

1. **Észlelés:** Healthcheck hiba, felhasználói bejelentés, log riasztás
2. **Diagnosztika:**
   ```bash
   docker compose -f docker-compose.prod.yml ps       # service állapot
   docker compose -f docker-compose.prod.yml logs --tail=100 backend  # logok
   docker compose -f docker-compose.prod.yml exec db psql -U openschool -c "SELECT 1;"  # DB elérés
   ```
3. **Azonnali intézkedés:**
   - Service újraindítás: `docker compose -f docker-compose.prod.yml restart backend`
   - Rollback ha szükséges (lásd fent)
4. **Gyökérok feltárás:** Log analízis, commit history átvizsgálás
5. **Javítás:** Hotfix branch → tesztelés → merge → deploy
6. **Dokumentálás:** Issue létrehozása, post-mortem leírás

### Gyakori problémák és megoldások

| Probléma | Diagnosztika | Megoldás |
|----------|-------------|----------|
| Backend nem indul | `docker logs backend` | Env vars ellenőrzés, DB elérés |
| DB connection refused | `docker compose ps db` | DB container újraindítás |
| 502 Bad Gateway | `docker logs nginx` | Backend healthcheck, proxy_pass |
| Lassú válaszidő | Backend logok, DB query-k | Index hozzáadás, N+1 query javítás |
| Disk full | `df -h`, `docker system df` | Log rotáció, image prune |

## 8. Biztonsági karbantartás

### Rendszeres biztonsági feladatok

| Feladat | Gyakoriság | Leírás |
|---------|-----------|--------|
| Függőség frissítés | Hetente | Dependabot PR-ok merge |
| `pip-audit` | Havonta | Ismert sebezhetőségek keresése |
| Secret rotation | Negyedévente | `JWT_SECRET`, DB jelszó, GitHub OAuth |
| Nginx security headers | Deploy-onként | Ellenőrzés: [securityheaders.com](https://securityheaders.com) |
| Docker base image | Havonta | `python:3.12-slim` frissítés |
| SSL tanúsítvány | Havonta | Lejárat ellenőrzés |

### Secret kezelés

- Secrets **soha** nem kerülnek Git-be
- `.env` fájl a `.gitignore`-ban van
- GitHub Secrets a CI/CD-hez (`Settings > Secrets and variables > Actions`)
- Éles env vars: közvetlenül a VPS-en beállítva

### Biztonsági checklist (negyedéves)

- [ ] Minden függőség naprakész
- [ ] `pip-audit` 0 vulnerability
- [ ] JWT_SECRET erős és egyedi (≥32 karakter)
- [ ] CORS only az éles domain-re engedélyezett
- [ ] Swagger UI letiltva production-ben
- [ ] Nginx security headers aktívak
- [ ] SSL A+ minősítés
- [ ] GitHub branch protection aktív
- [ ] Backup tesztelve (visszaállítás)
- [ ] Docker image-ek frissek

## 9. Éves karbantartási naptár

| Hónap | Feladat |
|-------|---------|
| Január | Python verzió ellenőrzés, éves biztonsági audit |
| Március | Dependabot konfiguráció review |
| Május | Docker base image frissítés |
| Július | Teljesítmény review, DB optimalizáció |
| Szeptember | SSL tanúsítvány megújítás (ha nem auto-renew) |
| November | Backup/restore teszt, disaster recovery próba |
| Folyamatos | Dependabot PR-ok, log review, healthcheck |
