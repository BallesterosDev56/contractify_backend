"""Firebase authentication and authorization."""

from typing import Annotated, Optional

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials
from pydantic import BaseModel

from .config import settings

# Initialize Firebase Admin SDK
_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is not None:
        return

    creds = settings.firebase_credentials
    if creds:
        cred = credentials.Certificate(creds)
        _firebase_app = firebase_admin.initialize_app(cred)
    else:
        # For development without Firebase
        _firebase_app = None


class CurrentUser(BaseModel):
    """Authenticated user data extracted from Firebase token."""

    id: str
    email: str
    email_verified: bool = False
    name: Optional[str] = None
    picture: Optional[str] = None


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> CurrentUser:
    """
    Validate Firebase JWT token and extract user info.

    Raises HTTPException 401 if token is invalid or missing.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Development mode: accept mock tokens
    if settings.debug and token.startswith("dev_"):
        # Parse dev token format: dev_userId_email
        parts = token.split("_", 2)
        if len(parts) >= 3:
            return CurrentUser(
                id=parts[1],
                email=parts[2],
                email_verified=True,
                name="Dev User",
            )
        return CurrentUser(
            id="dev_user_123",
            email="dev@example.com",
            email_verified=True,
            name="Dev User",
        )

    # Production: validate Firebase token
    if _firebase_app is None:
        init_firebase()

    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase not configured",
        )

    try:
        decoded_token = auth.verify_id_token(token)
        return CurrentUser(
            id=decoded_token["uid"],
            email=decoded_token.get("email", ""),
            email_verified=decoded_token.get("email_verified", False),
            name=decoded_token.get("name"),
            picture=decoded_token.get("picture"),
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[CurrentUser]:
    """
    Try to get current user, but don't fail if not authenticated.

    Used for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
