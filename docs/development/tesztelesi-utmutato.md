# OpenSchool Platform — Tesztelési útmutató

> 📖 **Dokumentáció:** [Főoldal](../../README.md) · [Architektúra](../getting-started/architektura.md) · [Telepítés](../getting-started/telepitesi-utmutato.md) · [Környezeti változók](../getting-started/kornyezeti-valtozok.md) · [Fejlesztői útmutató](fejlesztoi-utmutato.md) · [Backend](backend-fejlesztes.md) · [Frontend](frontend-fejlesztes.md) · **Tesztelés** · [API referencia](../reference/api-referencia.md) · [Adatbázis](../reference/adatbazis-sema.md) · [Karbantartás](../operations/karbantartas-utmutato.md) · [Automatizálás](../operations/automatizalas-beallitas.md) · [GitHub Classroom](../integrations/github-classroom-integraciot.md) · [Discord](../integrations/discord-integracio.md) · [Felhasználói útmutató](../guides/felhasznaloi-utmutato.md) · [Dokumentálás](../guides/dokumentacios-utmutato.md) · [Roadmap](../jovokep-es-fejlesztesi-terv.md) · [Hozzájárulás](../../CONTRIBUTING.md)

Ez az útmutató a projekt tesztelési rendszerét, a tesztek futtatását és új tesztek írását mutatja be.

---

## 1. Áttekintés

A projektben **két különálló tesztcsomag** van:

| Csomag | Hely | Cél | Futtatás |
|--------|------|-----|----------|
| **Backend unit tesztek** | `backend/tests/` | API végpontok, üzleti logika, modellek | `make test` |
| **Verifikációs tesztek** | `tesztek/` | Diákok projektjének ellenőrzése (labor feladatok) | `pytest tesztek/modul-01/ -v` |

### Backend tesztek (56 db)

| Fájl | Tesztek | Mit tesztel |
|------|---------|-------------|
| `test_auth.py` | 8 | GitHub OAuth flow, JWT tokenek, refresh, logout |
| `test_courses.py` | 14 | Kurzus CRUD, modul/feladat hozzáadás, beiratkozás, leiratkozás |
| `test_certificates.py` | 12 | Tanúsítvány igénylés, PDF letöltés, verifikáció, duplikáció |
| `test_classroom.py` | 9 | GitHub Classroom webhook, repo_prefix egyeztetés |
| `test_admin.py` | 11 | Admin statisztikák, felhasználó kezelés, kaszkád törlés |
| `test_health.py` | 1+ | Health check végpont |

### Verifikációs tesztek (7 modul)

Ezek a `tesztek/` mappában találhatók és a diákok projektjének helyességét ellenőrzik — fájlok megléte, Docker futás, API válaszok, stb. A tanár/mentor futtatja vagy a CI pipeline.

| Modul | Mit ellenőriz |
|-------|---------------|
| `modul-01/` | Alembic, Docker, health check |
| `modul-02/` | Auth flow, védett végpontok, szerepkörök |
| `modul-03/` | Kurzusok, haladás |
| `modul-04/` | Tanúsítvány befejezés, verifikáció |
| `modul-05/` | Frontend oldalak |
| `modul-06/` | Éles konfiguráció |
| `modul-07/` | Közösségi fájlok (README, CONTRIBUTING, stb.) |

---

## 2. Tesztek futtatása

### Backend tesztek

```bash
# Teljes tesztcsomag (javasolt)
make test

# Közvetlenül pytest-tel
cd backend
pytest -v

# Egy fájl futtatása
pytest tests/test_auth.py -v

# Egy teszt futtatása
pytest tests/test_auth.py::test_login_redirect -v

# Teszt lefedettséggel (ha pytest-cov telepítve)
pytest --cov=app tests/ -v
```

### Verifikációs tesztek

```bash
# Egy modul futtatása
pytest tesztek/modul-01/ -v

# Összes verifikációs teszt
pytest tesztek/ -v
```

### CI-ben

A GitHub Actions CI workflow (`ci.yml`) automatikusan futtatja a backend teszteket minden push-ra és PR-re:

```yaml
- name: Run tests
  run: |
    cd backend
    pytest -v
```

---

## 3. Teszt adatbázis és izoláció

### SQLite teszt adatbázis

A backend tesztek **SQLite-ot használnak** (nem PostgreSQL-t), hogy gyorsak legyenek és ne kelljen Docker:

```python
# backend/tests/conftest.py
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
```

### Automatikus tisztítás

Az `autouse=True` fixture **minden teszt előtt újra létrehozza** és **utána törli** a teljes adatbázis sémát:

```python
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
```

