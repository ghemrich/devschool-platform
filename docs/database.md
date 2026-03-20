# Adatbázis séma

Az adatbázis SQLAlchemy ORM-mel van definiálva, Alembic migrációkkal kezelve. Fejlesztésben SQLite, élesben PostgreSQL 16.

## ER diagram

```mermaid
erDiagram
    users ||--o{ enrollments : "beiratkozik"
    users ||--o{ progress : "haladás"
    users ||--o{ certificates : "tanúsítvány"
    users ||--o{ promotion_log : "előléptetés"
    courses ||--o{ modules : "tartalmaz"
    courses ||--o{ enrollments : "beiratkozás"
    courses ||--o{ certificates : "tanúsítvány"
    courses ||--o{ promotion_rule_requirements : "feltétel"
    modules ||--o{ exercises : "tartalmaz"
    exercises ||--o{ progress : "haladás"
    promotion_rules ||--o{ promotion_rule_requirements : "követelmény"
    promotion_rules ||--o{ promotion_log : "napló"

    users {
        int id PK
        int github_id UK
        string username UK
        string email
        string avatar_url
        enum role
        string discord_id UK
        datetime created_at
        datetime last_login
    }

    courses {
        int id PK
        string name
        text description
        datetime created_at
    }

    modules {
        int id PK
        int course_id FK
        string name
        int order
    }

    exercises {
        int id PK
        int module_id FK
        string name
        string repo_prefix
        string classroom_url
        string classroom_teacher_url
        int order
        bool required
    }

    enrollments {
        int id PK
        int user_id FK
        int course_id FK
        datetime enrolled_at
    }

    progress {
        int id PK
        int user_id FK
        int exercise_id FK
        string github_repo
        enum status
        datetime completed_at
    }

    certificates {
        int id PK
        string cert_id UK
        int user_id FK
        int course_id FK
        datetime issued_at
        string pdf_path
    }

    promotion_rules {
        int id PK
        string name
        string description
        enum target_role
        bool is_active
        datetime created_at
    }

    promotion_rule_requirements {
        int id PK
        int rule_id FK
        int course_id FK
    }

    promotion_log {
        int id PK
        int user_id FK
        int rule_id FK
        enum previous_role
        enum new_role
        datetime promoted_at
    }
```

---

## Táblák

### `users`

GitHub OAuth-tal regisztrált felhasználók.

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `github_id` | Integer | Nem | — | GitHub azonosító (unique) |
| `username` | String | Nem | — | GitHub felhasználónév (unique), bejelentkezéskor frissül |
| `email` | String | Igen | — | GitHub email (lehet null, ha privát) |
| `avatar_url` | String | Igen | — | Profilkép URL, bejelentkezéskor frissül |
| `role` | Enum | Nem | `student` | `student`, `mentor`, `admin` |
| `discord_id` | String | Igen | — | Discord snowflake (17-20 számjegy, unique) |
| `created_at` | DateTime | Igen | `now()` | Első bejelentkezés |
| `last_login` | DateTime | Igen | — | Utolsó bejelentkezés |

### `courses`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `name` | String | Nem | — | Kurzus neve |
| `description` | Text | Igen | — | Leírás |
| `created_at` | DateTime | Igen | `now()` | Létrehozás |

### `modules`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `course_id` | Integer (FK) | Nem | — | → `courses.id` |
| `name` | String | Nem | — | Modul neve |
| `order` | Integer | Igen | `0` | Megjelenítési sorrend |

### `exercises`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `module_id` | Integer (FK) | Nem | — | → `modules.id` |
| `name` | String | Nem | — | Feladat neve |
| `repo_prefix` | String | Igen | — | GitHub Classroom prefix. Tanulók repója: `{prefix}-{username}` |
| `classroom_url` | String | Igen | — | Classroom assignment meghívó link (tanulóknak) |
| `classroom_teacher_url` | String | Igen | — | Teacher dashboard URL (GitHub Classroom, mentoroknak) |
| `order` | Integer | Igen | `0` | Sorrend a modulon belül |
| `required` | Boolean | Nem | `true` | Szükséges-e a tanúsítványhoz |

### `enrollments`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `user_id` | Integer (FK) | Nem | — | → `users.id` |
| `course_id` | Integer (FK) | Nem | — | → `courses.id` |
| `enrolled_at` | DateTime | Igen | `now()` | Beiratkozás ideje |

