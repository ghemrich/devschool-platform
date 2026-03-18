from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.course import Course, Enrollment, Exercise, Module
from app.models.user import User, UserRole
from app.services.discord import notify_enrollment
from app.services.progress import count_progress

router = APIRouter(prefix="/api/courses", tags=["courses"])


# --- Pydantic schemas ---


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)


class ModuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    order: int = Field(default=0, ge=0)


class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    repo_prefix: str = Field(default="", max_length=200)
    classroom_url: str = Field(default="", max_length=500)
    order: int = Field(default=0, ge=0)
    required: bool = True


# --- Public endpoints ---


@router.get("")
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List courses with pagination (public)."""
    total = db.query(Course).count()
    courses = db.query(Course).order_by(Course.created_at.asc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ],
    }


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get course details with modules and exercises (public)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "modules": [
            {
                "id": m.id,
                "name": m.name,
                "order": m.order,
                "exercises": [
                    {
                        "id": e.id,
                        "name": e.name,
                        "repo_prefix": e.repo_prefix,
                        "classroom_url": e.classroom_url or "",
                        "order": e.order,
                    }
                    for e in m.exercises
                ],
            }
            for m in course.modules
        ],
    }


# --- Admin endpoints ---


@router.post("", status_code=201)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    course = Course(name=data.name, description=data.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return {"id": course.id, "name": course.name}


@router.put("/{course_id}")
def update_course(
    course_id: int,
    data: CourseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.name = data.name
    course.description = data.description
    db.commit()
    return {"id": course.id, "name": course.name}


@router.post("/{course_id}/modules", status_code=201)
def add_module(
    course_id: int,
    data: ModuleCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    module = Module(course_id=course_id, name=data.name, order=data.order)
    db.add(module)
    db.commit()
    db.refresh(module)
    return {"id": module.id, "name": module.name}


@router.post("/{course_id}/modules/{module_id}/exercises", status_code=201)
def add_exercise(
    course_id: int,
    module_id: int,
    data: ExerciseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    module = db.query(Module).filter(Module.id == module_id, Module.course_id == course_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    exercise = Exercise(
        module_id=module_id,
        name=data.name,
        repo_prefix=data.repo_prefix,
        classroom_url=data.classroom_url,
        order=data.order,
        required=data.required,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return {"id": exercise.id, "name": exercise.name}


# --- Enrollment ---


@router.post("/{course_id}/enroll", status_code=201)
def enroll(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = (
        db.query(Enrollment).filter(Enrollment.user_id == current_user.id, Enrollment.course_id == course_id).first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.add(enrollment)
    db.commit()

    notify_enrollment(current_user.username, course.name)

    return {"detail": "Enrolled successfully"}


@router.post("/{course_id}/unenroll")
def unenroll(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enrollment = (
        db.query(Enrollment).filter(Enrollment.user_id == current_user.id, Enrollment.course_id == course_id).first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled")
    db.delete(enrollment)
    db.commit()
    return {"detail": "Unenrolled successfully"}


# --- Teacher / Admin endpoints ---


@router.get("/{course_id}/students")
def course_students(
    course_id: int,
    db: Session = Depends(get_db),
    _teacher: User = Depends(require_role(UserRole.mentor)),
):
    """List all enrolled students with their progress (mentor/admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollments = (
        db.query(Enrollment).filter(Enrollment.course_id == course_id).options(joinedload(Enrollment.user)).all()
    )
    result = []
    for enrollment in enrollments:
        user = enrollment.user
        if not user:
            continue

        total, completed = count_progress(db, user.id, course_id)

        result.append(
            {
                "user_id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "total_exercises": total,
                "completed_exercises": completed,
                "progress_percent": round(completed / total * 100, 1) if total > 0 else 0,
                "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
            }
        )

    return {"course_name": course.name, "students": result}
