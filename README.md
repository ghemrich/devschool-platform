# OpenSchool Platform

[![CI](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/ghemrich/openschool-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Nyílt forráskódú oktatási platform, ahol a diákok valódi fejlesztői eszközökkel tanulnak programozni.

> **Az open source nem feature — az open source a tanterv.**

Nem csak a szoftver nyílt: a tananyag, az eszközök, az értékelés, a platform kódja — minden látható, minden módosítható.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Adatbázis:** PostgreSQL
- **Frontend:** Astro (statikus oldal generátor)
- **Infrastruktúra:** Docker Compose, nginx, GitHub Actions

## Gyors indítás

### Előfeltételek

- Docker és Docker Compose
- Python 3.12+ (lokális fejlesztéshez)

### Futtatás Docker-rel

```bash
# .env fájl létrehozása
cp .env.example .env

# Indítás
docker compose up --build -d

# Ellenőrzés
curl http://localhost:8000/health
```

Lokális fejlesztéshez lásd: [Fejlesztői útmutató](docs/development/fejlesztoi-utmutato.md)

## Hozzájárulás

Szívesen fogadjuk a hozzájárulásokat! Olvasd el a [CONTRIBUTING.md](CONTRIBUTING.md) fájlt a részletekért.

## Dokumentáció

### 🏠 Kezdőlépések

| Dokumentum | Leírás |
|---|---|
| [Architektúra](docs/getting-started/architektura.md) | Rendszer felépítés, adatmodell, auth folyamat |
| [Telepítési útmutató](docs/getting-started/telepitesi-utmutato.md) | Helyi fejlesztés, staging, VPS telepítés |
| [Környezeti változók](docs/getting-started/kornyezeti-valtozok.md) | Env var referencia, Docker, GitHub Actions secrets |

### 🛠️ Fejlesztés

| Dokumentum | Leírás |
|---|---|
| [Fejlesztői útmutató](docs/development/fejlesztoi-utmutato.md) | Környezet beállítás, VS Code, Docker, CI/CD |
| [Backend](docs/development/backend-fejlesztes.md) | FastAPI, modellek, Ruff, pytest, Alembic |
| [Frontend](docs/development/frontend-fejlesztes.md) | Astro oldalak, komponensek, admin panel |
| [Tesztelés](docs/development/tesztelesi-utmutato.md) | Tesztek futtatása, fixture-ök, CI integráció |

### 📚 Referencia

| Dokumentum | Leírás |
|---|---|
| [API referencia](docs/reference/api-referencia.md) | Összes végpont, sémák, státuszkódok |
| [Adatbázis séma](docs/reference/adatbazis-sema.md) | Táblák, kapcsolatok, Alembic migrációk |

### ⚙️ Üzemeltetés & Integrációk

| Dokumentum | Leírás |
|---|---|
| [Karbantartás](docs/operations/karbantartas-utmutato.md) | Monitoring, backup, biztonsági audit |
| [Automatizálás](docs/operations/automatizalas-beallitas.md) | Cron jobok, VPS bootstrap, secrets kezelés |
| [GitHub Classroom](docs/integrations/github-classroom-integraciot.md) | Feladatok összekötése, webhook, tanári útmutató |
| [Discord](docs/integrations/discord-integracio.md) | Discord szerver, webhook, CI/CD értesítések |

### 📖 Útmutatók

| Dokumentum | Leírás |
|---|---|
| [Felhasználói útmutató](docs/guides/felhasznaloi-utmutato.md) | Oldalak, felhasználói folyamatok, admin panel |
| [Dokumentálás](docs/guides/dokumentacios-utmutato.md) | Docstring-ek, Markdown konvenciók, navsáv |
| [Jövőkép és roadmap](docs/jovokep-es-fejlesztesi-terv.md) | Megvalósított funkciók, tervezett fejlesztések |
| [Hozzájárulás](CONTRIBUTING.md) | Fork, branch stratégia, PR küldés, kódstílus |

A `good first issue` címkéjű [issue-k](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) ideálisak kezdőknek.

## Licensz

A projekt az [MIT License](LICENSE) alatt érhető el.
