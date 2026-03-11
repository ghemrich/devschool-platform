# OpenSchool Platform — Felhasználói útmutató

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · **Felhasználói útmutató** · [Dokumentálás](dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez a dokumentum leírja, hogy az OpenSchool platform felülete hogyan működik: milyen oldalak vannak, mit csinálnak a gombok, és hogyan zajlik a tanulási folyamat a beiratkozástól a tanúsítványig.

---

## Oldalak és funkcióik

### Főoldal (`/`)

A nyitóoldal három részből áll:

1. **Héró szekció** — rövid bevezető és egy „Kurzusok böngészése" gomb, amely a `/courses` oldalra navigál.
2. **Hogyan működik?** — három lépésben bemutatja a folyamatot: Beiratkozás → Feladatok → Tanúsítvány.
3. **Elérhető kurzusok** — az API-ból (`GET /api/courses`) betöltött kurzuskártyák. Minden kártyán egy **„Részletek"** gomb, amely a kurzus részletező oldalára (`/courses/{id}`) visz.

### Belépés (`/login`)

Egyetlen gomb: **„Belépés GitHub-bal"** — átirányít a GitHub OAuth folyamatba (`/api/auth/login`). Sikeres belépés után a backend JWT tokent ad vissza query paraméterben (`?token=...`), amelyet a frontend `localStorage`-ba ment, majd a dashboardra irányít.

### Kurzuslista (`/courses`)

Az összes kurzust listázza kártya formátumban. Minden kártyán:

- **Kurzus neve és leírása**
- **„Részletek"** gomb → a kurzus részletező oldalára navigál

### Kurzus részletei (`/courses/{id}`)

Egy adott kurzus teljes leírása modulokkal és feladatokkal. Az oldal elemei:

| Elem | Funkció |
|---|---|
| **Kurzus neve és leírása** | A kurzus alapadatai |
| **„Beiratkozás" gomb** | `POST /api/courses/{id}/enroll` — beiratkozás a kurzusra. Bejelentkezés szükséges. Ha már beiratkozott, „Már beiratkoztál" üzenet jelenik meg. |
| **Modulok listája** | Minden modul név szerint, alatta a feladatok felsorolva |
| **📎 ikon (feladat mellett)** | Ha a feladathoz van GitHub Classroom link, kattintásra megnyílik egy új lapon |

### Dashboard (`/dashboard`)

A bejelentkezett felhasználó személyes oldala. Bejelentkezés nélkül a `/login` oldalra irányít.

#### Fő elemek

| Elem | Funkció |
|---|---|
| **„Haladás szinkronizálása GitHub-ból" gomb** | `POST /api/me/sync-progress` — végigmegy az összes beiratkozott kurzus minden feladatán, és a GitHub Actions API-n keresztül ellenőrzi, hogy a tanuló repójában sikeres CI futás történt-e. Ha igen, a feladatot megoldottnak jelöli. Szinkronizálás közben a gomb „⏳ Szinkronizálás..." szöveget mutat. |
| **Kurzuskártyák** | Minden beiratkozott kurzushoz egy kártya: kurzusnév, haladási sáv (progress bar), és a megoldott/összes feladat arány (pl. „3/10 — 30%"). |
| **„Tanúsítvány igénylése" gomb** | Csak akkor jelenik meg, ha a haladás 100%. `POST /api/me/courses/{id}/certificate` — tanúsítványt generál az adott kurzushoz. |
| **„PDF letöltése" gomb** | Megjelenik ha már van tanúsítvány. Letölti a tanúsítvány PDF-et (`GET /api/me/certificates/{id}/pdf`), amely tartalmaz egy ellenőrző QR kódot. |

#### A „Haladás szinkronizálása" részletesen

Ez a funkció a kulcsa a platform automatikus értékelési rendszerének:

1. A háttérben a szerver lekéri a felhasználó összes beiratkozását
2. Minden beiratkozott kurzus minden moduljának minden feladatához:
   - Összeállítja a GitHub repo nevét: `{repo_prefix}-{github_username}`
   - Lekéri a GitHub Actions API-tól a legutóbbi CI futás eredményét
   - Ha a futás `conclusion == "success"` → a feladatot megoldottnak jelöli
3. A frontend újratölti az oldalt, hogy az új haladás megjelenjen

> **Megjegyzés:** A platform webhook-ot is fogad (`POST /api/webhooks/github`), így a haladás automatikusan is frissülhet minden sikeres CI futás után, nemcsak manuális szinkronizáláskor.

---

## Admin panel

Az admin panel csak `admin` szerepkörű felhasználóknak érhető el. A navigációs sávban az **„Admin"** link csak admin felhasználóknak jelenik meg.

### Áttekintés (`/admin`)

Összesített statisztikák kártyákon:

| Statisztika | Leírás |
|---|---|
| Felhasználó | Regisztrált felhasználók száma |
| Kurzus | Létrehozott kurzusok száma |
| Beiratkozás | Összes beiratkozás száma |
| Tanúsítvány | Kiadott tanúsítványok száma |
| Feladat | Feladatok száma összesen |

A három admin oldal között fülszerű navigáció biztosítja a váltást (Áttekintés / Felhasználók / Kurzusok).

### Felhasználók kezelése (`/admin/users`)

Táblázat az összes felhasználóról:

| Oszlop | Tartalom |
|---|---|
| Avatar | GitHub profilkép |
| Felhasználónév | GitHub username |
| Email | GitHub email (ha elérhető) |
| Szerepkör | Legördülő lista: `student` / `mentor` / `admin` |
| Regisztráció | Regisztráció dátuma |
| Utolsó belépés | Utolsó belépés dátuma |
| Művelet | **„Mentés"** gomb — csak akkor jelenik meg, ha a szerepkör megváltozott |

A szerepkör módosítása: a legördülő listában kiválasztjuk az új szerepkört → megjelenik a **„Mentés"** gomb → kattintásra `PATCH /api/admin/users/{id}/role` — frissíti a felhasználó szerepkörét.

### Kurzusok kezelése (`/admin/courses`)

Két fő rész:

#### 1. Új kurzus létrehozása

Űrlap két mezővel:
- **Név** (kötelező)
- **Leírás** (opcionális)
- **„Létrehozás"** gomb → `POST /api/courses` — létrehozza a kurzust, majd újratölti az oldalt.

#### 2. Meglévő kurzusok listája

Minden kurzushoz egy kártya:

| Gomb | Funkció |
|---|---|
| **„Részletek"** | Lenyitja/összecsukja a kurzus részleteit (modulok, feladatok, hozzáadás/törlés űrlapok) |
| **„Törlés"** (piros) | `DELETE /api/admin/courses/{id}` — törli a kurzust az összes moduljával, feladatával és beiratkozásával együtt. Megerősítő dialógust kér. |

#### Kurzus részletek (lenyitva)

| Művelet | Leírás |
|---|---|
| **Modul hozzáadása** | Név + sorrend megadása → `POST /api/courses/{id}/modules` |
| **Modul törlése** | **„Modul törlése"** gomb → `DELETE /api/admin/modules/{id}` — törli a modult és összes feladatát. Megerősítést kér. |
| **Feladat hozzáadása** | Név + `repo_prefix` + `classroom_url` + sorrend → `POST /api/courses/{id}/modules/{mid}/exercises` |
| **Feladat törlése** | **✕** gomb a feladat sorában → `DELETE /api/admin/exercises/{id}` |

A `repo_prefix` határozza meg, hogy a GitHub-on milyen nevű repót keres a rendszer a tanuló haladásának ellenőrzéséhez. A `classroom_url` a GitHub Classroom assignment linkje, amely megjelenik 📎 ikonként a kurzus részletező oldalán.

---

## Navigáció

A fejléc (header) minden oldalon megjelenik:

| Elem | Funkció |
|---|---|
| **OpenSchool** logó | Főoldalra navigál |
| **Kurzusok** | `/courses` oldalra navigál |
| **Dashboard** | `/dashboard` oldalra navigál |
| **Admin** | `/admin` oldalra navigál (csak admin felhasználóknak jelenik meg) |
| **Profilom** | `/dashboard` oldalra navigál (bejelentkezett felhasználóknak) |
| **Belépés** (piros gomb) | `/login` oldalra navigál (nem bejelentkezett felhasználóknak) |
| **☰** (hamburger ikon) | Mobil nézetben a navigáció megnyitása/bezárása |

---

## Felhasználói folyamatok összefoglalása

### Tanuló (student)

```
Főoldal → Kurzusok → Részletek → Beiratkozás → GitHub Classroom feladat elfogadása
→ Kód megoldása → CI futás sikerül → Dashboard szinkronizálás → Haladás frissül
→ 100% → Tanúsítvány igénylése → PDF letöltése
```

### Admin

```
Admin Áttekintés → Kurzusok kezelése → Kurzus létrehozása → Modulok hozzáadása
→ Feladatok hozzáadása (repo_prefix + classroom_url) → Felhasználók kezelése
→ Szerepkörök módosítása
```
