import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth.jwt import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models.course import Course, Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User, UserRole

SQLALCHEMY_TEST_URL = "sqlite:///./test_courses.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


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


@pytest.fixture
def student(db_session):
    user = User(github_id=11111, username="student1", email="s@example.com", role=UserRole.student)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin(db_session):
    user = User(github_id=22222, username="admin1", email="a@example.com", role=UserRole.admin)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_course(db_session):
    course = Course(name="Python 101", description="Beginner Python")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


# --- Courses CRUD ---


def test_list_courses_public(client, sample_course):
    response = client.get("/api/courses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Python 101"


def test_create_course_requires_admin(client, student):
    token = create_access_token(student.id)
    response = client.post("/api/courses", json={"name": "X"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_create_course_as_admin(client, admin):
    token = create_access_token(admin.id)
    response = client.post(
        "/api/courses", json={"name": "New Course", "description": "Desc"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "New Course"


def test_get_course_detail(client, db_session, sample_course):
    mod = Module(course_id=sample_course.id, name="Mod 1", order=1)
    db_session.add(mod)
    db_session.commit()
    db_session.refresh(mod)
    ex = Exercise(module_id=mod.id, name="Ex 1", order=1)
    db_session.add(ex)
    db_session.commit()

    response = client.get(f"/api/courses/{sample_course.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Python 101"
    assert len(data["modules"]) == 1
    assert len(data["modules"][0]["exercises"]) == 1


def test_course_not_found(client):
    response = client.get("/api/courses/999")
    assert response.status_code == 404


# --- Enrollment ---


def test_enroll_requires_auth(client):
    response = client.post("/api/courses/1/enroll")
    assert response.status_code in (401, 403)


def test_enroll_success(client, student, sample_course):
    token = create_access_token(student.id)
    response = client.post(f"/api/courses/{sample_course.id}/enroll", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201


def test_enroll_duplicate(client, student, sample_course):
    token = create_access_token(student.id)
    client.post(f"/api/courses/{sample_course.id}/enroll", headers={"Authorization": f"Bearer {token}"})
    response = client.post(f"/api/courses/{sample_course.id}/enroll", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409


def test_unenroll(client, student, sample_course):
    token = create_access_token(student.id)
    client.post(f"/api/courses/{sample_course.id}/enroll", headers={"Authorization": f"Bearer {token}"})
    response = client.post(f"/api/courses/{sample_course.id}/unenroll", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


# --- Dashboard ---


def test_dashboard_requires_auth(client):
    response = client.get("/api/me/dashboard")
    assert response.status_code in (401, 403)


def test_my_courses_requires_auth(client):
    response = client.get("/api/me/courses")
    assert response.status_code in (401, 403)


def test_dashboard_with_progress(client, db_session, student, sample_course):
    # Setup: module, exercise, enrollment, progress
    mod = Module(course_id=sample_course.id, name="M1", order=1)
    db_session.add(mod)
    db_session.commit()
    db_session.refresh(mod)

    ex1 = Exercise(module_id=mod.id, name="E1", order=1)
    ex2 = Exercise(module_id=mod.id, name="E2", order=2)
    db_session.add_all([ex1, ex2])
    db_session.commit()
    db_session.refresh(ex1)
    db_session.refresh(ex2)

    enrollment = Enrollment(user_id=student.id, course_id=sample_course.id)
    db_session.add(enrollment)
    db_session.commit()

    progress = Progress(user_id=student.id, exercise_id=ex1.id, status=ProgressStatus.completed)
    db_session.add(progress)
    db_session.commit()

    token = create_access_token(student.id)
    response = client.get("/api/me/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["total_exercises"] == 2
    assert data[0]["completed_exercises"] == 1
    assert data[0]["progress_percent"] == 50.0


# --- Services ---


def test_github_service_importable():
    from app.services.github import check_exercise_status

    assert callable(check_exercise_status)


def test_progress_service_importable():
    from app.services.progress import update_progress_for_user

    assert callable(update_progress_for_user)
