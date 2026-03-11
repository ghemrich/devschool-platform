import pytest

from app.auth.jwt import create_access_token
from app.models.course import Course, Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User, UserRole


@pytest.fixture
def student(db_session):
    user = User(
        github_id=11111,
        username="student1",
        email="s@example.com",
        role=UserRole.student,
        github_token="ghp_fake_token",
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


# --- GitHub webhook ---


def test_webhook_ignores_non_workflow(client):
    response = client.post(
        "/api/webhooks/github",
        json={"action": "push"},
        headers={"X-GitHub-Event": "push"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_ignores_failed_runs(client):
    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "failure"},
        "repository": {"name": "het01-hello-student1"},
    }
    response = client.post(
        "/api/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "workflow_run"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_updates_progress(client, db_session, student, course_with_exercises):
    enrollment = Enrollment(user_id=student.id, course_id=course_with_exercises.id)
    db_session.add(enrollment)
    db_session.commit()

    payload = {
        "action": "completed",
        "workflow_run": {"conclusion": "success"},
        "repository": {"name": "het01-hello-student1"},
    }
    response = client.post(
        "/api/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "workflow_run"},
    )
    assert response.status_code == 200
    assert response.json()["updated"] is True

    ex = db_session.query(Exercise).filter(Exercise.name == "Hello World").first()
    progress = db_session.query(Progress).filter(Progress.user_id == student.id, Progress.exercise_id == ex.id).first()
    assert progress is not None
    assert progress.status == ProgressStatus.completed


def test_webhook_no_duplicate_update(client, db_session, student, course_with_exercises):
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
    response = client.post(
        "/api/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "workflow_run"},
    )
    assert response.status_code == 200
    assert response.json()["updated"] is False