Ez biztosítja, hogy minden teszt tiszta, üres adatbázissal indul — a tesztek **nem függenek egymástól**.

### FastAPI TestClient

A `client` fixture a FastAPI alkalmazást a teszt adatbázisra irányítja:

```python
@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

---

## 4. Fixture-ök

A `conftest.py` előre definiált felhasználókat biztosít a tesztekhez:

### Felhasználó fixture-ök

| Fixture | Szerepkör | GitHub ID | Username |
|---------|-----------|-----------|----------|
| `student` | `student` | 11111 | `student1` |
| `admin` | `admin` | 22222 | `admin1` |
| `mentor` | `mentor` | 33333 | `mentor1` |

**Használat:**

```python
def test_admin_stats(client, admin, db_session):
    # Az admin fixture automatikusan létrehoz egy admin felhasználót az adatbázisban
    # A client fixture a teszt adatbázist használja
    ...
```

### Hitelesítés tesztekben

A tesztek JWT tokent generálnak a fixture felhasználókhoz:

```python
from app.auth.jwt import create_access_token

def test_protected_endpoint(client, student):
    token = create_access_token(student.id)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "student1"
```

### Kurzus és adatok létrehozása

Tesztekben közvetlenül a `db_session`-nel hozd létre a szükséges adatokat:

```python
from app.models.course import Course, Module, Exercise, Enrollment

def test_course_progress(client, student, db_session):
    # Kurzus + modul + feladat létrehozása
    course = Course(name="Test Course")
    db_session.add(course)
    db_session.commit()

    module = Module(course_id=course.id, name="Module 1", order=1)
    db_session.add(module)
    db_session.commit()

    exercise = Exercise(module_id=module.id, name="Exercise 1", order=1)
    db_session.add(exercise)
    db_session.commit()

    # Beiratkozás
    enrollment = Enrollment(user_id=student.id, course_id=course.id)
    db_session.add(enrollment)
    db_session.commit()

    # API hívás
    token = create_access_token(student.id)
    response = client.get(
        f"/api/me/courses/{course.id}/progress",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

## 5. Új teszt írása

### Fájl elnevezés

- Fájlnév: `test_<funkció>.py` (pl. `test_notifications.py`)
- Tesztfüggvény: `test_<mit_tesztel>` (pl. `test_enroll_duplicate_returns_409`)

### Sablon

```python
"""Modul leírása — mit tesztelünk."""

from app.auth.jwt import create_access_token
from app.models.course import Course


def test_publikus_vegpont(client):
    """Publikus végpont — nem kell hitelesítés."""
    response = client.get("/api/courses")
    assert response.status_code == 200


def test_vedett_vegpont_hitelesites_nelkul(client):
    """Védett végpont hitelesítés nélkül — 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_vedett_vegpont_tokennel(client, student):
    """Védett végpont érvényes tokennel."""
    token = create_access_token(student.id)
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "student"


def test_admin_vegpont_diak_nem_ferhet_hozza(client, student):
    """Admin végpont — a diák nem érheti el (403 vagy 401)."""
    token = create_access_token(student.id)
    response = client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in (401, 403)


def test_admin_vegpont_adminnal(client, admin, db_session):
    """Admin végpont — admin felhasználóval működik."""
    token = create_access_token(admin.id)
    response = client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_nem_letezo_eroforras(client):
    """404 válasz nem létező erőforrásra."""
    response = client.get("/api/courses/99999")
    assert response.status_code == 404
```

### Tipp-ek

- Minden tesztet **egy dolgot** teszteljen
- A tesztnév legyen **leíró** — a kimenetből látszódjon, mi hibás
- Használd a kész fixture-öket (`student`, `admin`, `mentor`, `client`, `db_session`)
- Ne függj más tesztek eredményétől — a `setup_db` fixture minden tesztre tiszta DB-t ad

---

## 6. Tesztkonfiguráció

### `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

A pytest a `backend/tests/` mappából indul. A `backend/` könyvtárban kell futtatni.

### Ruff lint a tesztekről

A Ruff automatikusan linteli a tesztfájlokat is. A `B008` szabály ki van kapcsolva (`ignore = ["B008"]`), mert a FastAPI `Depends()` default value mintát használ.

---

## 7. CI integráció

A GitHub Actions CI workflow minden push-ra és PR-re automatikusan:

1. Python 3.12 környezet felállítása
2. Függőségek telepítése (`requirements-dev.txt`)
3. Ruff lint futtatása
4. `pytest -v` futtatása
5. Discord értesítés küldése (ha `DISCORD_WEBHOOK_CI` secret be van állítva)

Ha a tesztek elbuknak, a PR nem merge-elhető.
