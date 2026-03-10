from unittest.mock import MagicMock, patch

from app.auth.jwt import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models.certificate import Certificate
from app.models.course import Course, Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User, UserRole
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest

SQLALCHEMY_TEST_URL = "sqlite:///./test_certificates.db"
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
    user = User(github_id=33333, username="certuser", email="cert@example.com", role=UserRole.student)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def completed_course(db_session, student):
    """Create a course with all required exercises completed by the student."""
    course = Course(name="Test Course", description="For cert testing")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    mod = Module(course_id=course.id, name="Module 1", order=1)
    db_session.add(mod)
    db_session.commit()
    db_session.refresh(mod)

    ex1 = Exercise(module_id=mod.id, name="Ex 1", order=1, required=True)
    ex2 = Exercise(module_id=mod.id, name="Ex 2", order=2, required=True)
    ex3 = Exercise(module_id=mod.id, name="Ex Optional", order=3, required=False)
    db_session.add_all([ex1, ex2, ex3])
    db_session.commit()
    db_session.refresh(ex1)
    db_session.refresh(ex2)

    enrollment = Enrollment(user_id=student.id, course_id=course.id)
    db_session.add(enrollment)

    p1 = Progress(user_id=student.id, exercise_id=ex1.id, status=ProgressStatus.completed)
    p2 = Progress(user_id=student.id, exercise_id=ex2.id, status=ProgressStatus.completed)
    db_session.add_all([p1, p2])
    db_session.commit()

    return course


@pytest.fixture
def incomplete_course(db_session, student):
    """Create a course with not all exercises completed."""
    course = Course(name="Incomplete Course", description="Not done")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    mod = Module(course_id=course.id, name="Module 1", order=1)
    db_session.add(mod)
    db_session.commit()
    db_session.refresh(mod)

    ex1 = Exercise(module_id=mod.id, name="Ex 1", order=1, required=True)
    ex2 = Exercise(module_id=mod.id, name="Ex 2", order=2, required=True)
    db_session.add_all([ex1, ex2])
    db_session.commit()
    db_session.refresh(ex1)

    enrollment = Enrollment(user_id=student.id, course_id=course.id)
    p1 = Progress(user_id=student.id, exercise_id=ex1.id, status=ProgressStatus.completed)
    db_session.add_all([enrollment, p1])
    db_session.commit()

    return course


# --- Completion logic ---


def test_is_course_completed_true(db_session, student, completed_course):
    from app.services.certificate import is_course_completed

    assert is_course_completed(db_session, student.id, completed_course.id) is True


def test_is_course_completed_false(db_session, student, incomplete_course):
    from app.services.certificate import is_course_completed

    assert is_course_completed(db_session, student.id, incomplete_course.id) is False


def test_is_course_completed_no_exercises(db_session, student):
    from app.services.certificate import is_course_completed

    course = Course(name="Empty", description="No exercises")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    assert is_course_completed(db_session, student.id, course.id) is False


# --- Certificate request ---


def test_request_certificate_requires_auth(client):
    response = client.post("/api/me/courses/1/certificate")
    assert response.status_code in (401, 403)


def test_request_certificate_incomplete_course(client, student, incomplete_course):
    token = create_access_token(student.id)
    response = client.post(
        f"/api/me/courses/{incomplete_course.id}/certificate", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_request_certificate_success(client, student, completed_course):
    token = create_access_token(student.id)
    with patch("app.services.pdf.generate_certificate_pdf", return_value=b"%PDF-fake"):
        with patch("app.services.qr.generate_qr_base64", return_value="fakebase64"):
            response = client.post(
                f"/api/me/courses/{completed_course.id}/certificate",
                headers={"Authorization": f"Bearer {token}"},
            )
    assert response.status_code == 201
    data = response.json()
    assert "cert_id" in data


def test_request_certificate_duplicate(client, db_session, student, completed_course):
    token = create_access_token(student.id)
    with patch("app.services.pdf.generate_certificate_pdf", return_value=b"%PDF-fake"):
        with patch("app.services.qr.generate_qr_base64", return_value="fakebase64"):
            client.post(
                f"/api/me/courses/{completed_course.id}/certificate",
                headers={"Authorization": f"Bearer {token}"},
            )
            response = client.post(
                f"/api/me/courses/{completed_course.id}/certificate",
                headers={"Authorization": f"Bearer {token}"},
            )
    assert response.status_code == 409


# --- My certificates ---


def test_my_certificates_requires_auth(client):
    response = client.get("/api/me/certificates")
    assert response.status_code in (401, 403)


def test_my_certificates_returns_list(client, db_session, student, completed_course):
    cert = Certificate(user_id=student.id, course_id=completed_course.id)
    db_session.add(cert)
    db_session.commit()

    token = create_access_token(student.id)
    response = client.get("/api/me/certificates", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


# --- Verification ---


def test_verify_nonexistent_returns_404(client):
    response = client.get("/api/verify/nonexistent-id")
    assert response.status_code == 404


def test_verify_valid_certificate(client, db_session, student, completed_course):
    cert = Certificate(user_id=student.id, course_id=completed_course.id)
    db_session.add(cert)
    db_session.commit()
    db_session.refresh(cert)

    response = client.get(f"/api/verify/{cert.cert_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["name"] == "certuser"
    assert data["course"] == "Test Course"


# --- QR module ---


def test_qr_module_importable():
    from app.services.qr import generate_qr_base64

    assert callable(generate_qr_base64)


def test_qr_generates_base64():
    from app.services.qr import generate_qr_base64

    result = generate_qr_base64("https://example.com/verify/test")
    assert isinstance(result, str)
    assert len(result) > 100  # Base64 PNG should be reasonably long
