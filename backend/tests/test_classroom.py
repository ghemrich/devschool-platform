import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.auth.jwt import create_access_token
from app.models.course import Course, Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User, UserRole
from app.services.classroom import AssignmentInfo, ClassroomInfo

TEST_WEBHOOK_SECRET = "test-webhook-secret"


def _signed_webhook_post(client, payload: dict, event: str = "workflow_run"):
    """Send a webhook POST with a valid HMAC-SHA256 signature."""
    body = json.dumps(payload, separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(TEST_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        "/api/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": event,
            "X-Hub-Signature-256": signature,
            "Content-Type": "application/json",
        },
    )


@pytest.fixture
def student(db_session):
    user = User(
        github_id=11111,
        username="student1",
        email="s@example.com",
        role=UserRole.student,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mentor(db_session):
    user = User(github_id=33333, username="mentor1", email="m@example.com", role=UserRole.mentor)
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
def course_with_exercises(db_session):
    course = Course(name="Python 101", description="Beginner Python")
    db_session.add(course)
    db_session.flush()
    module = Module(course_id=course.id, name="Module 1", order=1)
    db_session.add(module)
    db_session.flush()
    ex1 = Exercise(
        module_id=module.id,
        name="Hello World",
        order=1,
        repo_prefix="het01-hello",
        classroom_url="https://classroom.github.com/a/abc123",
    )
    ex2 = Exercise(module_id=module.id, name="Variables", order=2, repo_prefix="het02-variables")
    db_session.add_all([ex1, ex2])
    db_session.commit()
    db_session.refresh(course)
    return course


# --- Classroom URL in exercise creation ---


def test_create_exercise_with_classroom_url(client, admin, db_session):
    course = Course(name="Test", description="desc")
    db_session.add(course)
    db_session.flush()
    module = Module(course_id=course.id, name="Mod 1", order=1)
    db_session.add(module)
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.post(
        f"/api/courses/{course.id}/modules/{module.id}/exercises",
        json={
            "name": "Task 1",
            "repo_prefix": "het01-task1",
            "classroom_url": "https://classroom.github.com/a/xyz789",
            "order": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    ex = db_session.query(Exercise).filter(Exercise.name == "Task 1").first()
    assert ex.classroom_url == "https://classroom.github.com/a/xyz789"


def test_course_detail_includes_classroom_url(client, course_with_exercises):
    response = client.get(f"/api/courses/{course_with_exercises.id}")
    assert response.status_code == 200
    data = response.json()
    exercises = data["modules"][0]["exercises"]
    assert exercises[0]["classroom_url"] == "https://classroom.github.com/a/abc123"
    assert exercises[1]["classroom_url"] == ""


# --- Teacher progress overview ---


def test_students_endpoint_requires_mentor(client, student, course_with_exercises):
    token = create_access_token(student.id)
    response = client.get(
        f"/api/courses/{course_with_exercises.id}/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_students_endpoint_as_mentor(client, mentor, student, db_session, course_with_exercises):
    # Enroll student
    enrollment = Enrollment(user_id=student.id, course_id=course_with_exercises.id)
    db_session.add(enrollment)
    db_session.commit()

    token = create_access_token(mentor.id)
    response = client.get(
        f"/api/courses/{course_with_exercises.id}/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["course_name"] == "Python 101"
    assert len(data["students"]) == 1
    assert data["students"][0]["username"] == "student1"
    assert data["students"][0]["completed_exercises"] == 0


def test_students_shows_progress(client, mentor, student, db_session, course_with_exercises):
    enrollment = Enrollment(user_id=student.id, course_id=course_with_exercises.id)
    db_session.add(enrollment)

    ex = db_session.query(Exercise).filter(Exercise.name == "Hello World").first()
    progress = Progress(user_id=student.id, exercise_id=ex.id, status=ProgressStatus.completed)
    db_session.add(progress)
    db_session.commit()

    token = create_access_token(mentor.id)
    response = client.get(
        f"/api/courses/{course_with_exercises.id}/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert data["students"][0]["completed_exercises"] == 1
    assert data["students"][0]["progress_percent"] == 50.0


# --- Student exercise details with Classroom links ---


def test_student_exercises_requires_mentor(client, student, course_with_exercises):
    token = create_access_token(student.id)
    response = client.get(
        f"/api/courses/{course_with_exercises.id}/students/{student.id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_student_exercises_not_found_course(client, mentor):
    token = create_access_token(mentor.id)
    response = client.get(
        "/api/courses/999/students/1/exercises",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_student_exercises_not_found_user(client, mentor, course_with_exercises):
    token = create_access_token(mentor.id)
    response = client.get(
        f"/api/courses/{course_with_exercises.id}/students/999/exercises",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_student_exercises_returns_classroom_urls(client, mentor, student, db_session, course_with_exercises):
    enrollment = Enrollment(user_id=student.id, course_id=course_with_exercises.id)
    db_session.add(enrollment)

    ex = db_session.query(Exercise).filter(Exercise.name == "Hello World").first()
    progress = Progress(user_id=student.id, exercise_id=ex.id, status=ProgressStatus.completed)
    db_session.add(progress)
    db_session.commit()

    token = create_access_token(mentor.id)
    response = client.get(
        f"/api/courses/{course_with_exercises.id}/students/{student.id}/exercises",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["course_name"] == "Python 101"
    assert data["username"] == "student1"
    assert len(data["modules"]) == 1

    mod = data["modules"][0]
    assert mod["module_name"] == "Module 1"
    assert len(mod["exercises"]) == 2

    # First exercise has classroom_url (invite link) and is completed
    # Mentor endpoint returns teacher URL (classroom_teacher_url) if available, otherwise invite link
    ex1 = mod["exercises"][0]
    assert ex1["name"] == "Hello World"
    assert ex1["status"] == "completed"
    assert ex1["classroom_url"] == "https://classroom.github.com/a/abc123"

    # Second exercise has no classroom_url and is not started
    ex2 = mod["exercises"][1]
    assert ex2["name"] == "Variables"
    assert ex2["status"] == "not_started"
    assert ex2["classroom_url"] is None


# --- GitHub webhook ---


def test_webhook_ignores_non_workflow(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.github_webhook_secret", TEST_WEBHOOK_SECRET)
    payload = {"action": "push"}
    response = _signed_webhook_post(client, payload, event="push")
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_ignores_failed_runs(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.github_webhook_secret", TEST_WEBHOOK_SECRET)
    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "failure"},
        "repository": {"name": "het01-hello-student1"},
    }
    response = _signed_webhook_post(client, payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_updates_progress(client, db_session, student, course_with_exercises, monkeypatch):
    monkeypatch.setattr("app.config.settings.github_webhook_secret", TEST_WEBHOOK_SECRET)
    enrollment = Enrollment(user_id=student.id, course_id=course_with_exercises.id)
    db_session.add(enrollment)
    db_session.commit()

    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "success"},
        "repository": {"name": "het01-hello-student1"},
    }
    response = _signed_webhook_post(client, payload)
    assert response.status_code == 200
    assert response.json()["updated"] is True

    ex = db_session.query(Exercise).filter(Exercise.name == "Hello World").first()
    progress = db_session.query(Progress).filter(Progress.user_id == student.id, Progress.exercise_id == ex.id).first()
    assert progress is not None
    assert progress.status == ProgressStatus.completed


def test_webhook_no_duplicate_update(client, db_session, student, course_with_exercises, monkeypatch):
    monkeypatch.setattr("app.config.settings.github_webhook_secret", TEST_WEBHOOK_SECRET)
    enrollment = Enrollment(user_id=student.id, course_id=course_with_exercises.id)
    db_session.add(enrollment)

    ex = db_session.query(Exercise).filter(Exercise.name == "Hello World").first()
    progress = Progress(user_id=student.id, exercise_id=ex.id, status=ProgressStatus.completed)
    db_session.add(progress)
    db_session.commit()

    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "success"},
        "repository": {"name": "het01-hello-student1"},
    }
    response = _signed_webhook_post(client, payload)
    assert response.status_code == 200
    assert response.json()["updated"] is False


# --- Classroom import API ---


MOCK_CLASSROOMS = [
    ClassroomInfo(id=1, name="Python Course", url="https://classroom.github.com/classrooms/1"),
    ClassroomInfo(id=2, name="Web Dev", url="https://classroom.github.com/classrooms/2"),
]

MOCK_ASSIGNMENTS = [
    AssignmentInfo(
        id=10,
        title="Hello World",
        slug="het01-hello",
        invite_link="https://classroom.github.com/a/abc123",
        classroom_id=1,
    ),
    AssignmentInfo(
        id=11, title="Loops", slug="het03-loops", invite_link="https://classroom.github.com/a/def456", classroom_id=1
    ),
]


def test_list_classrooms_requires_admin(client, student):
    token = create_access_token(student.id)
    response = client.get("/api/courses/classroom/classrooms", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@patch("app.routers.courses.list_classrooms", new_callable=AsyncMock, return_value=MOCK_CLASSROOMS)
def test_list_classrooms(mock_lc, client, admin, monkeypatch):
    monkeypatch.setattr("app.config.settings.github_org_admin_token", "test-token")
    token = create_access_token(admin.id)
    response = client.get("/api/courses/classroom/classrooms", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["name"] == "Python Course"
    mock_lc.assert_called_once_with("test-token")


@patch("app.routers.courses.list_assignments", new_callable=AsyncMock, return_value=MOCK_ASSIGNMENTS)
def test_list_assignments_marks_imported(mock_la, client, admin, db_session, course_with_exercises, monkeypatch):
    monkeypatch.setattr("app.config.settings.github_org_admin_token", "test-token")
    token = create_access_token(admin.id)
    response = client.get(
        "/api/courses/classroom/classrooms/1/assignments", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    # "het01-hello" already exists in the course_with_exercises fixture
    assert data[0]["already_imported"] is True
    assert data[1]["already_imported"] is False


def test_import_exercises(client, admin, db_session):
    course = Course(name="Import Test", description="")
    db_session.add(course)
    db_session.flush()
    module = Module(course_id=course.id, name="Mod 1", order=1)
    db_session.add(module)
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.post(
        f"/api/courses/{course.id}/modules/{module.id}/import-classroom",
        json={
            "exercises": [
                {
                    "title": "Loops",
                    "slug": "het03-loops",
                    "invite_link": "https://classroom.github.com/a/def456",
                    "classroom_url": "https://classroom.github.com/classrooms/123-test",
                },
                {
                    "title": "Functions",
                    "slug": "het04-funcs",
                    "invite_link": "https://classroom.github.com/a/ghi789",
                    "classroom_url": "https://classroom.github.com/classrooms/123-test",
                },
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    result = response.json()
    assert len(result["imported"]) == 2
    assert len(result["skipped"]) == 0

    exercises = db_session.query(Exercise).filter(Exercise.module_id == module.id).order_by(Exercise.order).all()
    assert len(exercises) == 2
    assert exercises[0].name == "Loops"
    assert exercises[0].repo_prefix == "het03-loops"
    assert exercises[0].classroom_url == "https://classroom.github.com/a/def456"
    assert (
        exercises[0].classroom_teacher_url == "https://classroom.github.com/classrooms/123-test/assignments/het03-loops"
    )
    assert exercises[1].classroom_url == "https://classroom.github.com/a/ghi789"
    assert (
        exercises[1].classroom_teacher_url == "https://classroom.github.com/classrooms/123-test/assignments/het04-funcs"
    )


def test_import_skips_duplicates(client, admin, db_session, course_with_exercises):
    module = db_session.query(Module).filter(Module.course_id == course_with_exercises.id).first()
    token = create_access_token(admin.id)
    response = client.post(
        f"/api/courses/{course_with_exercises.id}/modules/{module.id}/import-classroom",
        json={
            "exercises": [
                {
                    "title": "Hello World Again",
                    "slug": "het01-hello",
                    "invite_link": "https://classroom.github.com/a/dup",
                },
                {"title": "New Exercise", "slug": "het05-new", "invite_link": "https://classroom.github.com/a/new123"},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["imported"] == ["New Exercise"]
    assert result["skipped"] == ["Hello World Again"]
    assert result["updated"] == []


def test_reimport_backfills_teacher_url(client, admin, db_session, course_with_exercises):
    """Re-importing with classroom_url backfills classroom_teacher_url."""
    module = db_session.query(Module).filter(Module.course_id == course_with_exercises.id).first()
    # Verify existing exercises have no teacher URL
    ex = db_session.query(Exercise).filter(Exercise.repo_prefix == "het01-hello").first()
    assert ex.classroom_teacher_url is None

    token = create_access_token(admin.id)
    response = client.post(
        f"/api/courses/{course_with_exercises.id}/modules/{module.id}/import-classroom",
        json={
            "exercises": [
                {
                    "title": "Hello World",
                    "slug": "het01-hello",
                    "invite_link": "https://classroom.github.com/a/abc123",
                    "classroom_url": "https://classroom.github.com/classrooms/123-test",
                },
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    result = response.json()
    assert result["imported"] == []
    assert result["updated"] == ["Hello World"]
    assert result["skipped"] == []

    db_session.refresh(ex)
    assert ex.classroom_teacher_url == "https://classroom.github.com/classrooms/123-test/assignments/het01-hello"
