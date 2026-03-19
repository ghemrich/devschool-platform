# Jövőkép és roadmap

## Filozófia

> **Az open source nem feature — az open source a tanterv.**

Az OpenSchool Platform nem egy hagyományos LMS. A tanulók a platform kódján keresztül tanulnak programozni — a tananyag, az eszközök, az értékelés és maga a platform is nyílt forráskódú. Aki tanul, az hozzájárul; aki hozzájárul, az tanul.

## Növekedési modell

```
Tanuló → Kontribútor → Mentor → Maintainer
```

1. **Tanuló** — kurzusokat végez, feladatokat old meg GitHub Classroom-ban
2. **Kontribútor** — PR-eket küld a platformhoz (bugfix, feature, docs)
3. **Mentor** — code review-t végez, segít a tanulóknak, kurzusokat kezel
4. **Maintainer** — az infrastruktúra és a projekt irányítása

Az előléptetés automatizálható: tanúsítvány-kombináció → szerepkörváltás (promotion rules).

## Megvalósított funkciók

### Platform core
- GitHub OAuth bejelentkezés (JWT, httpOnly cookie-k, token rotáció)
- Szerepkör-alapú hozzáférés (student, mentor, admin)
- Kurzus/modul/feladat CRUD (admin panel)
- Beiratkozás és leiratkozás
- Haladáskövetés (manuális + automatikus)
- Tanúsítvány generálás (PDF + QR kód + publikus verifikáció)
- Előléptetési szabályok (automatikus szerepkörváltás tanúsítványok alapján)
- Mentor dashboard (diákok haladásának áttekintése kurzusonként)

### Integrációk
- GitHub Classroom — feladat összekötés (`repo_prefix`), webhook haladásfrissítés, sync-progress, assignment import (Classroom API)
- GitHub Organization — automatikus org meghívás bejelentkezéskor
- Discord webhook értesítések (beiratkozás, tanúsítvány, előléptetés)
- Discord szerepkör szinkronizáció (Bot API)

### Infrastruktúra
- Docker Compose (dev, staging, production)
- CI/CD (GitHub Actions — lint, test, deploy)
- VPS automatizálás (bootstrap, cron, maintenance, monitoring)
- Staging környezet (elkülönített, ugyanazon a VPS-en)
- Let's Encrypt SSL + Cloudflare kompatibilitás

### Minőségbiztosítás
- 156 teszt (118 backend pytest + 38 frontend Vitest)
- Ruff linter + ESLint + Prettier
- Dependabot (heti pip, havi Actions)
- pip-audit, security-check.sh

## Következő lépések

> Ezek irányok, nem ígéretek. A prioritásokat a közösség igényei határozzák meg.

### Rövid táv
- [ ] E-mail értesítések (opcionális, a Discord mellé)
- [ ] Rate limiting finomhangolás (végpontonként konfigurálható)

### Közép táv
- [ ] Leaderboard / rangsor (opt-in, kurzusonként)
- [ ] Haladási statisztikák és grafikonok (admin + tanuló)
- [ ] Discord bot (kétirányú integráció: parancsok, automatikus szálak)
- [ ] Többnyelvűség (i18n) — magyar + angol
- [ ] Keresés kurzusokban és feladatokban

### Hosszú táv
- [ ] Peer review rendszer (tanulók egymás kódját nézik)
- [ ] Achievement / badge rendszer
- [ ] Mobil-optimalizált nézet
- [ ] API kulcs hitelesítés (külső kliensek számára)
- [ ] Plugin rendszer (egyedi értékelő logika)

## Hozzájárulás

Az egyes elemekhez GitHub issue-k tartoznak (vagy tartozni fognak). Ha valamit el szeretnél kezdeni, nyiss egy issue-t, hogy egyeztessünk az irányvonalról.

Lásd: [CONTRIBUTING.md](../CONTRIBUTING.md)
