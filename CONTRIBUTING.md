# Hozzájárulás az OpenSchool Platformhoz

> 📖 **Dokumentáció:** [Főoldal](README.md) · [Architektúra](docs/getting-started/architektura.md) · [Telepítés](docs/getting-started/telepitesi-utmutato.md) · [Környezeti változók](docs/getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](docs/development/fejlesztoi-utmutato.md) · [Backend](docs/development/backend-fejlesztes.md) · [Frontend](docs/development/frontend-fejlesztes.md) · [Tesztelés](docs/development/tesztelesi-utmutato.md) · [API referencia](docs/reference/api-referencia.md) · [Adatbázis](docs/reference/adatbazis-sema.md) · [Karbantartás](docs/operations/karbantartas-utmutato.md) · [Automatizálás](docs/operations/automatizalas-beallitas.md) · [GitHub Classroom](docs/integrations/github-classroom-integraciot.md) · [Discord](docs/integrations/discord-integracio.md) · [Felhasználói útmutató](docs/guides/felhasznaloi-utmutato.md) · [Dokumentálás](docs/guides/dokumentacios-utmutato.md) · [Roadmap](docs/jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](CONTRIBUTING.md)

Köszönjük, hogy hozzá szeretnél járulni az OpenSchool fejlesztéséhez! Ez az útmutató segít az indulásban.

## Hogyan indulj el

### 1. Fork és klónozás

```bash
# Forkold a repót a GitHubon, majd klónozd
git clone https://github.com/<te-felhasználóneved>/openschool-platform.git
cd openschool-platform
```

### 2. Lokális fejlesztői környezet felállítása

Részletes útmutató: [Fejlesztői útmutató](docs/development/fejlesztoi-utmutato.md)

Gyors összefoglalás:

```bash
# Python virtuális környezet
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# .env fájl létrehozása
cp .env.example .env

# Tesztek futtatása
pytest -v

# Linter ellenőrzés
ruff check . && ruff format --check .
```

### 3. Frontend fejlesztés

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker-rel való futtatás

```bash
docker compose up --build -d
curl http://localhost:8000/health
```

## Issue-k

- Nézd meg a [meglévő issue-kat](../../issues), mielőtt újat nyitsz
- Használd az issue template-eket (bug report / feature request / documentation / question)
- A `good first issue` címkéjű issue-k ideálisak kezdőknek
- Mielőtt nagyobb változtatásba kezdesz, nyiss egy issue-t és egyeztessünk

## Branch stratégia

```
main ──────────────────── (éles, védett)
  │
  ├── develop ─────────── (staging)
  │     │
  │     ├── feature/...  (új funkció)
  │     ├── fix/...      (hibajavítás)
  │     └── docs/...     (dokumentáció)
```

### Branch elnevezés

- `feature/<rövid-leírás>` — új funkció (pl. `feature/user-profile`)
- `fix/<rövid-leírás>` — hibajavítás (pl. `fix/login-redirect`)
- `docs/<rövid-leírás>` — dokumentáció (pl. `docs/api-guide`)

## Commit üzenetek

A [Conventional Commits](https://www.conventionalcommits.org/) konvenciót követjük:

- `feat:` — új funkció
- `fix:` — hibajavítás
- `docs:` — dokumentáció
- `test:` — tesztek
- `refactor:` — refaktorálás
- `chore:` — egyéb (CI, build, dependencies)

Példa: `feat: add user profile page`

## Pull Request küldése

1. Hozz létre egy branch-et a `develop`-ból:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/az-en-funkciom
   ```

2. Végezd el a módosításokat, írd meg a teszteket

3. Ellenőrizd, hogy minden rendben:
   ```bash
   pytest -v
   ruff check . && ruff format --check .
   ```

4. Commitold és pushold:
   ```bash
   git add .
   git commit -m "feat: rövid leírás"
   git push origin feature/az-en-funkciom
   ```

5. Nyiss egy Pull Request-et a `develop` branch-be a GitHub-on

### PR ellenőrzőlista

- [ ] A tesztek zöldek (`pytest -v`)
- [ ] A linter nem jelez hibát (`ruff check .`)
- [ ] Új publikus függvényeknek van docstring-jük
- [ ] Az érintett dokumentáció frissítve van (lásd: [Dokumentálási útmutató](docs/guides/dokumentacios-utmutato.md))
- [ ] A `README.md` API táblázata és docs indexe naprakész
- [ ] A PR leírás tartalmazza a változtatás célját

## Code review

- Minden PR-hez legalább 1 reviewer jóváhagyása szükséges
- A review-ra általában 1-2 munkanapon belül válaszolunk
- Konstruktív visszajelzésre törekszünk — kérdéseket teszünk fel, nem kritizálunk

## Kódstílus

- **Python:** [ruff](https://docs.astral.sh/ruff/) linter és formatter, max. 120 karakter/sor
- **Tesztek:** pytest, a tesztfájlok a `backend/tests/` mappában
- **Típusannotáció:** ajánlott, de nem kötelező

## Közösségi szerepkörök

| Szerepkör | Elérés módja | Jogosultság |
|-----------|-------------|-------------|
| **Tanuló** | Beiratkozás egy kurzusra | Részvétel, issue nyitás |
| **Kontribútor** | Legalább 1 elfogadott PR | Contributor címke |
| **Mentor** | 5+ elfogadott PR + aktív code review | Code review jogosultság |
| **Maintainer** | Meghívás a core csapattól | Write access, release |

## Kérdésed van?

Nyiss egy [issue-t](../../issues) vagy keress minket a Discord szerveren!
