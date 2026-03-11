# Frontend fejlesztés (Astro)

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](fejlesztoi-utmutato.md) · [Backend](backend-fejlesztes.md) · **Frontend** · [Tesztelés](tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a frontend fejlesztéséhez tartalmaz mindent: Astro projekt felépítés, oldalak, komponensek, kliens oldali JavaScript, stílusok és a backend API-val való kommunikáció.

> **Általános fejlesztői útmutató** (Docker, pre-commit, VS Code, Git, CI/CD, Makefile): [fejlesztoi-utmutato.md](fejlesztoi-utmutato.md)
> **Dokumentálási útmutató** (docstring-ek, API docs, README karbantartás): [dokumentacios-utmutato.md](../guides/dokumentacios-utmutato.md)

---

## 1. Telepítés és indítás

```bash
cd frontend
npm install
```

### Fejlesztői szerver

```bash
npm run dev     # Astro dev szerver: http://localhost:4321
```

A dev szerver hot reload-dal működik — a fájl módosítások automatikusan megjelennek a böngészőben.

> **Fontos:** A dev szerver önmagában nem tud API hívásokat kiszolgálni. A teljes fejlesztéshez a Docker Compose-zal kell futtatni az egész stacket (`make up`), ami az nginx-en keresztül összekötni a frontendet a backenddel.

### Build

```bash
npm run build    # Statikus fájlok generálása → dist/
npm run preview  # Build kimenet előnézete: http://localhost:4321
```

Az Astro statikus HTML/CSS/JS fájlokat generál. A build kimenetet az nginx szolgálja ki. A böngészőből érkező `/api/*` hívásokat az nginx a FastAPI backend-re proxyzi.

---

## 2. Könyvtárstruktúra

```
frontend/
├── astro.config.mjs       # Astro konfiguráció (output: static, port: 4321)
├── package.json           # Node.js függőségek (astro ^5.0.0)
├── tsconfig.json          # TypeScript konfig (strict mód)
│
├── public/                # Statikus fájlok (favicon, képek — változtatás nélkül másolódnak)
│
└── src/
    ├── env.d.ts           # Astro típus deklarációk
    │
    ├── styles/
    │   └── global.css     # Globális stílusok (CSS változók, card, btn, progress-bar)
    │
    ├── layouts/
    │   └── Layout.astro   # Fő layout — header, footer, auth navigáció, hamburger menü
    │
    ├── components/
    │   ├── CourseCard.astro   # Kurzus kártya (név, leírás, link)
    │   ├── Footer.astro       # Lábléc (copyright)
    │   ├── Header.astro       # Fejléc (logo, navigáció, hamburger)
    │   └── ProgressBar.astro  # Haladási sáv (percent, label)
    │
    ├── lib/
    │   ├── api.js             # API wrapper — token kezelés, auto-refresh
    │   ├── dashboard.js       # Dashboard logika — kurzusok, tanúsítványok, sync
    │   └── course-detail.js   # Kurzus részletek — modulok, beiratkozás
    │
    └── pages/
        ├── index.astro        # Kezdőoldal
        ├── login.astro        # Belépés (GitHub OAuth)
        ├── dashboard.astro    # Dashboard (haladás, tanúsítványok)
        ├── courses/
        │   ├── index.astro    # Kurzuslista
        │   └── [slug].astro   # Kurzus részletei
        ├── verify/
        │   └── [id].astro     # Tanúsítvány publikus verifikáció
        └── admin/
            ├── index.astro    # Admin dashboard (statisztikák)
            ├── users.astro    # Felhasználók kezelése (tábla, szerepkörök)
            └── courses.astro  # Kurzusok kezelése (CRUD, modulok, feladatok)
```

---

## 3. Astro konfiguráció

```javascript
// astro.config.mjs
export default defineConfig({
  output: 'static',           // Statikus HTML generálás (nincs SSR)
  server: { port: 4321 },     // Dev szerver portja
  build: { format: 'directory' }, // /courses/index.html (nem /courses.html)
});
```

### Fontos tudnivalók

- **Nincs SSR** — az Astro statikus fájlokat generál build időben
- **Dinamikus útvonalak** (`[slug].astro`, `[id].astro`) a `getStaticPaths()` függvényt használják. Jelenleg placeholder értékkel térnek vissza, mert az adatok kliens oldalon töltődnek be
- **TypeScript** — strict mód engedélyezve, de a legtöbb kliens oldali kód vanilla JS

---

## 4. Layout és komponensek

### Layout (`Layout.astro`)

Minden oldal a `Layout` komponenst használja, ami biztosítja:

- **HTML head** — charset, viewport, favicon, `<title>`
- **Header** — logo, navigáció (Kurzusok, Dashboard), auth állapot
- **Footer** — copyright
- **Hamburger menü** — mobil nézetben

Az auth navigáció dinamikus: a layout `<script>` blokkja ellenőrzi a `localStorage` tokent, és ha van, lekérdezi a `/api/auth/me` végpontot a szerepkör megállapításához. Admin felhasználóknál megjelenik az „Admin" link.

```astro
<!-- Használat egy oldalban -->
---
import Layout from '../layouts/Layout.astro';
---
<Layout title="Oldal neve">
  <div class="container page">
    <!-- tartalom -->
  </div>
</Layout>
```

### Komponensek

| Komponens | Props | Használat |
|-----------|-------|-----------|
| `CourseCard` | `name`, `description`, `id` | Kurzus kártya a listában |
| `ProgressBar` | `percent`, `label?` | Haladási sáv százalékkal |
| `Header` | — | Fejléc navigációval |
| `Footer` | — | Lábléc |

> **Megjegyzés:** A `Header` és `Footer` komponensek jelenleg közvetlenül a `Layout.astro`-ba vannak beépítve (nem importálva). A különálló `Header.astro` és `Footer.astro` fájlok egyszerűsített változatot tartalmaznak.

---

## 5. Oldalak

### Publikus oldalak

| Oldal | Fájl | Leírás |
|-------|------|--------|
| Kezdőoldal | `pages/index.astro` | Hero szekció, „Hogyan működik?" lépések, kurzus előnézet |
| Kurzuslista | `pages/courses/index.astro` | Összes kurzus kártya nézetben |
| Kurzus részletek | `pages/courses/[slug].astro` | Modulok, feladatok, beiratkozás gomb, Classroom linkek |
| Belépés | `pages/login.astro` | GitHub OAuth gomb, token kezelés URL fragment-ből |
| Verifikáció | `pages/verify/[id].astro` | Tanúsítvány publikus hitelesítés |

### Védett oldalak (bejelentkezés szükséges)

| Oldal | Fájl | Leírás |
|-------|------|--------|
| Dashboard | `pages/dashboard.astro` | Beiratkozott kurzusok, haladási sávok, tanúsítvány kezelés, GitHub sync |
| Admin dashboard | `pages/admin/index.astro` | Statisztikák (felhasználók, kurzusok, beiratkozások, stb.) |
| Admin felhasználók | `pages/admin/users.astro` | Felhasználók táblázata, szerepkör módosítás |
| Admin kurzusok | `pages/admin/courses.astro` | Kurzus CRUD, modul/feladat hozzáadás/törlés |

---

## 6. Kliens oldali JavaScript

Mivel az Astro statikus HTML-t generál, az interaktív funkciók kliens oldali JavaScript-tel működnek. A fő JS modulok a `src/lib/` mappában vannak.

### `api.js` — API wrapper

Az `apiFetch()` függvény kezeli az autentikációt:

1. Hozzáadja a `Bearer` tokent a kéréshez a `localStorage`-ból
2. Ha a válasz `401`, megpróbálja frissíteni a tokent a `/api/auth/refresh` végponton
3. Ha a refresh is sikertelen, átirányít a `/login` oldalra

```javascript
import { apiFetch } from '../lib/api.js';

const res = await apiFetch('/api/me/dashboard');
const data = await res.json();
```

### `dashboard.js` — Dashboard logika

A dashboard oldal teljes kliens oldali logikája:

- Betölti a haladást (`/api/me/dashboard`) és a tanúsítványokat (`/api/me/certificates`)
- Megjeleníti a kurzusokat haladási sávokkal
- **Tanúsítvány igénylés** — ha a kurzus 100%-os, megjelenik az „Igénylés" gomb (`POST /api/me/courses/{id}/certificate`)
- **PDF letöltés** — meglévő tanúsítványhoz Blob-ként letölti a PDF-et (`GET /api/me/certificates/{id}/pdf`)
- **GitHub szinkronizálás** — a „🔄 Haladás szinkronizálása GitHub-ból" gomb hívja a `POST /api/me/sync-progress` végpontot

### `course-detail.js` — Kurzus részletek

- Az URL-ből kiszedi a kurzus ID-t (slug)
- Betölti a kurzus adatait (`GET /api/courses/{id}`)
- Megjeleníti a modulokat és feladatokat, GitHub Classroom linkekkel (📎 ikon)
- Beiratkozás gomb kezelése (`POST /api/courses/{id}/enroll`)

---

## 7. Autentikáció

### Token kezelés

A frontend `localStorage`-ban tárolja az access tokent:

```javascript
// Token mentése (login.astro — OAuth callback után)
const hash = window.location.hash.substring(1);
const params = new URLSearchParams(hash);
const token = params.get('token');
localStorage.setItem('access_token', token);

// Token használata API hívásoknál
const headers = { Authorization: `Bearer ${token}` };

// Kijelentkezés
localStorage.removeItem('access_token');
```

### Auth flow

1. Felhasználó kattint a „Belépés GitHub-bal" gombra → `/api/auth/login`
2. Backend átirányít a GitHub OAuth oldalra
3. GitHub visszairányít → `/api/auth/callback?code=xxx`
4. Backend JWT-t generál, átirányít → `/login#token=eyJ...`
5. A `login.astro` script kiszedi a tokent a URL fragment-ből és elmenti

### Védett oldalak

A védett oldalak (dashboard, admin) kliens oldalon ellenőrzik a tokent:

```javascript
const token = localStorage.getItem('access_token');
if (!token) {
  window.location.href = '/login';
}
```

Az admin oldalak ezen felül a `/api/auth/me` végponton ellenőrzik a szerepkört:

```javascript
const me = await meRes.json();
if (me.role !== 'admin') {
  container.innerHTML = '<p>Nincs jogosultságod.</p>';
  return;
}
```

---

## 8. Stílusok (CSS)

### CSS változók (`global.css`)

```css
:root {
  --color-primary: #2c3e50;     /* Sötétkék — header, gombok */
  --color-accent: #e74c3c;      /* Piros — elsődleges gombok, kiemelés */
  --color-bg: #f8f9fa;          /* Világosszürke háttér */
  --color-text: #333;           /* Szöveges tartalom */
  --color-text-light: #7f8c8d;  /* Másodlagos szöveg */
  --color-border: #dee2e6;      /* Keretek, elválasztók */
  --color-white: #fff;          /* Fehér */
  --color-success: #27ae60;     /* Zöld — haladási sáv, sikeres műveletek */
  --max-width: 1200px;          /* Tartalom maximális szélessége */
}
```

### Globális osztályok

| Osztály | Leírás |
|---------|--------|
| `.container` | Tartalom centrálása `max-width: 1200px`-szel |
| `.btn` | Gomb alap stílus (padding, border-radius, transition) |
| `.btn-primary` | Piros gomb (accent szín) |
| `.btn-secondary` | Sötétkék gomb (primary szín) |
| `.card` | Fehér kártya árnyékkal |
| `.card-grid` | Reszponzív grid kártyákhoz (`auto-fill, minmax(300px, 1fr)`) |
| `.progress-bar` | Haladási sáv konténer |
| `.progress-bar-fill` | Haladási sáv kitöltés (zöld, animált szélesség) |

### Stílus konvenciók

- **Scoped stílusok** — az oldalak és komponensek `<style>` blokkjai automatikusan scope-oltak (Astro alapértelmezés)
- **Globális stílusok** — a `global.css`-t a `Layout.astro` importálja
- **Nincs CSS framework** — vanilla CSS, CSS változókkal
- **Reszponzív** — `@media (max-width: 767px)` törésponttal

---

## 9. Admin panel

Az admin panel 3 oldalból áll, mindegyik kliens oldalon ellenőrzi az admin szerepkört.

### Admin navigáció

Minden admin oldal tartalmaz egy belső navigációs sávot:

```html
<div class="admin-nav">
  <a href="/admin" class="btn btn-primary">Áttekintés</a>
  <a href="/admin/users" class="btn btn-secondary">Felhasználók</a>
  <a href="/admin/courses" class="btn btn-secondary">Kurzusok</a>
</div>
```

### Admin — Áttekintés (`admin/index.astro`)

- Statisztikák: felhasználók, kurzusok, beiratkozások, tanúsítványok, feladatok
- API: `GET /api/admin/stats`

### Admin — Felhasználók (`admin/users.astro`)

- Táblázat: avatar, felhasználónév, email, szerepkör, regisztráció, utolsó belépés
- Szerepkör módosítás: `<select>` dropdown → „Mentés" gomb (csak megváltozott soroknál)
- API: `GET /api/admin/users`, `PATCH /api/admin/users/{id}/role`

### Admin — Kurzusok (`admin/courses.astro`)

Legösszetettebb oldal — kurzusok, modulok és feladatok teljes CRUD kezelése:

- **Kurzus létrehozása** — űrlap (név, leírás) → `POST /api/courses`
- **Kurzus törlése** — megerősítés ablak → `DELETE /api/admin/courses/{id}`
- **Részletek lenyitása** — modulok és feladatok betöltése → `GET /api/courses/{id}`
- **Modul hozzáadása** — űrlap (név, sorrend) → `POST /api/courses/{id}/modules`
- **Modul törlése** → `DELETE /api/admin/modules/{id}`
- **Feladat hozzáadása** — űrlap (név, repo prefix, classroom URL, sorrend) → `POST /api/courses/{id}/modules/{mid}/exercises`
- **Feladat törlése** → `DELETE /api/admin/exercises/{id}`

---

## 10. Új oldal hozzáadása (lépésről lépésre)

### Egyszerű publikus oldal

1. Hozz létre egy új `.astro` fájlt a `src/pages/` mappában:

```astro
---
import Layout from '../layouts/Layout.astro';
---
<Layout title="Új oldal">
  <div class="container page">
    <h1>Új oldal</h1>
    <p>Tartalom...</p>
  </div>
</Layout>

<style>
  .page { padding: 40px 0; }
</style>
```

2. Az oldal automatikusan elérhető az URL-en (pl. `src/pages/about.astro` → `/about`)

### Dinamikus oldal (pl. `/items/[id]`)

1. Hozz létre `src/pages/items/[id].astro`:

```astro
---
import Layout from '../../layouts/Layout.astro';
export function getStaticPaths() {
  return [{ params: { id: 'placeholder' } }];
}
---
<Layout title="Item">
  <div class="container page" id="content">
    <p>Betöltés...</p>
  </div>
</Layout>

<script>
  const id = window.location.pathname.split('/').filter(Boolean).pop();
  // Fetch és megjelenítés...
</script>
```

### Védett oldal (bejelentkezés szükséges)

Add hozzá az auth ellenőrzést a `<script>` blokkban:

```javascript
const token = localStorage.getItem('access_token');
if (!token) {
  window.location.href = '/login';
}
const headers = { Authorization: `Bearer ${token}` };
```

---

## 11. Backend API kommunikáció

### Fejlesztés közben

A Docker Compose-zal futtatott környezetben az nginx a 80-as porton:
- `/api/*` → backend (FastAPI, port 8000)
- Minden más → frontend (Astro build)

Az API hívások relatív URL-eket használnak (`/api/courses`, nem `http://localhost:8000/api/courses`), így mind fejlesztésben, mind produkcióban működnek.

### Adatok betöltése

A statikus Astro oldalak kliens oldali `fetch()`-csel töltik be az adatokat:

```javascript
// Publikus endpoint (nem kell token)
const res = await fetch('/api/courses');
const body = await res.json();
const courses = body.data;

// Védett endpoint (token szükséges)
const token = localStorage.getItem('access_token');
const res = await fetch('/api/me/dashboard', {
  headers: { Authorization: `Bearer ${token}` }
});
```

### Hibakezelés minta

```javascript
try {
  const res = await fetch('/api/courses');
  if (!res.ok) {
    container.innerHTML = '<p>Hiba történt.</p>';
    return;
  }
  const data = await res.json();
  // ...megjelenítés
} catch {
  container.innerHTML = '<p>A szolgáltatás nem elérhető.</p>';
}
```

---

## 12. Docker integráció

A frontend a Docker Compose-ban build-only konténerként fut:

```yaml
frontend:
  build: ./frontend
  volumes:
    - frontend_dist:/app/dist   # Build kimenet megosztva nginx-szel
```

A `frontend/Dockerfile` telepíti a csomagokat és futtatja az `astro build`-et. Az nginx a generált fájlokat szolgálja ki a megosztott volume-ból.

### Újraépítés fejlesztés közben

```bash
# Csak a frontend újraépítése
docker compose up -d --build frontend

# Vagy a teljes stack
make up
```

---

## 13. Hibaelhárítás

### „Kurzusok nem elérhetőek" az oldalon

Ez azt jelenti, hogy a frontend nem éri el a backend API-t. Ellenőrizd:

```bash
# Fut-e a backend?
docker compose ps

# Elérhető-e az API?
curl http://localhost:8000/health

# Nginx konfig rendben van?
docker compose logs nginx
```

### Hot reload nem működik

Az Astro dev szerver (`npm run dev`) esetén:
- Ellenőrizd, hogy a helyes mappában vagy-e: `cd frontend`
- Port ütközés: próbáld `npx astro dev --port 4322`

### Styles nem töltődnek be

- Ellenőrizd, hogy a `Layout.astro` importálja a `global.css`-t: `import '../styles/global.css';`
- Docker build után: `docker compose up -d --build frontend`
