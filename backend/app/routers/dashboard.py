from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.models.course import Course, Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User
from app.services.progress import count_progress, update_progress_for_user

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

        total, completed = count_progress(db, current_user.id, course.id)
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
def course_progress(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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


class ProgressUpdate(BaseModel):
    exercise_id: int
    status: str = "completed"


@router.post("/courses/{course_id}/progress")
def update_exercise_progress(
    course_id: int,
    data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an exercise as completed (or in_progress)."""
    # Verify enrollment
    enrollment = (
        db.query(Enrollment).filter(Enrollment.user_id == current_user.id, Enrollment.course_id == course_id).first()
    )
    if not enrollment:
        raise HTTPException(status_code=400, detail="Not enrolled in this course")

    # Verify exercise belongs to course
    exercise = db.query(Exercise).filter(Exercise.id == data.exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    module = db.query(Module).filter(Module.id == exercise.module_id, Module.course_id == course_id).first()
    if not module:
        raise HTTPException(status_code=400, detail="Exercise does not belong to this course")

    # Create or update progress
    progress = (
        db.query(Progress).filter(Progress.user_id == current_user.id, Progress.exercise_id == data.exercise_id).first()
    )

    status_value = ProgressStatus.completed if data.status == "completed" else ProgressStatus.in_progress

    if progress:
        progress.status = status_value
        if status_value == ProgressStatus.completed:
            progress.completed_at = datetime.now(timezone.utc)
    else:
        progress = Progress(
            user_id=current_user.id,
            exercise_id=data.exercise_id,
            status=status_value,
            completed_at=datetime.now(timezone.utc) if status_value == ProgressStatus.completed else None,
        )
        db.add(progress)

    db.commit()
    return {"status": "ok", "exercise_id": data.exercise_id, "progress": status_value.value}


@router.post("/sync-progress")
async def sync_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Sync progress from GitHub CI status for all enrolled exercises."""
    if not current_user.github_token:
        raise HTTPException(status_code=400, detail="No GitHub token — please log in again")

    owner = settings.github_org or current_user.username
    await update_progress_for_user(db, current_user, current_user.github_token, owner)

    return my_courses(db=db, current_user=current_user)
