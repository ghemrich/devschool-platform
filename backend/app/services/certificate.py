from sqlalchemy.orm import Session

from app.models.course import Exercise, Module, Progress, ProgressStatus


def is_course_completed(db: Session, user_id: int, course_id: int) -> bool:
    """Check if a user has completed all required exercises in a course."""
    total = (
        db.query(Exercise)
        .join(Module)
        .filter(
            Module.course_id == course_id,
            Exercise.required.is_(True),
        )
        .count()
    )

    completed = (
        db.query(Progress)
        .join(Exercise)
        .join(Module)
        .filter(
            Module.course_id == course_id,
            Progress.user_id == user_id,
            Progress.status == ProgressStatus.completed,
            Exercise.required.is_(True),
        )
        .count()
    )

    return total > 0 and total == completed
