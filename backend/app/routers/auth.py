from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token, create_refresh_token
from app.config import settings
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/login")
def auth_login():
    """Redirect to GitHub OAuth authorization page."""
    url = f"{GITHUB_AUTHORIZE_URL}?client_id={settings.github_client_id}&scope=read:user user:email repo"
    return RedirectResponse(url=url)


@router.get("/callback")
def auth_callback(code: str, db: Session = Depends(get_db), response: Response = None):
    """Handle GitHub OAuth callback: exchange code for token, create/update user, return JWT."""
    # Exchange code for access token
    token_response = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
        },
        headers={"Accept": "application/json"},
    )
    token_data = token_response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub OAuth failed")

    # Get user info from GitHub
    user_response = httpx.get(
        GITHUB_USER_URL,
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    github_user = user_response.json()

    if "id" not in github_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to get GitHub user info")

    # Create or update user
    user = db.query(User).filter(User.github_id == github_user["id"]).first()
    if user:
        user.last_login = datetime.now(UTC)
        user.username = github_user.get("login", user.username)
        user.avatar_url = github_user.get("avatar_url", user.avatar_url)
        user.email = github_user.get("email", user.email)
        user.github_token = token_data["access_token"]
    else:
        user = User(
            github_id=github_user["id"],
            username=github_user.get("login", ""),
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
            last_login=datetime.now(UTC),
            github_token=token_data["access_token"],
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Redirect to frontend with token in URL fragment (not sent to server)
    redirect_url = f"/login#token={access_token}"
    resp = RedirectResponse(url=redirect_url, status_code=302)
    resp.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return resp


@router.get("/me")
def auth_me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user info."""
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role.value,
    }


@router.post("/refresh")
def auth_refresh(request: Request, db: Session = Depends(get_db)):
    """Issue a new access token using the refresh token cookie."""
    from app.auth.jwt import verify_token

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        token_data = verify_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None

    if token_data.get("payload", {}).get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token(user.id)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
def auth_logout(response: Response):
    """Clear the refresh token cookie."""
    response = Response(content='{"detail": "Logged out"}')
    response.headers["Content-Type"] = "application/json"
    response.delete_cookie(key="refresh_token")
    return response
