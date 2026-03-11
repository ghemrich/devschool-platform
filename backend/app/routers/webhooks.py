import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.course import Exercise, Progress, ProgressStatus
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _verify_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    if not signature or not secret:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    """Receive GitHub webhook events and update exercise progress.

    Listens for 'workflow_run' events with conclusion='success'
    to automatically mark exercises as completed.
    """
    body = await request.body()

    # Verify signature if webhook secret is configured
    if settings.github_webhook_secret:
        if not _verify_signature(body, x_hub_signature_256, settings.github_webhook_secret):
            raise HTTPException(status_code=403, detail="Invalid signature")

    if x_github_event != "workflow_run":
        return {"status": "ignored", "event": x_github_event}

    import json
    from datetime import datetime, timezone

    payload = json.loads(body)

    if payload.get("action") != "completed":
        return {"status": "ignored", "reason": "not completed"}

    workflow_run = payload.get("workflow_run", {})
    if workflow_run.get("conclusion") != "success":
        return {"status": "ignored", "reason": "not successful"}

    repo_name = payload.get("repository", {}).get("name", "")
    if not repo_name:
        return {"status": "ignored", "reason": "no repo name"}

    # Match repo to exercise: repo format is "{repo_prefix}-{username}"
    # Find exercises whose repo_prefix matches
    exercises = db.query(Exercise).filter(Exercise.repo_prefix.isnot(None), Exercise.repo_prefix != "").all()

    matched = False
    for exercise in exercises:
        if not repo_name.startswith(exercise.repo_prefix):
            continue

        # Extract username suffix: repo_name = "{prefix}-{username}"
        suffix = repo_name[len(exercise.repo_prefix) :]
        if not suffix.startswith("-"):
            continue
        github_username = suffix[1:]

        user = db.query(User).filter(User.username == github_username).first()
        if not user:
            continue

        progress = db.query(Progress).filter(Progress.user_id == user.id, Progress.exercise_id == exercise.id).first()

        if progress is None:
            progress = Progress(
                user_id=user.id,
                exercise_id=exercise.id,
                github_repo=repo_name,
                status=ProgressStatus.completed,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(progress)
            matched = True
        elif progress.status != ProgressStatus.completed:
            progress.status = ProgressStatus.completed
            progress.completed_at = datetime.now(timezone.utc)
            matched = True

    if matched:
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to commit webhook progress update for repo=%s", repo_name)
            raise HTTPException(status_code=500, detail="Failed to update progress")

    return {"status": "processed", "repo": repo_name, "updated": matched}
