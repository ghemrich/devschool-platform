from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.course import Course, Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/courses")
def my_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List courses the current user is enrolled in, with progress summary."""
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    result = []
    for enrollment in enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        if not course:
            continue

        total, completed = _count_progress(db, current_user.id, course.id)
        result.append(
            {
                "course_id": course.id,
                "course_name": course.name,
                "total_exercises": total,
                "completed_exercises": completed,
                "progress_percent": round(completed / total * 100, 1) if total > 0 else 0,
                "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
            }
        )
    return result


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Dashboard with aggregated progress across all enrolled courses."""
    return my_courses(db=db, current_user=current_user)


@router.get("/courses/{course_id}/progress")
def course_progress(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Detailed progress for a specific course."""
    modules = db.query(Module).filter(Module.course_id == course_id).order_by(Module.order).all()
    result = []
    for module in modules:
        exercises = db.query(Exercise).filter(Exercise.module_id == module.id).order_by(Exercise.order).all()
        ex_list = []
        for exercise in exercises:
            progress = (
                db.query(Progress)
                .filter(Progress.user_id == current_user.id, Progress.exercise_id == exercise.id)
                .first()
            )
            ex_list.append(
                {
                    "id": exercise.id,
                    "name": exercise.name,
                    "status": progress.status.value if progress else "not_started",
                    "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
                }
            )
        result.append({"module_id": module.id, "module_name": module.name, "exercises": ex_list})
    return result


def _count_progress(db: Session, user_id: int, course_id: int) -> tuple[int, int]:
    """Count total and completed exercises for a user in a course."""
    modules = db.query(Module).filter(Module.course_id == course_id).all()
    module_ids = [m.id for m in modules]
    if not module_ids:
        return 0, 0
    total = db.query(Exercise).filter(Exercise.module_id.in_(module_ids)).count()
    completed = (
        db.query(Progress)
        .filter(
            Progress.user_id == user_id,
            Progress.exercise_id.in_(
                db.query(Exercise.id).filter(Exercise.module_id.in_(module_ids))
            ),
            Progress.status == ProgressStatus.completed,
        )
        .count()
    )
    return total, completed