Duplikáció-ellenőrzés kódban (`409` hiba), nem DB constraint.

### `progress`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `user_id` | Integer (FK) | Nem | — | → `users.id` |
| `exercise_id` | Integer (FK) | Nem | — | → `exercises.id` |
| `github_repo` | String | Igen | — | Repó neve (webhook tölti ki) |
| `status` | Enum | Nem | `not_started` | `not_started`, `in_progress`, `completed` |
| `completed_at` | DateTime | Igen | — | Csak `completed` esetén |

Frissítési források: manuális (`POST /api/me/.../progress`), webhook, sync-progress.

### `certificates`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `cert_id` | String | Nem | `uuid4()` | Publikus UUID, verifikációs URL-ben |
| `user_id` | Integer (FK) | Nem | — | → `users.id` |
| `course_id` | Integer (FK) | Nem | — | → `courses.id` |
| `issued_at` | DateTime | Igen | `now()` | Kiállítás ideje |
| `pdf_path` | String | Igen | — | `data/certificates/{cert_id}.pdf` |

Unique: `cert_id`, `(user_id, course_id)`.

### `promotion_rules`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `name` | String | Nem | — | Szabály neve |
| `description` | String | Igen | — | Leírás |
| `target_role` | Enum | Nem | — | `mentor` / `admin` |
| `is_active` | Boolean | Nem | `true` | Aktív-e |
| `created_at` | DateTime | Igen | `now()` | Létrehozás |

### `promotion_rule_requirements`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `rule_id` | Integer (FK) | Nem | — | → `promotion_rules.id` (CASCADE) |
| `course_id` | Integer (FK) | Nem | — | → `courses.id` |

Unique: `(rule_id, course_id)`. A szabály teljesül, ha a felhasználó minden felsorolt kurzushoz rendelkezik tanúsítvánnyal.

### `promotion_log`

| Oszlop | Típus | Nullable | Default | Leírás |
|--------|-------|----------|---------|--------|
| `id` | Integer | — | autoincrement | PK |
| `user_id` | Integer (FK) | Nem | — | → `users.id` |
| `rule_id` | Integer (FK) | Nem | — | → `promotion_rules.id` |
| `previous_role` | Enum | Nem | — | Korábbi szerepkör |
| `new_role` | Enum | Nem | — | Új szerepkör |
| `promoted_at` | DateTime | Igen | `now()` | Előléptetés ideje |

---

## Kapcsolatok

| Forrás | Cél | FK | Leírás |
|--------|-----|----|--------|
| `modules` | `courses` | `course_id` | Modul → kurzus |
| `exercises` | `modules` | `module_id` | Feladat → modul |
| `enrollments` | `users`, `courses` | `user_id`, `course_id` | Beiratkozás |
| `progress` | `users`, `exercises` | `user_id`, `exercise_id` | Haladás |
| `certificates` | `users`, `courses` | `user_id`, `course_id` | Tanúsítvány |
| `promotion_rule_requirements` | `promotion_rules`, `courses` | `rule_id`, `course_id` | Követelmény |
| `promotion_log` | `users`, `promotion_rules` | `user_id`, `rule_id` | Napló |

## Kaszkád törlés

`DELETE /api/admin/courses/{id}` — alkalmazás kódban, nem DB-szintű CASCADE:

```
Course → Module-ok → Exercise-ek → Progress rekordok
       → Enrollment-ek
       → Certificate-ek
```

## Alembic migrációk

```bash
make migrate                                  # alembic upgrade head
cd backend && alembic revision --autogenerate -m "leírás"   # új migráció
alembic downgrade -1                          # visszagörgetés
```

| Migráció | Leírás |
|----------|--------|
| `5492c9d27e5f` | `users` tábla |
| `38fa8a895630` | `courses`, `modules`, `exercises`, `enrollments`, `progress` |
| `a1b2c3d4e5f6` | `github_token` (deprecated) + `classroom_url` |
| `cefa39428d67` | `certificates` + `required` oszlop |
| `d1e2f3a4b5c6` | `promotion_rules`, `promotion_rule_requirements`, `promotion_log` |
| `e2f3a4b5c6d7` | `discord_id` (`users`, unique) |
| `f4a5b6c7d8e9` | `classroom_teacher_url` (`exercises`) |
