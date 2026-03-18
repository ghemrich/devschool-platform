# Karbantartás és minőségbiztosítás

Fejlesztési munkafolyamat, minőségkapuk, függőségkezelés, monitorozás, adatbázis karbantartás, incidenskezelés, biztonsági gyakorlatok.

## 1. Fejlesztési munkafolyamat

### Branch stratégia

```
main          ← stabil, éles verzió (CD automatikusan deploy-ol)
develop       ← integráció, CI fut rajta
feature/xyz   ← új funkciók
fix/xyz       ← hibajavítások
```

### PR folyamat

1. Feature branch `develop`-ról
2. Fejlesztés + tesztek
3. `ruff check` + `ruff format` lokálisan
4. PR → CI automatikusan lint + test
5. Code review (≥1 jóváhagyás)
6. Merge `develop`-ba → tesztelés
7. `develop` → `main` → CD deploy

### Commit konvenciók

```
feat: új funkció          fix: hibajavítás         docs: dokumentáció
chore: karbantartás       ci: CI/CD változás       refactor: átstrukturálás
test: teszt módosítás     security: biztonsági javítás
```

A `git-cliff` ezeket használja a `CHANGELOG.md` generálásához (`cliff.toml` konfig).

## 2. Függőségkezelés

### Dependabot

`.github/dependabot.yml` — pip csomagok hetente, GitHub Actions havonta.

PR kezelés: CI tesztek → changelog/breaking changes ellenőrzése → merge ha zöld.

### Manuális frissítés

```bash
pip list --outdated        # elavult csomagok
pip-audit                  # biztonsági audit
pip install --upgrade <pkg>
pytest                     # kötelező tesztelés frissítés után
```

| Feladat | Gyakoriság |
|---------|-----------|
| Dependabot PR review | Hetente |
| `pip-audit` | Havonta |
| GitHub Security Advisories | Havonta |
| Python verzió frissítés | Félévente |

## 3. Minőségkapuk

| Szint | Eszköz | Parancs | Elvárt |
|-------|--------|---------|--------|
| Backend lint | ruff | `ruff check backend/` | 0 hiba |
| Backend formázás | ruff | `ruff format --check backend/` | 0 eltérés |
| Frontend lint | ESLint | `cd frontend && npx eslint .` | 0 hiba |
| Frontend formázás | Prettier | `npx prettier --check 'src/**/*.{ts,tsx,css}'` | 0 eltérés |
| Frontend típusok | TypeScript | `npx tsc --noEmit` | 0 hiba |
| Backend tesztek | pytest | `pytest` | 100% pass |
| Frontend tesztek | Vitest | `npx vitest run` | 100% pass |
| Lefedettség | pytest-cov | `pytest --cov=app --cov-report=term` | ≥80% |
| Biztonsági audit | pip-audit | `pip-audit` | 0 vulnerability |

CI pipeline: `Push/PR → lint (backend + frontend) → test (backend + frontend) → [main] → deploy`

## 4. Deployment checklist

- [ ] Minden teszt zöld
- [ ] Lint hibamentes (`make lint`)
- [ ] `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` = éles domain
- [ ] Migráció futtatva (`alembic upgrade head`)
- [ ] Docker image-ek újraépítve
- [ ] SSL tanúsítvány érvényes
- [ ] `/health` válaszol

### Éles deploy

```bash
cd /opt/openschool
git pull origin main
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build --force-recreate -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head
curl -s http://localhost:8000/health
```

### Rollback

```bash
git log --oneline -5
git checkout <commit-hash>
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build --force-recreate -d
```

## 5. Monitorozás

### Healthcheck (Docker automatikus)

```yaml
# docker-compose.prod.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

DB: `pg_isready` 10 másodpercenként. Nginx: `wget http://127.0.0.1/health` 30 másodpercenként.

### Logok

```bash
docker compose -f docker-compose.prod.yml logs --tail=50 backend
docker compose -f docker-compose.prod.yml logs -f backend        # valós idejű
docker compose -f docker-compose.prod.yml logs backend | grep -i error
```

Log rotáció: Docker JSON driver, konténerenként 10MB × 3 fájl.

### Rendszeres ellenőrzések

| Feladat | Gyakoriság | Módszer |
|---------|-----------|---------|
| Healthcheck | Folyamatos | Docker automatikus |
| Log review | Naponta | `docker logs --tail=100 backend` |
| Lemezhasználat | Hetente | `df -h` + `docker system df` |
| Container állapot | Naponta | `docker compose ps` |
| SSL lejárat | Havonta | `maintenance.sh ssl-check` |

## 6. Docker karbantartás

```bash
docker image prune -a --filter "until=720h"  # 30 napnál régebbi image-ek
docker system df                              # használat áttekintése
docker system prune -f                        # nem használt objektumok
```

## 7. Adatbázis karbantartás

### Backup

```bash
./scripts/maintenance.sh backup   # ajánlott — automatikus tömörítés + régi fájlok törlése

# Manuális
docker compose -f docker-compose.prod.yml exec db pg_dump -U openschool openschool > backup.sql
```

### Migráció munkafolyamat

1. Modell módosítása (`backend/app/models/`)
2. `alembic revision --autogenerate -m "leírás"`
3. Generált fájl ellenőrzése
4. `alembic upgrade head` + `pytest`
5. Élesben: `docker compose exec backend alembic upgrade head`

### Állapot ellenőrzés

```bash
./scripts/maintenance.sh db-status  # kapcsolatok, tábla méretek, verzió
docker compose exec backend alembic current
```

## 8. Incidenskezelés

1. **Észlelés:** healthcheck, felhasználói bejelentés, log riasztás
2. **Diagnosztika:** `docker compose ps` + `logs --tail=100` + DB elérés teszt
3. **Intézkedés:** service újraindítás vagy rollback
4. **Gyökérok:** log analízis, commit history
5. **Javítás:** hotfix branch → teszt → merge → deploy
6. **Dokumentálás:** issue + post-mortem

| Probléma | Megoldás |
|----------|----------|
| Backend nem indul | Env vars + DB elérés ellenőrzés |
| DB connection refused | DB container újraindítás |
| 502 Bad Gateway | Backend healthcheck, proxy_pass |
| Lassú válaszidő | DB query optimalizálás, index |
| Disk full | Log rotáció, `docker image prune` |

## 9. Biztonsági karbantartás

| Feladat | Gyakoriság |
|---------|-----------|
| Dependabot PR merge | Hetente |
| `pip-audit` | Havonta |
| Secret rotáció | Negyedévente |
| Nginx security headers | Deploy-onként |
| Docker base image frissítés | Havonta |
| SSL ellenőrzés | Havonta |

### Negyedéves checklist

- [ ] Függőségek naprakészek
- [ ] `pip-audit` 0 vulnerability
- [ ] SECRET_KEY erős (≥32 karakter)
- [ ] CORS csak éles domain
- [ ] Swagger UI letiltva production-ben
- [ ] Nginx security headers aktívak
- [ ] SSL A+ minősítés
- [ ] Branch protection aktív
- [ ] Backup visszaállítás tesztelve

## 10. Éves naptár

| Hónap | Feladat |
|-------|---------|
| Január | Python verzió ellenőrzés, éves audit |
| Március | Dependabot konfig review |
| Május | Docker base image frissítés |
| Július | Teljesítmény review, DB optimalizáció |
| Szeptember | SSL megújítás (ha nem auto) |
| November | Backup/restore teszt, disaster recovery próba |
| Folyamatos | Dependabot, log review, healthcheck |
