# OpenSchool Platform — Jövőkép és fejlesztési terv

> 📖 **Dokumentáció:** [Főoldal](../README.md) · [Architektúra](getting-started/architektura.md) · [Telepítés](getting-started/telepitesi-utmutato.md) · [Környezeti változók](getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](development/fejlesztoi-utmutato.md) · [Backend](development/backend-fejlesztes.md) · [Frontend](development/frontend-fejlesztes.md) · [Tesztelés](development/tesztelesi-utmutato.md) · [API referencia](reference/api-referencia.md) · [Adatbázis](reference/adatbazis-sema.md) · [Karbantartás](operations/karbantartas-utmutato.md) · [Automatizálás](operations/automatizalas-beallitas.md) · [GitHub Classroom](integrations/github-classroom-integraciot.md) · [Discord](integrations/discord-integracio.md) · [Felhasználói útmutató](guides/felhasznaloi-utmutato.md) · [Dokumentálás](guides/dokumentacios-utmutato.md) · **Roadmap** · [Hozzájárulás](../CONTRIBUTING.md)

Ez a dokumentum összefoglalja az OpenSchool platform teljes vízióját, és felméri, mi van készen, mi hiányzik, és mi a tervezett fejlesztési irány.

---

## Az OpenSchool elve

Az OpenSchool nem egy hagyományos e-learning platform. A diákok **ugyanazokkal az eszközökkel dolgoznak, amelyeket az iparban is használnak**: GitHub, Discord, VS Code, Docker, pytest, CI/CD. A cél nem az, hogy egy feladatbeadó rendszert tanuljanak meg, hanem hogy **a munkafolyamat maga legyen a tananyag része**.

| Iskolai verzió | Ipari megfelelő |
|----------------|-----------------|
| GitHub repóba pushol | Verziókezelés, commit kultúra |
| GitHub Actions futtatja a teszteket | CI pipeline, zöld build = kész |
| Discord szálakban kérdez | Csapatkommunikáció |
| VS Code + terminál | Ipari fejlesztőkörnyezet |
| Docker + PostgreSQL | Konténerizált fejlesztés |
| pytest / shell tesztek | Tesztvezérelt gondolkodás |

---

## Kurzus beállítása

Egy új kurzus indításához a GitHub Classroom-ban és az OpenSchool admin panelen is konfigurálni kell. A teljes lépésről lépésre útmutatót lásd: **[GitHub Classroom integráció](integrations/github-classroom-integraciot.md)**.

---

## Aktuális állapot (ami kész van)

### ✅ Backend API — teljes

| Funkció | Végpont | Állapot |
|---------|---------|---------|
| GitHub OAuth bejelentkezés | `/api/auth/login`, `/callback` | ✅ Működik |
| JWT tokenek (access + refresh) | `/api/auth/me`, `/refresh`, `/logout` | ✅ Működik |
| Szerepkör-alapú hozzáférés | `student`, `mentor`, `admin` | ✅ Működik |
| Kurzus CRUD (admin) | `/api/courses` POST/PUT | ✅ Működik |
| Modul és gyakorlat kezelés | `/api/courses/{id}/modules/...` | ✅ Működik |
| Beiratkozás | `/api/courses/{id}/enroll` | ✅ Működik |
| Haladás követés | `/api/me/dashboard`, `/api/me/courses/{id}/progress` | ✅ Működik |
| GitHub CI állapot ellenőrzés | `services/github.py` | ✅ Implementálva |
| Tanúsítvány igénylés | `/api/me/courses/{id}/certificate` | ✅ Működik |
| PDF generálás QR kóddal | `services/pdf.py` (fpdf2, vektor QR) | ✅ Működik |
| Tanúsítvány hitelesítés | `/api/verify/{cert_id}` | ✅ Működik |
| Dinamikus BASE_URL | Környezeti változóból | ✅ Működik |
| GitHub Classroom integráció | `classroom_url`, webhook, sync | ✅ Működik |
| Admin panel API | `/api/admin/*` — statisztikák, felhasználók, törlés | ✅ Működik |

### ✅ Frontend — alapvető oldalak

| Oldal | Útvonal | Állapot |
|-------|---------|---------|
| Kezdőoldal | `/` | ✅ Kész |
| Kurzuslista | `/courses` | ✅ Kész |
| Kurzus részletek | `/courses/[slug]` | ✅ Kész |
| Bejelentkezés | `/login` | ✅ Kész |
| Dashboard | `/dashboard` | ✅ Kész |
| Tanúsítvány hitelesítés | `/verify/[id]` | ✅ Kész |
| Admin dashboard | `/admin` | ✅ Kész |
| Admin felhasználók | `/admin/users` | ✅ Kész |
| Admin kurzusok | `/admin/courses` | ✅ Kész |

