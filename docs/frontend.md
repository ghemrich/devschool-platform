# Frontend fejlesztés

A React + TypeScript + Vite frontend fejlesztéséhez szükséges minden: struktúra, oldalak, komponensek, API kommunikáció, stílusok, tesztelés.

## Telepítés és indítás

```bash
cd frontend
npm install
npm run dev      # Vite dev szerver: http://localhost:4321 (HMR)
npm run build    # TypeScript check + Vite build → dist/
```

A Vite dev szerver proxy-zza a `/api` hívásokat a backend-re (`http://localhost:8000`). Docker nélküli lokális fejlesztés is lehetséges.

## Könyvtárstruktúra

```
frontend/
├── vite.config.ts         # Vite konfig (React plugin, proxy, Vitest)
├── eslint.config.js       # ESLint 9 flat config
├── .prettierrc            # Prettier beállítások
├── package.json
├── tsconfig.json          # TypeScript strict mód
├── public/                # Statikus fájlok
└── src/
    ├── main.tsx           # Belépési pont — React DOM render, BrowserRouter
    ├── App.tsx            # Útvonalak (React Router)
    ├── styles/
    │   └── global.css     # CSS változók, globális stílusok
    ├── components/
    │   ├── Layout.tsx     # Header, footer, auth nav, hamburger menü
    │   ├── CourseCard.tsx  # Kurzus kártya
    │   └── ProgressBar.tsx # Haladási sáv
    ├── lib/
    │   ├── api.ts         # API wrapper — cookie-alapú auth, auto-refresh
    │   ├── config.ts      # Oldal konfig (név, GitHub URL, Discord link)
    │   └── types.ts       # TypeScript interfészek
    ├── pages/
    │   ├── HomePage.tsx
    │   ├── LoginPage.tsx
    │   ├── CoursesPage.tsx
    │   ├── CourseDetailPage.tsx
    │   ├── DashboardPage.tsx
    │   ├── VerifyPage.tsx
    │   └── admin/
    │       ├── AdminPage.tsx
    │       ├── AdminCoursesPage.tsx
    │       └── AdminUsersPage.tsx
    └── test/
        ├── setup.ts
        ├── App.test.tsx
        ├── components/
        ├── pages/
        └── lib/
```

## Útvonalak (React Router)

```tsx
<Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/courses" element={<CoursesPage />} />
  <Route path="/courses/:id" element={<CourseDetailPage />} />
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/admin" element={<AdminPage />} />
  <Route path="/admin/courses" element={<AdminCoursesPage />} />
  <Route path="/admin/users" element={<AdminUsersPage />} />
  <Route path="/verify/:id" element={<VerifyPage />} />
</Routes>
```

Minden útvonal a `Layout` komponensbe van csomagolva (header, footer).

## API kommunikáció (`api.ts`)

Az `apiFetch()` kezeli az autentikációt cookie-alapon:

1. Cookie-kat küldi (`credentials: 'same-origin'`)
2. Ha `401`, megpróbálja frissíteni a tokent `/api/auth/refresh`-en
3. Ha a refresh is sikertelen, átirányít `/login`-ra

```typescript
import { apiFetch } from '../lib/api';
const res = await apiFetch('/api/me/dashboard');
const data = await res.json();
```

## Autentikáció

httpOnly cookie-k — a tokenek nem hozzáférhetőek JavaScript-ből. A böngésző automatikusan küldi minden kéréssel. Védett oldalak a `/api/auth/me` végponton ellenőrzik a hitelesítést, és szükség esetén `/login`-ra irányítanak.

## Stílusok (CSS)

Vanilla CSS, CSS változókkal, framework nélkül:

```css
:root {
  --color-primary: #2c3e50;
  --color-accent: #e74c3c;
  --color-bg: #f8f9fa;
  --color-text: #333;
  --color-success: #27ae60;
  --max-width: 1200px;
}
```

Reszponzív: `@media (max-width: 767px)` töréspont.

## Admin panel

| Oldal | API | Funkciók |
|-------|-----|----------|
| Áttekintés (`AdminPage.tsx`) | `GET /api/admin/stats` | Statisztikák |
| Felhasználók (`AdminUsersPage.tsx`) | `GET /api/admin/users`, `PATCH .../role` | Táblázat, szerepkör módosítás |
| Kurzusok (`AdminCoursesPage.tsx`) | CRUD végpontok | Kurzus/modul/feladat létrehozás, törlés |

## Mentor dashboard

| Oldal | API | Funkciók |
|-------|-----|----------|
| Mentor (`MentorDashboardPage.tsx`) | `GET /api/courses/{id}/students`, `GET /api/courses/{id}/students/{uid}/exercises` | Diákok haladása, feladatonkénti részletek, GitHub Classroom linkek |

## Linting és formázás

```bash
npm run lint          # ESLint ellenőrzés
npm run lint:fix      # ESLint javítás
npm run format:check  # Prettier ellenőrzés
npm run format        # Prettier formázás
npx tsc --noEmit      # TypeScript ellenőrzés
```

ESLint 9 flat config (`eslint.config.js`), Prettier (`.prettierrc`). Pre-commit hookok automatikusan futtatják.

## Tesztelés

Vitest + React Testing Library.

```bash
npm test          # Vitest egyszer
npx vitest        # Watch mód
npx vitest --ui   # Böngészős UI
```

### Teszt fájlok

| Fájl | Tesztel |
|------|---------|
| `App.test.tsx` | Routing |
| `components/Layout.test.tsx` | Header, navigáció, auth állapot |
| `components/CourseCard.test.tsx` | Kurzus kártya |
| `components/ProgressBar.test.tsx` | Haladási sáv |
| `pages/HomePage.test.tsx` | Szekciók, kurzusok betöltése |
| `pages/LoginPage.test.tsx` | Login gomb |
| `pages/CoursesPage.test.tsx` | Kurzuslista |
| `pages/DashboardPage.test.tsx` | Dashboard |
| `pages/VerifyPage.test.tsx` | Tanúsítvány verifikáció |
| `lib/api.test.ts` | API wrapper, token refresh |
| `lib/config.test.ts` | Konfiguráció |

### Teszt minta

```tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MemoryRouter><MyComponent /></MemoryRouter>);
    expect(screen.getByText('Expected text')).toBeInTheDocument();
  });
});
```

## Új oldal hozzáadása

1. Új `.tsx` fájl a `src/pages/`-ben
2. Útvonal hozzáadása az `App.tsx`-ben
3. Védett oldalak: `useEffect`-ben `/api/auth/me` ellenőrzés

## Docker integráció

A frontend a Docker Compose-ban build konténerként fut. A `Dockerfile` `npm run build`-et futtat, az nginx a generált fájlokat szolgálja ki. Újraépítés: `docker compose up -d --build frontend`.
