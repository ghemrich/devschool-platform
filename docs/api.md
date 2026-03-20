# API Referencia

Az összes API végpont: URL, metódus, hitelesítés, kérés/válasz sémák, státuszkódok.

> **Swagger UI** fejlesztési módban elérhető: `http://localhost:8000/docs` (éles módban kikapcsolva).

## Hitelesítés

JWT alapú, cookie-kon keresztül:

- **Access token:** httpOnly cookie (`access_token`), 30 perc. Alternatívan `Authorization: Bearer <token>` fejléccel
- **Refresh token:** httpOnly cookie (`refresh_token`), 7 nap, `SameSite=Lax`
- **Szerepkörök:** `student`, `mentor`, `admin`
- **Rate limiting:** auth végpontok rate limitáltak

### Token megszerzése

1. `/api/auth/login` → GitHub OAuth redirect (+ `oauth_state` cookie CSRF védelemhez)
2. GitHub → `/api/auth/callback` kóddal és `state` paraméterrel
3. Backend ellenőrzi a `state`-et, felhasználót hoz létre/frissít
4. Redirect `/dashboard` + httpOnly cookie-k beállítása

### Token frissítés

`POST /api/auth/refresh` — refresh token cookie-val új access + refresh tokent ad (token rotáció).

## Hibakezelés

```json
{"detail": "Hibaüzenet szövege"}
```

| Kód | Jelentés |
|-----|----------|
| 200 | Sikeres lekérdezés/módosítás |
| 201 | Sikeres létrehozás |
| 302 | Átirányítás (OAuth) |
| 400 | Érvénytelen kérés |
| 401 | Hitelesítés szükséges / érvénytelen token |
| 403 | Jogosultság megtagadva |
| 404 | Nem található |
| 409 | Ütközés (már beiratkozott, cert már létezik) |
| 413 | Payload túl nagy (webhook max 1 MB) |
| 422 | Pydantic validációs hiba |
| 500 | Szerverhiba |

---

## 1. Health check

### `GET /health`

Publikus.

```json
{"status": "ok"}
```

---

## 2. Auth (`/api/auth`)

### `GET /api/auth/login`

GitHub OAuth redirect. Rate limit: 10/perc. Beállít `oauth_state` cookie-t (CSRF, 10 perc).

### `GET /api/auth/callback`

OAuth callback — kódot cserél tokenre, felhasználót hoz létre/frissít. Rate limit: 10/perc.

| Param | Leírás |
|-------|--------|
| `code` | GitHub OAuth kód (kötelező) |
| `state` | CSRF token (kötelező) |

Siker: `302` → `/dashboard` + cookie-k. Hiba: `400` (érvénytelen state), `401` (OAuth hiba).

Automatikus org meghívás: ha `GITHUB_ORG` + `GITHUB_ORG_ADMIN_TOKEN` konfigurálva van.

### `GET /api/auth/me`

Bejelentkezett felhasználó adatai. Hitelesítés: Bearer / cookie.

```json
{
  "id": 1,
  "github_id": 12345678,
  "username": "diak1",
  "email": "diak1@example.com",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345678",
  "role": "student",
  "discord_id": "123456789012345678"
}
```

### `PATCH /api/auth/me`

Discord ID beállítása/törlése. Hitelesítés: Bearer / cookie.

```json
{"discord_id": "123456789012345678"}
```

Törlés: `{"discord_id": ""}`. Validáció: numerikus snowflake (17-20 számjegy), egyedi, szerveren kell legyen. Sikeres mentés → automatikus Discord szerepkör szinkronizáció.

Hiba: `400` (érvénytelen formátum / nem tag), `409` (már használt ID).

### `POST /api/auth/refresh`

Token rotáció. Hitelesítés: `refresh_token` cookie. Új access + refresh cookie-kat állít be.

```json
{"access_token": "ok", "token_type": "bearer"}
```

### `POST /api/auth/logout`

Refresh token cookie törlése. Hitelesítés nem szükséges.

```json
{"detail": "Logged out"}
```

---

## 3. Kurzusok (`/api/courses`)

### `GET /api/courses`

Publikus kurzuslista, lapozással. Query: `skip` (default: 0), `limit` (default: 50, max: 200).

```json
{
  "total": 3,
  "data": [{"id": 1, "name": "Python Alapok", "description": "...", "created_at": "..."}]
}
```

