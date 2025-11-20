"""
Security utilities for JWT token validation and authentication.
Integrates with auth-api JWT tokens and implements service-to-service authentication.
"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.core.exceptions import (
    AuthInsufficientPermissionsError,
    AuthTokenExpiredError,
    AuthTokenInvalidError,
    AuthTokenMissingError,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# OAuth2 bearer token extractor
security = HTTPBearer(auto_error=False)


class TokenPayload:
    """Structured representation of JWT token payload."""

    def __init__(self, payload: Dict):
        try:
            self.user_id: UUID = UUID(payload["sub"])
        except (TypeError, ValueError, KeyError):
            raise AuthTokenInvalidError({"reason": "Token missing subject"})
        self.email: Optional[str] = payload.get("email")
        self.org_id: Optional[UUID] = UUID(payload["org_id"]) if payload.get("org_id") else None
        self.subscription_level: str = payload.get("subscription_level", "free")
        self.ghost_mode: bool = payload.get("ghost_mode", False)
        self.exp: int = payload["exp"]
        self.iat: Optional[int] = payload.get("iat")
        self.token_type: str = payload.get("type", "access")
        self.role: Optional[str] = payload.get("role")

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "org_id": self.org_id,
            "subscription_level": self.subscription_level,
            "ghost_mode": self.ghost_mode,
            "role": self.role,
        }

    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        return self.subscription_level == "premium"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"

    @property
    def is_moderator(self) -> bool:
        """Check if user has moderator or admin role."""
        return self.role in ["admin", "moderator"]


def validate_jwt_token(token: str) -> TokenPayload:
    """
    Validate JWT token and extract payload.

    Args:
        token: JWT token string

    Returns:
        TokenPayload object with user information

    Raises:
        AuthTokenInvalidError: If token signature is invalid
        AuthTokenExpiredError: If token has expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Verify token type is 'access'
        if payload.get("type") != "access":
            raise AuthTokenInvalidError({"reason": "Invalid token type"})

        return TokenPayload(payload)

    except jwt.ExpiredSignatureError:
        expired_at = datetime.utcnow().isoformat()
        logger.warning("token_expired", expired_at=expired_at)
        raise AuthTokenExpiredError(expired_at=expired_at)

    except jwt.InvalidTokenError as e:
        logger.warning("token_invalid", error=str(e))
        raise AuthTokenInvalidError({"reason": str(e)})

    except Exception as e:
        logger.error("token_validation_failed", error=str(e))
        raise AuthTokenInvalidError({"reason": "Token validation failed"})


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    """
    Dependency to extract and validate current user from JWT token.

    Args:
        credentials: HTTP bearer credentials from Authorization header

    Returns:
        TokenPayload with user information

    Raises:
        AuthTokenMissingError: If no token provided
        AuthTokenInvalidError: If token is invalid
        AuthTokenExpiredError: If token has expired
    """
    if not credentials:
        logger.warning("auth_token_missing")
        raise AuthTokenMissingError()

    token = credentials.credentials
    token_payload = validate_jwt_token(token)

    logger.debug(
        "user_authenticated",
        user_id=str(token_payload.user_id),
        subscription_level=token_payload.subscription_level,
    )

    return token_payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    """
    Dependency to extract user if token is provided, otherwise return None.
    Used for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    try:
        return validate_jwt_token(credentials.credentials)
    except (AuthTokenInvalidError, AuthTokenExpiredError):
        return None


def require_premium(token_payload: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """
    Dependency to require Premium subscription.

    Args:
        token_payload: Current user token payload

    Returns:
        TokenPayload if user has premium

    Raises:
        SubscriptionPremiumRequiredError: If user is not premium
    """
    from app.core.exceptions import SubscriptionPremiumRequiredError

    if not token_payload.is_premium:
        logger.warning(
            "premium_required",
            user_id=str(token_payload.user_id),
            current_level=token_payload.subscription_level,
        )
        raise SubscriptionPremiumRequiredError(current_level=token_payload.subscription_level)

    return token_payload


async def require_admin(token_payload: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """
    Dependency to require admin role.
    Checks database for admin role if not in JWT token.

    Args:
        token_payload: Current user token payload

    Returns:
        TokenPayload if user is admin

    Raises:
        AuthInsufficientPermissionsError: If user is not admin
    """
    # First check JWT token (if auth-api includes role)
    if token_payload.is_admin:
        return token_payload

    # Fallback: Check database for admin role
    from app.core.database import db

    result = await db.fetch_one(
        "SELECT roles FROM activity.users WHERE user_id = $1",
        token_payload.user_id
    )

    if result:
        roles = result.get("roles", [])
        # Handle JSONB array
        if isinstance(roles, str):
            import json
            try:
                roles = json.loads(roles)
            except:
                roles = []

        if "admin" in roles:
            token_payload.role = "admin"  # Update for subsequent checks
            return token_payload

    logger.warning(
        "admin_required",
        user_id=str(token_payload.user_id),
        role=token_payload.role,
    )
    raise AuthInsufficientPermissionsError(required_role="admin")


async def require_moderator(token_payload: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """
    Dependency to require moderator or admin role.
    Checks database for role if not in JWT token.

    Args:
        token_payload: Current user token payload

    Returns:
        TokenPayload if user is moderator or admin

    Raises:
        AuthInsufficientPermissionsError: If user is not moderator/admin
    """
    # First check JWT token (if auth-api includes role)
    if token_payload.is_moderator:
        return token_payload

    # Fallback: Check database for moderator/admin role
    from app.core.database import db

    result = await db.fetch_one(
        "SELECT roles FROM activity.users WHERE user_id = $1",
        token_payload.user_id
    )

    if result:
        roles = result.get("roles", [])
        # Handle JSONB array
        if isinstance(roles, str):
            import json
            try:
                roles = json.loads(roles)
            except:
                roles = []

        for role in ["admin", "moderator"]:
            if role in roles:
                token_payload.role = role  # Update for subsequent checks
                return token_payload

    logger.warning(
        "moderator_required",
        user_id=str(token_payload.user_id),
        role=token_payload.role,
    )
    raise AuthInsufficientPermissionsError(required_role="moderator")


# ============================================================================
# Service-to-Service Authentication
# ============================================================================


def validate_service_api_key(
    x_service_api_key: Optional[str] = Header(None, alias="X-Service-API-Key"),
) -> str:
    """
    Dependency to validate service-to-service API key.

    Args:
        x_service_api_key: API key from X-Service-API-Key header

    Returns:
        Service name if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_service_api_key:
        logger.warning("service_api_key_missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service API key required",
        )

    # Map API keys to service names
    service_keys = {
        settings.ACTIVITIES_API_KEY: "activities-api",
        settings.PARTICIPATION_API_KEY: "participation-api",
        settings.MODERATION_API_KEY: "moderation-api",
        settings.PAYMENT_API_KEY: "payment-api",
    }

    service_name = service_keys.get(x_service_api_key)

    if not service_name:
        logger.warning("service_api_key_invalid", key_prefix=x_service_api_key[:8])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service API key",
        )

    logger.debug("service_authenticated", service=service_name)
    return service_name


def validate_payment_api_key(
    x_payment_api_key: Optional[str] = Header(None, alias="X-Payment-API-Key"),
) -> bool:
    """
    Dependency to validate payment processor API key.

    Returns:
        True if valid payment API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_payment_api_key or x_payment_api_key != settings.PAYMENT_API_KEY:
        logger.warning("payment_api_key_invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid payment API key",
        )

    logger.debug("payment_api_authenticated")
    return True