### ✅ Infrastruktúra

| Elem | Állapot |
|------|---------|
| Docker Compose (fejlesztés) | ✅ 4 szolgáltatás (backend, db, nginx, frontend) |
| Docker Compose (éles) | ✅ restart, healthcheck, log rotáció |
| nginx reverse proxy | ✅ API proxy + statikus fájlok |
| Alembic migrációk | ✅ 4 migráció |
| GitHub Actions CI | ✅ pytest minden push-ra |
| GitHub Actions CD | ✅ SSH deploy (secrets konfigurálandó) |
| Biztonsági mentés szkript | ✅ pg_dump + 30 napos retenciő |
| Automatizált karbantartás | ✅ maintenance.sh (backup, health, disk, SSL, audit) |
| VPS bootstrap szkript | ✅ bootstrap-vps.sh (teljes szerver felállítás) |
| Cron job telepítő | ✅ setup-cron.sh (napi/heti/havi ütemezés) |
| Biztonsági audit szkript | ✅ security-check.sh |
| Discord CI/CD értesítések | ✅ discord-notify.sh + GitHub Actions |
| Discord ops monitoring | ✅ maintenance.sh webhook értesítések |

### ✅ Közösség és dokumentáció

| Elem | Állapot |
|------|---------|
| MIT licensz | ✅ |
| CONTRIBUTING.md (magyar) | ✅ |
| Issue sablonok (bug, feature, documentation, question) | ✅ |
| PR sablon | ✅ |
| README.md | ✅ |
| Makefile | ✅ |
| pre-commit + ruff | ✅ |
| Architektúra dokumentáció | ✅ |
| Telepítési útmutató | ✅ |
| Fejlesztői útmutató (közös) | ✅ |
| Backend fejlesztői útmutató | ✅ |
| Frontend fejlesztői útmutató | ✅ |
| Felhasználói útmutató (UI/domain) | ✅ |
| GitHub Classroom integrációs útmutató | ✅ |
| Karbantartási útmutató | ✅ |
| Automatizálás beállítási útmutató | ✅ |
| Discord integrációs útmutató | ✅ |
| Dokumentálási útmutató | ✅ |
| API referencia | ✅ |
| Adatbázis séma dokumentáció | ✅ |
| Tesztelési útmutató | ✅ |
| Környezeti változók referencia | ✅ |
| Dokumentumok közötti navigáció (18 doc) | ✅ |
### ✅ Tesztek

| Teszt | Állapot |
|-------|---------|
| Auth tesztek (8 teszt) | ✅ |
| Kurzus tesztek (14 teszt) | ✅ |
| Tanúsítvány tesztek (12 teszt) | ✅ |
| GitHub Classroom tesztek (9 teszt) | ✅ |
| Admin tesztek (11 teszt) | ✅ |
| Health check teszt | ✅ |
| Egyéb tesztek | ✅ |
| **Összesen: 56 teszt** | ✅ Mind zöld |

---

## Megvalósított és tervezett fejlesztések

### ✅ GitHub Classroom integráció

A kurzuskeretrendszer lényege, hogy a diákok GitHub Classroom-on keresztül adják be a feladataikat, és a platform ezt tükrözi.

**Implementált funkciók:**

- [x] GitHub Classroom assignment linkek tárolása az `Exercise` modellben (`classroom_url`)
- [x] Automatikus haladás frissítés a GitHub API-ból
- [x] Webhook fogadás GitHub-ból (push eseményekre) a haladás valós idejű frissítéséhez
- [x] Tanári nézet: diákok haladásának összeszítése kurzusonként
- [ ] GitHub Classroom CSV import a jegyekhez

**Miért fontos:** Ez a platform alapvető értékajánlata — a diákok valódi GitHub repókban dolgoznak, és a platform automatikusan követi a haladásukat.

### ✅ Admin panel

Az admin felhasználók számára dedikált kezelőfelület a platform adminisztrációjához.

**Implementált funkciók:**

- [x] Admin dashboard statisztikákkal (felhasználók, kurzusok, beiratkozások, tanúsítványok, gyakorlatok)
- [x] Felhasználók listázása és szerepkör módosítása
- [x] Kurzusok, modulok, gyakorlatok létrehozása és törlése
- [x] Szerepkör-alapú hozzáférésvédelem (csak admin)
- [x] 11 teszt az admin végpontokhoz