### `GET /api/courses/{course_id}`

Publikus kurzus részletek modulokkal és feladatokkal. Hiba: `404`.

```json
{
  "id": 1, "name": "Python Alapok",
  "modules": [{
    "id": 1, "name": "Változók és típusok", "order": 1,
    "exercises": [{"id": 1, "name": "Hello World", "repo_prefix": "python-alapok-hello", "classroom_url": "https://classroom.github.com/a/abc123", "order": 1}]
  }]
}
```

### `POST /api/courses` *(admin)*

Kurzus létrehozása. `201`.

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `description` | string | nem | max 5000, default: `""` |

### `PUT /api/courses/{course_id}` *(admin)*

Kurzus módosítása. Formátum: mint POST. Hiba: `404`.

### `POST /api/courses/{course_id}/modules` *(admin)*

Modul hozzáadása. `201`.

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `order` | int | nem | ≥ 0, default: 0 |

### `POST /api/courses/{course_id}/modules/{module_id}/exercises` *(admin)*

Feladat hozzáadása. `201`.

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `repo_prefix` | string | nem | max 200, default: `""` |
| `classroom_url` | string | nem | max 500, default: `""` |
| `order` | int | nem | ≥ 0, default: 0 |
| `required` | bool | nem | default: `true` |

### `POST /api/courses/{course_id}/enroll`

Beiratkozás. Hitelesítés: Bearer / cookie. `201`. Hiba: `404`, `409` (már beiratkozott).

### `POST /api/courses/{course_id}/unenroll`

Leiratkozás. Hitelesítés: Bearer / cookie. `200`. Hiba: `404` (nem beiratkozott).

### `GET /api/courses/{course_id}/students` *(mentor/admin)*

Diáklista haladással.

```json
{
  "course_name": "Python Alapok",
  "students": [{
    "user_id": 3, "username": "diak1", "avatar_url": "...",
    "total_exercises": 10, "completed_exercises": 7, "progress_percent": 70.0,
    "enrolled_at": "2025-09-15T08:00:00"
  }]
}
```

### `GET /api/courses/{course_id}/students/{user_id}/exercises` *(mentor/admin)*

Diák feladatonkénti haladása GitHub Classroom linkekkel.

```json
{
  "course_name": "Python Alapok",
  "username": "diak1",
  "modules": [{
    "module_id": 1, "module_name": "Változók és típusok",
    "exercises": [
      {"exercise_id": 1, "name": "Hello World", "status": "completed", "classroom_url": "https://classroom.github.com/a/abc123"},
      {"exercise_id": 2, "name": "Típuskonverzió", "status": "not_started", "classroom_url": null}
    ]
  }]
}
```

---

## 4. Dashboard / Haladás (`/api/me`)

Minden végpont: Hitelesítés Bearer / cookie.

### `GET /api/me/courses`

Beiratkozott kurzusok haladás-összesítéssel.

```json
[{
  "course_id": 1, "course_name": "Python Alapok",
  "total_exercises": 10, "completed_exercises": 7, "progress_percent": 70.0,
  "enrolled_at": "2025-09-15T08:00:00"
}]
```

### `GET /api/me/dashboard`

Alias: `GET /api/me/courses`.

### `GET /api/me/courses/{course_id}/progress`

Részletes haladás modulonként.

```json
[{
  "module_id": 1, "module_name": "Változók és típusok",
  "exercises": [
    {"id": 1, "name": "Hello World", "status": "completed", "completed_at": "2025-09-20T14:30:00"},
    {"id": 2, "name": "Típuskonverzió", "status": "not_started", "completed_at": null}
  ]
}]
```

Státuszok: `not_started`, `in_progress`, `completed`.

### `POST /api/me/courses/{course_id}/progress`

Feladat manuális jelölése.

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `exercise_id` | int | igen | — |
| `status` | string | nem | `"completed"` / `"in_progress"`, default: `"completed"` |

Hiba: `400` (nem beiratkozott / nem a kurzushoz tartozik), `404`.

### `POST /api/me/sync-progress`

GitHub CI állapot szinkronizálás. A backend `GITHUB_ORG_ADMIN_TOKEN`-nel lekéri a `{repo_prefix}-{username}` repók CI futását. Hiba: `400` (nincs `GITHUB_ORG` / `GITHUB_ORG_ADMIN_TOKEN`).

