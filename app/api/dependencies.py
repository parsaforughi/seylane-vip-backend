"""Shared dependencies for API endpoints."""

from __future__ import annotations

from base64 import b64decode
import secrets

from fastapi import Depends, HTTPException, Request, status

from app.config import settings
from app.security import get_current_user
from app.models import User


async def require_admin_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has administrative privileges."""

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


async def require_admin(request: Request) -> None:
    """Verify admin credentials via Basic Auth or admin token header."""

    auth_header = request.headers.get("Authorization", "")
    token_header = request.headers.get("x-admin-token")
    username = password = ""

    if auth_header.lower().startswith("basic "):
        encoded = auth_header.split(" ", 1)[1]
        try:
            decoded = b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            pass

    expected_username = settings.admin_username
    expected_password = settings.admin_password
    expected_token = settings.resolved_admin_token

    if (
        username
        and secrets.compare_digest(username, expected_username)
        and secrets.compare_digest(password, expected_password)
    ):
        return
    if token_header and secrets.compare_digest(token_header, expected_token):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin credentials",
        headers={"WWW-Authenticate": "Basic"},
    )
