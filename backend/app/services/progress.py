from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.course import Enrollment, Exercise, Module, Progress, ProgressStatus
from app.models.user import User
from app.services.github import check_exercise_status


def count_progress(db: Session, user_id: int, course_id: int) -> tuple[int, int]:
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
            Progress.exercise_id.in_(db.query(Exercise.id).filter(Exercise.module_id.in_(module_ids))),
            Progress.status == ProgressStatus.completed,
        )
        .count()
    )
    return total, completed


async def update_progress_for_user(db: Session, user: User, github_token: str, owner: str = "openschool-org"):
    """Check GitHub CI status for all enrolled exercises and update progress."""
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user.id).all()

    for enrollment in enrollments:
        modules = db.query(Module).filter(Module.course_id == enrollment.course_id).all()
        for module in modules:
            exercises = db.query(Exercise).filter(Exercise.module_id == module.id).all()
            for exercise in exercises:
                if not exercise.repo_prefix:
                    continue

                repo_name = f"{exercise.repo_prefix}-{user.username}"
                is_completed = await check_exercise_status(
                    owner=owner,
                    repo_name=repo_name,
                    github_token=github_token,
                )

                progress = (
                    db.query(Progress).filter(Progress.user_id == user.id, Progress.exercise_id == exercise.id).first()
                )

                if progress is None:
                    progress = Progress(
                        user_id=user.id,
                        exercise_id=exercise.id,
                        github_repo=repo_name,
                        status=ProgressStatus.completed if is_completed else ProgressStatus.not_started,
                        completed_at=datetime.now(timezone.utc) if is_completed else None,
                    )
                    db.add(progress)
                elif is_completed and progress.status != ProgressStatus.completed:
                    progress.status = ProgressStatus.completed
                    progress.completed_at = datetime.now(timezone.utc)

    db.commit()