---

## 5. Tanúsítványok

### `GET /api/me/certificates`

Saját tanúsítványok listája.

```json
[{"cert_id": "a1b2c3d4-...", "course_id": 1, "issued_at": "2025-12-01T10:00:00"}]
```

### `POST /api/me/courses/{course_id}/certificate`

Tanúsítvány igénylése. `201`. Feltétel: összes `required=True` feladat `completed`. PDF + QR kód generálás.

Hiba: `400` (nincs befejezve), `404`, `409` (már létezik).

### `GET /api/me/certificates/{cert_id}/pdf`

PDF letöltés (`application/pdf`). Hiba: `404`.

### `GET /api/verify/{cert_id}`

Publikus verifikáció. Hitelesítés nem szükséges.

```json
{"valid": true, "name": "diak1", "course": "Python Alapok", "issued_at": "...", "cert_id": "..."}
```

---

## 6. Admin (`/api/admin`)

Minden végpont: `admin` szerepkör szükséges.

### `GET /api/admin/stats`

```json
{"users": 150, "courses": 5, "enrollments": 420, "certificates": 38, "exercises": 75}
```

### `GET /api/admin/users`

| Query | Típus | Default | Leírás |
|-------|-------|---------|--------|
| `skip` | int | 0 | Kihagyás (≥ 0) |
| `limit` | int | 50 | Maximum (1–200) |
| `sort_by` | string | `"created_at"` | `created_at`, `username`, `role` |
| `sort_order` | string | `"desc"` | `asc`, `desc` |

```json
{"total": 150, "data": [{"id": 1, "username": "diak1", "email": "...", "role": "student", "created_at": "...", "last_login": "..."}]}
```

### `PATCH /api/admin/users/{user_id}/role`

```json
{"role": "mentor"}
```

Érvényes: `student`, `mentor`, `admin`. Hiba: `400` (érvénytelen / saját maga), `404`.

### `DELETE /api/admin/courses/{course_id}`

Kaszkád törlés (modulok, feladatok, beiratkozások, haladás, tanúsítványok). Hiba: `404`.

### `DELETE /api/admin/modules/{module_id}`

Modul törlése feladatokkal és haladással.

### `DELETE /api/admin/exercises/{exercise_id}`

Feladat törlése haladás rekordokkal.

### `GET /api/admin/promotion-rules`

```json
[{"id": 1, "name": "Python Mentor", "description": "...", "target_role": "mentor", "is_active": true, "course_ids": [1, 3]}]
```

### `POST /api/admin/promotion-rules`

| Mező | Típus | Kötelező | Validáció |
|------|-------|----------|-----------|
| `name` | string | igen | 1–200 karakter |
| `description` | string | nem | max 2000 |
| `target_role` | string | igen | `"mentor"` / `"admin"` |
| `course_ids` | int[] | igen | ≥1 létező kurzus |

### `GET /api/admin/promotion-rules/{rule_id}`

Szabály részletek. Hiba: `404`.

### `PATCH /api/admin/promotion-rules/{rule_id}`

Részleges frissítés. Minden mező opcionális: `name`, `description`, `target_role`, `is_active`, `course_ids`.

### `DELETE /api/admin/promotion-rules/{rule_id}`

Szabály törlése. Hiba: `404`.

### `GET /api/admin/promotion-log`

Query: `skip` (default: 0), `limit` (default: 50).

```json
[{"id": 1, "user_id": 3, "username": "diak1", "rule_id": 1, "rule_name": "Python Mentor", "previous_role": "student", "new_role": "mentor", "promoted_at": "..."}]
```

---

## 7. Webhooks

### `POST /api/webhooks/github`

GitHub webhook — `workflow_run` események alapján frissíti a haladást.

Hitelesítés: HMAC-SHA256 (`X-Hub-Signature-256` fejléc), ha `GITHUB_WEBHOOK_SECRET` be van állítva.

Működés:
1. `workflow_run` + `action=completed` + `conclusion=success`
2. Repó neve: `{repo_prefix}-{username}` → feladat + felhasználó egyeztetés
3. Haladás → `completed`

```json
{"status": "processed", "repo": "python-alapok-hello-diak1", "updated": true}
```