### � 1. fázis — Discord integráció

A kurzuskeretrendszer Discord szervert használ a kommunikációhoz, heti szálakkal és automatikus értesítésekkel.

**Kész:**

- [x] Discord webhook URL-ek tárolása a konfigurációban (VPS: `/etc/openschool-maintenance.conf`, GitHub: `DISCORD_WEBHOOK_CI` secret)
- [x] CI/CD Discord értesítések (GitHub Actions → Discord embed üzenetek: siker/hiba/megszakítva)
- [x] Ops monitoring Discord értesítések (backup hiba, health check, lemezhasználat, SSL lejárat)
- [x] Discord szerver felállítási útmutató ([discord-integracio.md](integrations/discord-integracio.md))
- [x] Csatornastruktúra ajánlás (kurzusonként bővíthető)
- [x] Discord CI/CD notify szkript (`scripts/discord-notify.sh`)

**Még tervezett:**

- [ ] Platform → Discord értesítések:
  - Új beiratkozás egy kurzusra
  - Tanúsítvány kiállítás
  - Új kurzus létrehozása
- [ ] Discord OAuth integráció (opcionális, a GitHub mellett)
- [ ] Discord szerver meghívó link a felületen
- [ ] Közlemények kezelése a platformon belül (admin felület)

### 🟠 2. fázis — Tanári eszközök

- [ ] Tanári dashboard: összes diák haladása egy helyen
- [ ] GitHub Classroom eredmények megjelenítése
- [ ] Házi feladatok határidejének kezelése
- [ ] Exportálás: haladás CSV-be

### 🟠 3. fázis — Haladó funkciók

- [ ] Pull Request alapú beadás (branch-elés, review)
- [ ] GitHub Issues használata feladatkezeléshez
- [ ] Projekt board (GitHub Projects) integráció
- [ ] Csapatmunka támogatás (közös repók, konfliktuskezelés)
- [ ] Értesítési rendszer (email vagy push notification)

### 🟢 4. fázis — Platform érettség

- [ ] Reszponzív design finomhangolás (mobil, tablet, desktop)
- [ ] Sötét mód
- [ ] Teljesítmény optimalizálás (cacheelés, lazy loading)
- [ ] Monitoring és riasztások (Sentry, Prometheus, stb.)
- [ ] Analitika dashboard (tanár számára: ki mennyit dolgozik, mikor)
- [ ] Többnyelvűség (ha más iskolák is használnák)
- [ ] API dokumentáció (Swagger UI) publikus hozzáférése

---

## Külső eszközök integrációja

A platform fejlesztése során a következő külső eszközök integrálása tervezett:

| Eszköz | Leírás | Állapot |
|--------|--------|--------|
| GitHub Classroom | Feladatkiadás és autograding | ✅ Webhook + repo_prefix + sync |
| Discord értesítések (CI/CD + ops) | CI/CD és VPS monitoring értesítések | ✅ Működik |
| Discord értesítések (platform) | Platform → Discord (beiratkozás, tanúsítvány) | 🔴 Tervezett |

---

## Prioritási sorrend

1. **VPS telepítés** (az éles rendszer felállítása a saját domainnel — automatizáló szkriptek készen: `bootstrap-vps.sh`, `provision.sh`) ← **KÖVETKEZŐ LÉPÉS**
2. **Discord integráció** — platform → Discord értesítések (CI/CD + ops monitoring már kész)
3. **Tanári eszközök** — haladás összeszítés, automatikus assignment szinkronizálás
4. **Haladó funkciók** — PR-ek, Issues, csapatmunka
5. **Platform érettség** — monitoring, analitika, teljesítmény

---

## Összefoglalás

A platform alapjai **készen állnak**: backend API (auth, kurzusok, haladás, tanúsítványok, admin), frontend (9 oldal), infrastruktúra (Docker, CI/CD, nginx, automatizált karbantartás, Discord CI/CD értesítések), GitHub Classroom integráció (repo_prefix, webhook, sync), admin panel, és 16 dokumentum navigációval összekötve.

Az automatizáció szintén kész: VPS bootstrap szkript, cron job-ok, biztonsági audit, ops monitoring Discord értesítésekkel. A következő nagy lépés a **VPS telepítés** (a szkriptek készen állnak), majd a **platform → Discord értesítések** és **tanári eszközök bővítése** (automatikus Classroom szinkronizálás, tanári dashboard), amelyek a platform valódi értékét tovább növelik.
