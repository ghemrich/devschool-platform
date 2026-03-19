from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.certificate import Certificate
from app.models.course import Course, Enrollment, Exercise, Module, Progress
from app.models.promotion import PromotionLog, PromotionRule, PromotionRuleRequirement
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/admin", tags=["admin"])

USERS_SORT_COLUMNS = {"created_at": User.created_at, "username": User.username, "role": User.role}


# --- Schemas ---


class RoleUpdate(BaseModel):
    role: str


# --- Dashboard / Stats ---


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Overview statistics for admin dashboard."""
    return {
        "users": db.query(User).count(),
        "courses": db.query(Course).count(),
        "enrollments": db.query(Enrollment).count(),
        "certificates": db.query(Certificate).count(),
        "exercises": db.query(Exercise).count(),
    }


# --- User management ---


@router.get("/users")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: Literal["created_at", "username", "role"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """List users with pagination and sorting."""
    total = db.query(User).count()
    column = USERS_SORT_COLUMNS[sort_by]
    order = column.asc() if sort_order == "asc" else column.desc()
    users = db.query(User).order_by(order).offset(skip).limit(limit).all()
    return {
        "total": total,
        "data": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "avatar_url": u.avatar_url,
                "role": u.role.value if u.role else "student",
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
    }


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    """Change a user's role."""
    if data.role not in ("student", "mentor", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    previous_role = user.role.value
    user.role = UserRole(data.role)
    db.commit()

    # Sync Discord role if user has linked their Discord
    if user.discord_id:
        from app.services.discord_bot import sync_discord_role

        sync_discord_role(user.discord_id, data.role, previous_role)

    return {"id": user.id, "username": user.username, "role": user.role.value}


# --- Course management ---


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete a course and all its modules, exercises, enrollments, progress."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = db.query(Module).filter(Module.course_id == course_id).all()
    module_ids = [m.id for m in modules]

    if module_ids:
        exercise_ids = [e.id for e in db.query(Exercise.id).filter(Exercise.module_id.in_(module_ids)).all()]
        if exercise_ids:
            db.query(Progress).filter(Progress.exercise_id.in_(exercise_ids)).delete(synchronize_session=False)
        db.query(Exercise).filter(Exercise.module_id.in_(module_ids)).delete(synchronize_session=False)

    db.query(Module).filter(Module.course_id == course_id).delete(synchronize_session=False)
    db.query(Enrollment).filter(Enrollment.course_id == course_id).delete(synchronize_session=False)
    db.query(Certificate).filter(Certificate.course_id == course_id).delete(synchronize_session=False)
    db.query(PromotionRuleRequirement).filter(PromotionRuleRequirement.course_id == course_id).delete(
        synchronize_session=False
    )
    db.delete(course)
    db.commit()
    return {"detail": "Course deleted"}


@router.delete("/modules/{module_id}")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete a module and its exercises."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    exercise_ids = [e.id for e in db.query(Exercise.id).filter(Exercise.module_id == module_id).all()]
    if exercise_ids:
        db.query(Progress).filter(Progress.exercise_id.in_(exercise_ids)).delete(synchronize_session=False)
    db.query(Exercise).filter(Exercise.module_id == module_id).delete(synchronize_session=False)
    db.delete(module)
    db.commit()
    return {"detail": "Module deleted"}


@router.delete("/exercises/{exercise_id}")
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete an exercise and its progress records."""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    db.query(Progress).filter(Progress.exercise_id == exercise_id).delete(synchronize_session=False)
    db.delete(exercise)
    db.commit()
    return {"detail": "Exercise deleted"}


# --- Promotion rules ---


class PromotionRuleCreate(BaseModel):
    name: str
    description: str | None = None
    target_role: str
    course_ids: list[int]


class PromotionRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_role: str | None = None
    is_active: bool | None = None
    course_ids: list[int] | None = None


def _serialize_rule(rule: PromotionRule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "target_role": rule.target_role.value if rule.target_role else None,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "course_ids": [r.course_id for r in rule.requirements],
    }


@router.get("/promotion-rules")
def list_promotion_rules(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """List all promotion rules."""
    rules = db.query(PromotionRule).order_by(PromotionRule.id).all()
    return [_serialize_rule(r) for r in rules]


@router.post("/promotion-rules", status_code=201)
def create_promotion_rule(
    data: PromotionRuleCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Create a new promotion rule."""
    if data.target_role not in ("student", "mentor", "admin"):
        raise HTTPException(status_code=400, detail="Invalid target role")
    if not data.course_ids:
        raise HTTPException(status_code=400, detail="At least one course is required")

    # Validate that all course_ids exist.
    existing = {row[0] for row in db.query(Course.id).filter(Course.id.in_(data.course_ids)).all()}
    missing = set(data.course_ids) - existing
    if missing:
        raise HTTPException(status_code=400, detail=f"Course IDs not found: {sorted(missing)}")

    rule = PromotionRule(
        name=data.name,
        description=data.description,
        target_role=UserRole(data.target_role),
    )
    db.add(rule)
    db.flush()

    for cid in data.course_ids:
        db.add(PromotionRuleRequirement(rule_id=rule.id, course_id=cid))
    db.commit()
    db.refresh(rule)
    return _serialize_rule(rule)


@router.get("/promotion-rules/{rule_id}")
def get_promotion_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Get a single promotion rule."""
    rule = db.query(PromotionRule).filter(PromotionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Promotion rule not found")
    return _serialize_rule(rule)


@router.patch("/promotion-rules/{rule_id}")
def update_promotion_rule(
    rule_id: int,
    data: PromotionRuleUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Update a promotion rule."""
    rule = db.query(PromotionRule).filter(PromotionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Promotion rule not found")

    if data.name is not None:
        rule.name = data.name
    if data.description is not None:
        rule.description = data.description
    if data.target_role is not None:
        if data.target_role not in ("student", "mentor", "admin"):
            raise HTTPException(status_code=400, detail="Invalid target role")
        rule.target_role = UserRole(data.target_role)
    if data.is_active is not None:
        rule.is_active = data.is_active

    if data.course_ids is not None:
        if not data.course_ids:
            raise HTTPException(status_code=400, detail="At least one course is required")
        existing = {row[0] for row in db.query(Course.id).filter(Course.id.in_(data.course_ids)).all()}
        missing = set(data.course_ids) - existing
        if missing:
            raise HTTPException(status_code=400, detail=f"Course IDs not found: {sorted(missing)}")

        # Replace requirements.
        db.query(PromotionRuleRequirement).filter(PromotionRuleRequirement.rule_id == rule.id).delete(
            synchronize_session=False
        )
        for cid in data.course_ids:
            db.add(PromotionRuleRequirement(rule_id=rule.id, course_id=cid))

    db.commit()
    db.refresh(rule)
    return _serialize_rule(rule)


@router.delete("/promotion-rules/{rule_id}")
def delete_promotion_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete a promotion rule."""
    rule = db.query(PromotionRule).filter(PromotionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Promotion rule not found")
    db.delete(rule)
    db.commit()
    return {"detail": "Promotion rule deleted"}


@router.get("/promotion-log")
def list_promotion_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """List promotion log entries (most recent first)."""
    total = db.query(PromotionLog).count()
    entries = db.query(PromotionLog).order_by(PromotionLog.promoted_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "data": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "rule_id": e.rule_id,
                "previous_role": e.previous_role.value,
                "new_role": e.new_role.value,
                "promoted_at": e.promoted_at.isoformat() if e.promoted_at else None,
            }
            for e in entries
        ],
    }
