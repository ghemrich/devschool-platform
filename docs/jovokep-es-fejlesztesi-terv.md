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

## A növekedési modell — Diákból mentor, mentorból fejlesztő

Az OpenSchool hosszú távú víziója egy **önfenntartó közösség**: a diákok, akik elvégzik a kurzusokat, nem csak tanúsítványt kapnak — **lehetőséget kapnak a platform fejlesztésében és az oktatásban való részvételre**.

Ez a modell három szintet tartalmaz:

| Szint | Ki? | Hogyan kerül ide? | Mit csinálhat? |
|-------|-----|-------------------|----------------|
| **Diák** | Bárki, aki regisztrál | GitHub OAuth bejelentkezés | Kurzusok elvégzése, tanúsítvány igénylése |
| **Mentor** | Tanúsítvánnyal rendelkező diák | Automatikus előléptetés meghatározott tanúsítványok alapján | Diákok haladásának követése, visszajelzés, mentorálás |
| **Platform fejlesztő** | Tapasztalt mentor | "Platform Development" kurzus elvégzése | Kurzusok létrehozása, platform fejlesztés, code review |

### Miért működik?

- A **tanúsítványok már bizonyítják a kompetenciát** — nem szubjektív döntés, hanem automatikus
- A diákok valódi eszközökkel dolgoznak (GitHub, CI, PR-ek) — **pontosan azokkal, amikkel a platformot is fejlesztjük**
- Az új mentorok motiváltak, mert éppen most végezték el a kurzust — **friss tapasztalattal rendelkeznek**
- A platform fejlesztése maga is tananyag — **hozzájárulás = tanulás**

### Automatikus előléptetés logikája

```
Diák elvégzi a kurzusokat → Tanúsítvány(ok) kiállítása
       ↓
Promotion szabály ellenőrzés (pl. "Python Haladó" + "Mentor Képzés" tanúsítványok)
       ↓
Automatikus szerepkör váltás: student → mentor
       ↓
Discord értesítés + privát csatorna hozzáférés
       ↓
Mentor dashboard megnyitása
```

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

### 🟠 2. fázis — Automatikus mentor és fejlesztő pipeline

A platform növekedési motorja: tanúsítvány-alapú automatikus előléptetés és mentor onboarding.

**Előléptetési rendszer:**

- [ ] Promotion szabályok adatmodell: tanúsítvány-kombinációk → célszerepkör (pl. "Python Haladó" + "Mentor Képzés" → `mentor`)
- [ ] Automatikus szerepkör-váltás tanúsítvány kiállításakor (szabály-motor a certificate service-ben)
- [ ] Discord értesítés előléptetéskor (pl. "🎓 @username mentorrá vált!")
- [ ] Discord szerepkör szinkronizáció (platform szerepkör → Discord role)

**Mentor onboarding kurzus:**

- [ ] "Legyél mentor!" meta-kurzus létrehozása — a platform használatáról, kódbázisról, mentori eszközökről
- [ ] Meta-kurzus gyakorlatai szintén GitHub Classroom-mal értékelve (ugyanaz az infra)
- [ ] Kurzus elvégzése → automatikus `mentor` szerepkör

**Platform fejlesztő track:**

- [ ] "Platform Development" kurzus, ahol a gyakorlatok = valódi platform hozzájárulások
  - Gyakorlat 1: `good-first-issue` javítása a platform repóban
  - Gyakorlat 2: Teszt hozzáadása a platform tesztcsomaghoz
  - Gyakorlat 3: Új gyakorlat létrehozása egy meglévő kurzushoz
  - Gyakorlat 4: Dokumentáció írása
- [ ] CI-alapú értékelés a platform repóban (PR merge = completed)
- [ ] Elvégzett fejlesztők automatikus meghívása a GitHub org teambe
- [ ] `teacher` szerepkör bevezetése (kurzus létrehozási jogosultsággal)

**Mentor dashboard:**

- [ ] Mentorált diákok listája és haladásuk
- [ ] Visszajelzés lehetőség (kommentek a haladáshoz)
- [ ] Kurzus létrehozási felület (mentor/teacher jogosultsággal)
- [ ] Publikus "Közreműködők" oldal a tanúsított fejlesztőkkel

### 🟠 3. fázis — Tanári eszközök

- [ ] Tanári dashboard: összes diák haladása egy helyen
- [ ] GitHub Classroom eredmények megjelenítése
- [ ] Házi feladatok határidejének kezelése
- [ ] Exportálás: haladás CSV-be

### 🟠 4. fázis — Haladó funkciók

- [ ] Pull Request alapú beadás (branch-elés, review)
- [ ] GitHub Issues használata feladatkezeléshez
- [ ] Projekt board (GitHub Projects) integráció
- [ ] Csapatmunka támogatás (közös repók, konfliktuskezelés)
- [ ] Értesítési rendszer (email vagy push notification)

### 🟢 5. fázis — Platform érettség

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
| Automatikus előléptetés | Tanúsítvány-alapú szerepkör váltás | 🔴 Tervezett |
| GitHub org team meghívás | Fejlesztők automatikus meghívása | 🔴 Tervezett |
| Discord szerepkör szinkronizáció | Platform → Discord role szinkron | 🔴 Tervezett |

---

## Prioritási sorrend

1. ~~**VPS telepítés**~~ ✅ — éles rendszer felállítva
2. ~~**Discord szerver**~~ ✅ — szerver létrehozva ([discord.gg/BrKd45S6](https://discord.gg/BrKd45S6)), CI/CD + ops monitoring értesítések működnek
3. **Discord platform értesítések** — platform → Discord értesítések (beiratkozás, tanúsítvány) ← **KÖVETKEZŐ LÉPÉS**
4. **Automatikus mentor pipeline** — előléptetési szabályok, mentor kurzus, mentor dashboard
5. **Tanári eszközök** — haladás összesítés, Classroom szinkronizálás
6. **Platform fejlesztő track** — meta-kurzus valódi platform hozzájárulásokkal
7. **Haladó funkciók** — PR-ek, Issues, csapatmunka
8. **Platform érettség** — monitoring, analitika, teljesítmény

---

## Összefoglalás

A platform alapjai **készen állnak**: backend API (auth, kurzusok, haladás, tanúsítványok, admin), frontend (9 oldal), infrastruktúra (Docker, CI/CD, nginx, automatizált karbantartás, Discord CI/CD értesítések), GitHub Classroom integráció (repo_prefix, webhook, sync), admin panel, és átfogó dokumentáció. A **VPS éles rendszer felállítva**, a **Discord szerver működik** ([discord.gg/BrKd45S6](https://discord.gg/BrKd45S6)).

A hosszú távú vízió egy **önfenntartó közösség** kiépítése: a diákok tanúsítványok megszerzésével automatikusan mentorrá válhatnak, majd a platform fejlesztésébe is bekapcsolódhatnak. Ez a modell lehetővé teszi, hogy a platform organikusan növekedjen — minden új mentor egyben új tanár és potenciális fejlesztő is.

A következő lépések: **Discord platform értesítések** (beiratkozás, tanúsítvány), majd az **automatikus mentor pipeline** kiépítése (előléptetési szabályok, meta-kurzusok, mentor dashboard). Az automatizáció infrastruktúrája (CI, webhook, tanúsítványok) már készen áll — a pipeline erre épít.
