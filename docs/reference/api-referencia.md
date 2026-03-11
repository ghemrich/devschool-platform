# OpenSchool Platform — API Referencia

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](../development/fejlesztoi-utmutato.md) · [Backend](../development/backend-fejlesztes.md) · [Frontend](../development/frontend-fejlesztes.md) · [Tesztelés](../development/tesztelesi-utmutato.md) · **API referencia** · [Adatbázis](adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez a dokumentum az összes API végpontot részletesen leírja: URL, metódus, hitelesítés, kérés/válasz sémák, státuszkódok.

> **Swagger UI** fejlesztési módban elérhető: `http://localhost:8000/docs` (éles módban kikapcsolva).

---

## Hitelesítés

Az API JWT (JSON Web Token) alapú hitelesítést használ:

- **Access token:** `Authorization: Bearer <token>` fejléccel küldve, 30 perc érvényesség
- **Refresh token:** HttpOnly cookie (`refresh_token`), 7 nap érvényesség, `SameSite=Lax`
- **Szerepkörök:** `student`, `mentor`, `admin` — egyes végpontok `admin` vagy `mentor` jogosultságot igényelnek

### Token megszerzése

1. A felhasználó a `/api/auth/login`-ra navigál → GitHub OAuth oldalra irányítás
2. GitHub visszairányít a `/api/auth/callback`-re a kóddal
3. A backend kicseréli a kódot access tokenre, létrehoz/frissít felhasználót
4. Redirect: `/login#token=<access_token>` + `refresh_token` cookie beállítása

### Token frissítés

A frontend a `refresh_token` cookie-t használva a `POST /api/auth/refresh` végpontot hívja, hogy új access tokent kapjon.

---

## Hibakezelés

Minden hiba JSON formátumban tér vissza:

```json
{"detail": "Hibaüzenet szövege"}
```

Visszatérő státuszkódok:

| Kód | Jelentés |
|-----|----------|
| 200 | Sikeres lekérdezés/módosítás |
| 201 | Sikeres létrehozás |
| 302 | Átirányítás (OAuth flow) |
| 400 | Érvénytelen kérés (validációs hiba, üzleti szabály) |
| 401 | Hitelesítés szükséges vagy érvénytelen token |
| 403 | Jogosultság megtagadva (webhook aláírás hiba) |
| 404 | Erőforrás nem található |
| 409 | Ütközés (pl. már beiratkozott, tanúsítvány már létezik) |
| 422 | Pydantic validációs hiba (hiányzó/érvénytelen mező) |
| 500 | Szerverhiba (logolva, kliensnek: „Internal server error") |

---

## 1. Health check

### `GET /health`

Publikus — hitelesítés nem szükséges.

**Válasz:**
```json
{"status": "ok"}
```

---

## 2. Auth (`/api/auth`)

### `GET /api/auth/login`

Átirányítja a felhasználót a GitHub OAuth engedélyezési oldalra.

| | |
|---|---|
| **Hitelesítés** | Nem szükséges |
| **Válasz** | `302` redirect a GitHub-ra |
| **Scope** | `read:user user:email` |

---

### `GET /api/auth/callback`

GitHub OAuth callback — kódot fogad, tokent cserél, felhasználót hoz létre/frissít.

| | |
|---|---|
| **Hitelesítés** | Nem szükséges |
| **Query paraméter** | `code` (GitHub OAuth kód) — **kötelező** |
| **Siker** | `302` redirect: `/login#token=<access_token>` + `refresh_token` cookie |
| **Hiba** | `401` — OAuth hiba vagy érvénytelen GitHub felhasználó |

**Felhasználó létrehozás/frissítés:** A callback létrehoz egy új `User` rekordot (ha nem létezik `github_id` alapján), vagy frissíti a meglévőt (`username`, `avatar_url`, `email`, `github_token`, `last_login`).

---

### `GET /api/auth/me`

Az aktuálisan bejelentkezett felhasználó adatai.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Válasz** | `200` |

```json
{
  "id": 1,
  "github_id": 12345678,
  "username": "diak1",
  "email": "diak1@example.com",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
  "role": "student"
}
```

---

### `POST /api/auth/refresh`

Új access tokent ad ki a refresh token cookie alapján.

| | |
|---|---|
| **Hitelesítés** | `refresh_token` cookie (automatikusan küldve) |
| **Válasz** | `200` |
| **Hiba** | `401` — nincs/érvénytelen/lejárt refresh token |

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### `POST /api/auth/logout`

Törli a refresh token cookie-t.

| | |
|---|---|
| **Hitelesítés** | Nem szükséges |
| **Válasz** | `200` |

```json
{"detail": "Logged out"}
```

---

## 3. Kurzusok (`/api/courses`)

### `GET /api/courses`

Kurzusok listázása lapozással (publikus).

| | |
|---|---|
| **Hitelesítés** | Nem szükséges |
| **Query paraméterek** | `skip` (int, default: 0, min: 0), `limit` (int, default: 50, min: 1, max: 200) |

**Válasz (200):**
```json
{
  "total": 3,
  "data": [
    {
      "id": 1,
      "name": "Python 10",
      "description": "Bevezető Python kurzus",
      "created_at": "2025-09-01T10:00:00"
    }
  ]
}
```

---

### `GET /api/courses/{course_id}`

Kurzus részletei modulokkal és feladatokkal (publikus).

| | |
|---|---|
| **Hitelesítés** | Nem szükséges |
| **Siker** | `200` |
| **Hiba** | `404` — kurzus nem található |

**Válasz (200):**
```json
{
  "id": 1,
  "name": "Python 10",
  "description": "Bevezető Python kurzus",
  "modules": [
    {
      "id": 1,
      "name": "Változók és típusok",
      "order": 1,
      "exercises": [
        {
          "id": 1,
          "name": "Hello World",
          "repo_prefix": "python10-hello",
          "classroom_url": "https://classroom.github.com/a/abc123",
          "order": 1
        }
      ]
    }
  ]
}
```

---

### `POST /api/courses` *(admin)*

Új kurzus létrehozása.

| | |
|---|---|
| **Hitelesítés** | Bearer token, `admin` szerepkör |
| **Siker** | `201` |
| **Hiba** | `422` — validációs hiba |

**Kérés:**
```json
{
  "name": "Backend 13",
  "description": "Backend fejlesztés FastAPI-val"
}
```

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `description` | string | nem | max 5000 karakter, default: `""` |

**Válasz (201):**
```json
{"id": 2, "name": "Backend 13"}
```

---

### `PUT /api/courses/{course_id}` *(admin)*

Kurzus módosítása.

| | |
|---|---|
| **Hitelesítés** | Bearer token, `admin` szerepkör |
| **Siker** | `200` |
| **Hiba** | `404` — nem található |

Kérés/válasz: megegyezik a `POST /api/courses` formátumával.

---

### `POST /api/courses/{course_id}/modules` *(admin)*

Modul hozzáadása kurzushoz.

| | |
|---|---|
| **Hitelesítés** | Bearer token, `admin` szerepkör |
| **Siker** | `201` |
| **Hiba** | `404` — kurzus nem található |

**Kérés:**
```json
{
  "name": "Változók és típusok",
  "order": 1
}
```

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `order` | int | nem | ≥ 0, default: 0 |

**Válasz (201):**
```json
{"id": 1, "name": "Változók és típusok"}
```

---

### `POST /api/courses/{course_id}/modules/{module_id}/exercises` *(admin)*

Feladat hozzáadása modulhoz.

| | |
|---|---|
| **Hitelesítés** | Bearer token, `admin` szerepkör |
| **Siker** | `201` |
| **Hiba** | `404` — modul nem található |

**Kérés:**
```json
{
  "name": "Hello World",
  "repo_prefix": "python10-hello",
  "classroom_url": "https://classroom.github.com/a/abc123",
  "order": 1,
  "required": true
}
```

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `repo_prefix` | string | nem | max 200 karakter, default: `""` |
| `classroom_url` | string | nem | max 500 karakter, default: `""` |
| `order` | int | nem | ≥ 0, default: 0 |
| `required` | bool | nem | default: `true` |

**Válasz (201):**
```json
{"id": 1, "name": "Hello World"}
```

---

### `POST /api/courses/{course_id}/enroll`

Beiratkozás kurzusra (bejelentkezett felhasználó).

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Siker** | `201` |
| **Hiba** | `404` — kurzus nem található, `409` — már beiratkozott |

**Válasz (201):**
```json
{"detail": "Enrolled successfully"}
```

---

### `POST /api/courses/{course_id}/unenroll`

Leiratkozás kurzusról.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Siker** | `200` |
| **Hiba** | `404` — nem beiratkozott |

**Válasz (200):**
```json
{"detail": "Unenrolled successfully"}
```

---

### `GET /api/courses/{course_id}/students` *(mentor/admin)*

Beiratkozott diákok listája haladással.

| | |
|---|---|
| **Hitelesítés** | Bearer token, `mentor` vagy `admin` szerepkör |
| **Siker** | `200` |
| **Hiba** | `404` — kurzus nem található |

**Válasz (200):**
```json
{
  "course_name": "Python 10",
  "students": [
    {
      "user_id": 3,
      "username": "diak1",
      "avatar_url": "https://...",
      "total_exercises": 10,
      "completed_exercises": 7,
      "progress_percent": 70.0,
      "enrolled_at": "2025-09-15T08:00:00"
    }
  ]
}
```

---

## 4. Dashboard / Haladás (`/api/me`)

### `GET /api/me/courses`

A bejelentkezett felhasználó beiratkozott kurzusai haladás-összesítéssel.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Válasz** | `200` |

```json
[
  {
    "course_id": 1,
    "course_name": "Python 10",
    "total_exercises": 10,
    "completed_exercises": 7,
    "progress_percent": 70.0,
    "enrolled_at": "2025-09-15T08:00:00"
  }
]
```

---

### `GET /api/me/dashboard`

Azonos a `GET /api/me/courses`-szal — kényelmi alias.

---

### `GET /api/me/courses/{course_id}/progress`

Kurzus részletes haladása modulonként és feladatonként.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Válasz** | `200` |

```json
[
  {
    "module_id": 1,
    "module_name": "Változók és típusok",
    "exercises": [
      {
        "id": 1,
        "name": "Hello World",
        "status": "completed",
        "completed_at": "2025-09-20T14:30:00"
      },
      {
        "id": 2,
        "name": "Típuskonverzió",
        "status": "not_started",
        "completed_at": null
      }
    ]
  }
]
```

A `status` értékek: `not_started`, `in_progress`, `completed`.

---

### `POST /api/me/courses/{course_id}/progress`

Feladat manuális teljesítés jelölése.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Siker** | `200` |
| **Hiba** | `400` — nem beiratkozott vagy feladat nem tartozik a kurzushoz, `404` — feladat nem található |

**Kérés:**
```json
{
  "exercise_id": 1,
  "status": "completed"
}
```

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `exercise_id` | int | igen | - |
| `status` | string | nem | `"completed"` vagy `"in_progress"`, default: `"completed"` |

**Válasz (200):**
```json
{"status": "ok", "exercise_id": 1, "progress": "completed"}
```

---

### `POST /api/me/sync-progress`

Haladás szinkronizálása a GitHub CI állapotából. Végigmegy az összes beiratkozott kurzus feladatán, és a GitHub Actions futási eredmény alapján frissíti.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Siker** | `200` — frissített kurzuslista (mint `GET /api/me/courses`) |
| **Hiba** | `400` — nincs GitHub token (újbóli bejelentkezés szükséges) |

**Működés:** A backend a `GITHUB_ORG` (vagy a felhasználó GitHub neve) szervezet alatt keresi a `{repo_prefix}-{username}` nevű repókat, és lekéri a legutóbbi sikeres CI futást a GitHub API-ból.

---

## 5. Tanúsítványok

### `GET /api/me/certificates`

A bejelentkezett felhasználó tanúsítványai.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Válasz** | `200` |

```json
[
  {
    "cert_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "course_id": 1,
    "issued_at": "2025-12-01T10:00:00"
  }
]
```

---

### `POST /api/me/courses/{course_id}/certificate`

Tanúsítvány igénylése befejezett kurzushoz. Generál PDF-et QR kóddal.

| | |
|---|---|
| **Hitelesítés** | Bearer token (bármely szerepkör) |
| **Siker** | `201` |
| **Hiba** | `400` — kurzus nincs befejezve, `404` — kurzus nem található, `409` — tanúsítvány már létezik |

**Befejezettség feltétele:** A kurzus összes `required=True` feladatának `completed` státuszúnak kell lennie.

**Válasz (201):**
```json
{
  "cert_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "course_id": 1,
  "issued_at": "2025-12-01T10:00:00"
}
```

---

### `GET /api/me/certificates/{cert_id}/pdf`

Tanúsítvány PDF letöltése.

| | |
|---|---|
| **Hitelesítés** | Bearer token (saját tanúsítvány) |
| **Siker** | `200` — PDF fájl (`application/pdf`) |
| **Hiba** | `404` — tanúsítvány vagy PDF nem található |

---

### `GET /api/verify/{cert_id}`

Tanúsítvány publikus verifikáció (hitelesítés nem szükséges).

| | |
|---|---|
| **Hitelesítés** | Nem szükséges |
| **Siker** | `200` |
| **Hiba** | `404` — érvénytelen tanúsítvány |

**Válasz (200):**
```json
{
  "valid": true,
  "name": "diak1",
  "course": "Python 10",
  "issued_at": "2025-12-01T10:00:00",
  "cert_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 6. Admin (`/api/admin`)

Minden admin végpont `admin` szerepkörű hitelesítést igényel.

### `GET /api/admin/stats`

Platform statisztikák.

**Válasz (200):**
```json
{
  "users": 150,
  "courses": 5,
  "enrollments": 420,
  "certificates": 38,
  "exercises": 75
}
```

---

### `GET /api/admin/users`

Felhasználók listázása lapozással és rendezéssel.

| Query paraméter | Típus | Default | Leírás |
|-----------------|-------|---------|--------|
| `skip` | int | 0 | Kihagyandó rekordok (≥ 0) |
| `limit` | int | 50 | Maximum rekordok (1–200) |
| `sort_by` | string | `"created_at"` | Rendezés: `created_at`, `username`, `role` |
| `sort_order` | string | `"desc"` | Irány: `asc`, `desc` |

**Válasz (200):**
```json
{
  "total": 150,
  "data": [
    {
      "id": 1,
      "username": "diak1",
      "email": "diak1@example.com",
      "avatar_url": "https://...",
      "role": "student",
      "created_at": "2025-09-01T10:00:00",
      "last_login": "2025-12-01T08:00:00"
    }
  ]
}
```

---

### `PATCH /api/admin/users/{user_id}/role`

Felhasználó szerepkörének módosítása.

| | |
|---|---|
| **Hiba** | `400` — érvénytelen szerepkör vagy saját maga módosítása, `404` — felhasználó nem található |

**Kérés:**
```json
{"role": "mentor"}
```

| Mező | Típus | Érvényes értékek |
|------|-------|------------------|
| `role` | string | `"student"`, `"mentor"`, `"admin"` |

**Válasz (200):**
```json
{"id": 3, "username": "diak1", "role": "mentor"}
```

---

### `DELETE /api/admin/courses/{course_id}`

Kurzus törlése kaszkádoltan (modulok, feladatok, beiratkozások, haladás, tanúsítványok).

| | |
|---|---|
| **Siker** | `200` |
| **Hiba** | `404` — nem található |

```json
{"detail": "Course deleted"}
```

---

### `DELETE /api/admin/modules/{module_id}`

Modul törlése (feladatok és haladás törlődik).

```json
{"detail": "Module deleted"}
```

---

### `DELETE /api/admin/exercises/{exercise_id}`

Feladat törlése (haladás rekordok törlődnek).

```json
{"detail": "Exercise deleted"}
```

---

## 7. Webhooks

### `POST /api/webhooks/github`

GitHub webhook fogadása — `workflow_run` események alapján automatikusan frissíti a feladatok haladását.

| | |
|---|---|
| **Hitelesítés** | HMAC-SHA256 aláírás (`X-Hub-Signature-256` fejléc), ha `GITHUB_WEBHOOK_SECRET` be van állítva |
| **Figyelt esemény** | `workflow_run` (action: `completed`, conclusion: `success`) |

**Fejlécek:**

| Fejléc | Leírás |
|--------|--------|
| `X-Hub-Signature-256` | HMAC-SHA256 aláírás a webhook secret-tel |
| `X-GitHub-Event` | Esemény típusa (csak `workflow_run` számít) |

**Hogyan működik:**

1. GitHub küld egy `workflow_run` eseményt, amikor egy Actions futás befejeződik
2. A backend ellenőrzi az aláírást (ha secret be van állítva)
3. Ha az `action=completed` és `conclusion=success`, kikeresi a repó nevéből a feladatot
4. A repó neve `{repo_prefix}-{username}` formátumú — a `repo_prefix` alapján egyezteti a feladatot, a `username` alapján a felhasználót
5. Frissíti a haladást `completed` státuszra

**Válasz (200):**
```json
{"status": "processed", "repo": "python10-hello-diak1", "updated": true}
```

**Figyelmen kívül hagyott események:**
```json
{"status": "ignored", "event": "push"}
{"status": "ignored", "reason": "not completed"}
{"status": "ignored", "reason": "not successful"}
```

---

## Összefoglaló tábla

| Végpont | Metódus | Hitelesítés | Leírás |
|---------|---------|-------------|--------|
| `/health` | GET | — | Állapot ellenőrzés |
| `/api/auth/login` | GET | — | GitHub OAuth redirect |
| `/api/auth/callback` | GET | — | OAuth callback |
| `/api/auth/me` | GET | Bearer | Profil |
| `/api/auth/refresh` | POST | Cookie | Token frissítés |
| `/api/auth/logout` | POST | — | Kijelentkezés |
| `/api/courses` | GET | — | Kurzuslista |
| `/api/courses/{id}` | GET | — | Kurzus részletek |
| `/api/courses` | POST | Admin | Kurzus létrehozás |
| `/api/courses/{id}` | PUT | Admin | Kurzus módosítás |
| `/api/courses/{id}/modules` | POST | Admin | Modul hozzáadás |
| `/api/courses/{id}/modules/{mid}/exercises` | POST | Admin | Feladat hozzáadás |
| `/api/courses/{id}/enroll` | POST | Bearer | Beiratkozás |
| `/api/courses/{id}/unenroll` | POST | Bearer | Leiratkozás |
| `/api/courses/{id}/students` | GET | Mentor+ | Diáklista haladással |
| `/api/me/courses` | GET | Bearer | Beiratkozott kurzusok |
| `/api/me/dashboard` | GET | Bearer | Dashboard (= /me/courses) |
| `/api/me/courses/{id}/progress` | GET | Bearer | Részletes haladás |
| `/api/me/courses/{id}/progress` | POST | Bearer | Feladat jelölés |
| `/api/me/sync-progress` | POST | Bearer | GitHub CI szinkron |
| `/api/me/certificates` | GET | Bearer | Tanúsítványok |
| `/api/me/courses/{id}/certificate` | POST | Bearer | Tanúsítvány igénylés |
| `/api/me/certificates/{id}/pdf` | GET | Bearer | PDF letöltés |
| `/api/verify/{cert_id}` | GET | — | Publikus verifikáció |
| `/api/admin/stats` | GET | Admin | Statisztikák |
| `/api/admin/users` | GET | Admin | Felhasználólista |
| `/api/admin/users/{id}/role` | PATCH | Admin | Szerepkör módosítás |
| `/api/admin/courses/{id}` | DELETE | Admin | Kurzus törlés |
| `/api/admin/modules/{id}` | DELETE | Admin | Modul törlés |
| `/api/admin/exercises/{id}` | DELETE | Admin | Feladat törlés |
| `/api/webhooks/github` | POST | HMAC | GitHub webhook |
