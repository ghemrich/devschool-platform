# OpenSchool Platform — Jövőkép és fejlesztési terv

> 📖 **Dokumentáció:** [Főoldal](../README.md) · [Architektúra](architektura.md) · [Telepítés](telepitesi-utmutato.md) · [Fejlesztői környezet](fejlesztoi-kornyezet.md) · **Roadmap** · [Felhasználói útmutató](felhasznaloi-utmutato.md) · [GitHub Classroom](github-classroom-integraciot.md) · [Hozzájárulás](../CONTRIBUTING.md)

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

## Kurzus beállítása lépésről lépésre

Egy új kurzus indításához mindkét rendszerben (GitHub Classroom + OpenSchool) kell dolgozni. A részletes technikai útmutatót lásd: [GitHub Classroom integráció](github-classroom-integraciot.md).

### 1. GitHub szervezet és Classroom előkészítése

1. Hozz létre egy **GitHub Organization**-t (ha még nincs), pl. `openschool-org`
2. A <https://classroom.github.com> oldalon kapcsold össze a szervezettel
3. Állítsd be a `.env` fájlban: `GITHUB_ORG=openschool-org`

### 2. Kurzus létrehozása az OpenSchool-ban

1. **Admin panel** → **Kurzusok** (`/admin/courses`)
2. Add meg a kurzus nevét és leírását → **Létrehozás**
3. A kurzus kártyáján kattints a **Részletek** gombra
4. Add hozzá a **modulokat** (pl. „1. Alapok", „2. Haladó")

### 3. Feladatok létrehozása (mindkét helyen)

Minden feladathoz két lépés kell:

| Hol | Mit csinálj |
|-----|-------------|
| **GitHub Classroom** | Hozz létre egy Assignment-et egy template repóval, amelyben van `.github/workflows/` CI teszt. Jegyezd meg a **repository prefix**-et (pl. `python-hello-world`) és a **meghívó linket**. |
| **OpenSchool admin** | A modul alatt add hozzá a feladatot: **Feladat neve** + **Repo prefix** (pontosan ugyanaz mint a Classroom-ban) + **Classroom link** (a meghívó URL) |

### 4. Webhook beállítása (opcionális)

Ha azt szeretnéd, hogy a haladás automatikusan frissüljön (ne kelljen a tanulónak a „Szinkronizálás" gombot nyomni):

1. GitHub org beállítások → Webhooks → **Add webhook**
2. URL: `https://{domain}/api/webhooks/github`
3. Esemény: **Workflow runs**
4. Secret: ugyanaz mint `GITHUB_WEBHOOK_SECRET` a `.env`-ben

### 5. Tanulók tájékoztatása

A tanulóknak a következőket kell tenniük:
1. Belépés az OpenSchool-ba GitHub fiókkal
2. Beiratkozás a kurzusra
3. A feladatok mellett a 📎 ikonra kattintva elfogadják a GitHub Classroom assignment-et
4. Megoldják a feladatot, push-olnak → CI fut → haladás frissül

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

### ✅ Közösség és dokumentáció

| Elem | Állapot |
|------|---------|
| MIT licensz | ✅ |
| CONTRIBUTING.md (magyar) | ✅ |
| Issue sablonok (bug, feature) | ✅ |
| PR sablon | ✅ |
| README.md | ✅ |
| Makefile | ✅ |
| pre-commit + ruff | ✅ || Architektúra dokumentáció | ✅ |
| Telepítési útmutató | ✅ |
| Fejlesztői környezet útmutató | ✅ |
| Felhasználói útmutató (UI/domain) | ✅ |
| GitHub Classroom integrációs útmutató | ✅ |
| Dokumentumok közötti navigáció | ✅ |
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

### 🔴 1. fázis — Discord integráció

A kurzuskeretrendszer Discord szervert használ a kommunikációhoz, heti szálakkal és automatikus értesítésekkel.

**Szükséges fejlesztések:**

- [ ] Discord webhook URL-ek tárolása a konfigurációban
- [ ] Platform → Discord értesítések:
  - Új beiratkozás egy kurzusra
  - Tanúsítvány kiállítás
  - Új kurzus létrehozása
- [ ] Discord OAuth integráció (opcionális, a GitHub mellett)
- [ ] Discord szerver meghívó link a felületen
- [ ] Közlemények kezelése a platformon belül (admin felület)

**Csatorna struktúra a kurzuskeretrendszerből:**

```
📋 INFORMÁCIÓK
  #szabályzat
  #közlemények
  #hasznos-linkek

🐍 PYTHON 10
  #python10-általános
  #python10-segítség (heti szálak)
  #python10-megoldások

⚡ BACKEND 13
  #backend13-általános
  #backend13-segítség (heti szálak)
  #backend13-megoldások

💬 KÖZÖSSÉG
  #általános
```

### 🟠 2. fázis — Tanári eszközök

- [ ] Tanári dashboard: összes diák haladása egy helyen
- [ ] Jegykalkulátor integráció (jelenleg CLI szkript: `jegy-szamolo.py`)
- [ ] GitHub Classroom eredmények megjelenítése
- [ ] Házi feladatok határidejének kezelése
- [ ] Exportálás: jegyek CSV-be

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

A kurzuskeretrendszer (`../testing/`) több külső eszközt tartalmaz, amelyek jelenleg CLI szkriptként működnek:

| Eszköz | Leírás | Integráció módja |
|--------|--------|------------------|
| `github-setup.sh` | Template repók létrehozása GitHub Organization-ben | Marad CLI — egyszeri beállítás |
| `discord-webhook.py` | Discord értesítések küldése | Platform beépített funkció lesz |
| `jegy-szamolo.py` | Félév végi jegy kiszámítása CSV-kből | Platform beépített funkció lesz |
| GitHub Classroom | Feladatkiadás és autograding | Webhook + API integráció |

---

## Prioritási sorrend

1. **VPS telepítés** (az éles rendszer felállítása a saját domainnel) ← **KÖVETKEZŐ LÉPÉS**
2. **Discord integráció** — a közösségi kommunikáció
3. **Tanári eszközök** — jegykalkulátor, haladás összeszítés, automatikus assignment szinkronizálás
4. **Haladó funkciók** — PR-ek, Issues, csapatmunka
5. **Platform érettség** — monitoring, analitika, teljesítmény

---

## Összefoglalás

A platform alapjai **készen állnak**: backend API (auth, kurzusok, haladás, tanúsítványok, admin), frontend (9 oldal), infrastruktúra (Docker, CI/CD, nginx), GitHub Classroom integráció (repo_prefix, webhook, sync), admin panel, és 7 dokumentum navigációval összekötve.

A következő nagy lépés a **VPS telepítés**, majd a **Discord integráció** és **tanári eszközök bővítése** (automatikus Classroom szinkronizálás, jegykalkulátor), amelyek a platform valódi értékét tovább növelik.
