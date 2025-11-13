"""
Custom exception classes and error handling for the User Profile API.
Implements standardized error response format across all endpoints.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class APIException(HTTPException):
    """
    Base exception class for all custom API exceptions.
    Provides structured error responses with error codes.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}

        detail = {
            "error": {
                "code": error_code,
                "message": message,
                "details": self.details,
            }
        }
        super().__init__(status_code=status_code, detail=detail)


# ============================================================================
# AUTHENTICATION ERRORS (AUTH_***)
# ============================================================================


class AuthTokenMissingError(APIException):
    """No Authorization header provided."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_TOKEN_MISSING",
            message="No authorization token provided",
        )


class AuthTokenInvalidError(APIException):
    """Invalid JWT signature or format."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_TOKEN_INVALID",
            message="Invalid access token",
            details=details,
        )


class AuthTokenExpiredError(APIException):
    """Token past expiration time."""

    def __init__(self, expired_at: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_TOKEN_EXPIRED",
            message="Access token has expired",
            details={"expired_at": expired_at},
        )


class AuthInsufficientPermissionsError(APIException):
    """Valid token but insufficient permissions."""

    def __init__(self, required_role: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTH_INSUFFICIENT_PERMISSIONS",
            message="Insufficient permissions for this operation",
            details={"required_role": required_role},
        )


# ============================================================================
# VALIDATION ERRORS (VALIDATION_***)
# ============================================================================


class ValidationFieldRequiredError(APIException):
    """Required field missing."""

    def __init__(self, field: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_FIELD_REQUIRED",
            message=f"Field '{field}' is required",
            details={"field": field},
        )


class ValidationFieldTooLongError(APIException):
    """Field exceeds maximum length."""

    def __init__(self, field: str, max_length: int):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_FIELD_TOO_LONG",
            message=f"Field '{field}' exceeds maximum length of {max_length}",
            details={"field": field, "max_length": max_length},
        )


class ValidationAgeRestrictionError(APIException):
    """User under required age."""

    def __init__(self, min_age: int, provided_age: int):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_AGE_RESTRICTION",
            message=f"User must be at least {min_age} years old",
            details={"min_age": min_age, "provided_age": provided_age},
        )


class ValidationInvalidFormatError(APIException):
    """Field format is invalid."""

    def __init__(self, field: str, expected_format: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_INVALID_FORMAT",
            message=f"Field '{field}' has invalid format. Expected: {expected_format}",
            details={"field": field, "expected_format": expected_format},
        )


# ============================================================================
# RESOURCE ERRORS (RESOURCE_***)
# ============================================================================


class ResourceNotFoundError(APIException):
    """Resource doesn't exist (or blocked for privacy)."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource} not found",
        )


class ResourceDuplicateError(APIException):
    """Duplicate resource (username taken, photo already added)."""

    def __init__(self, field: str, value: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_DUPLICATE",
            message=f"{field.capitalize()} already exists",
            details={"field": field, "value": value},
        )


class ResourceLimitExceededError(APIException):
    """Resource limit exceeded (max interests, max photos)."""

    def __init__(self, resource: str, limit: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="RESOURCE_LIMIT_EXCEEDED",
            message=f"Maximum {resource} limit of {limit} exceeded",
            details={"resource": resource, "limit": limit},
        )


# ============================================================================
# SUBSCRIPTION ERRORS (SUBSCRIPTION_***)
# ============================================================================


class SubscriptionRequiredError(APIException):
    """Feature requires paid subscription."""

    def __init__(self, feature: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="SUBSCRIPTION_REQUIRED",
            message=f"'{feature}' requires a paid subscription",
            details={"feature": feature, "upgrade_url": "/subscription/upgrade"},
        )


class SubscriptionPremiumRequiredError(APIException):
    """Feature requires Premium subscription level."""

    def __init__(self, current_level: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="SUBSCRIPTION_PREMIUM_REQUIRED",
            message="This feature requires Premium subscription",
            details={
                "current_level": current_level,
                "required_level": "premium",
                "upgrade_url": "/subscription/upgrade",
            },
        )


# ============================================================================
# USER STATUS ERRORS (USER_***)
# ============================================================================


class UserBannedError(APIException):
    """Account permanently banned."""

    def __init__(self, reason: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="USER_BANNED",
            message="Account has been permanently banned",
            details={"reason": reason} if reason else {},
        )


class UserTemporarilyBannedError(APIException):
    """Account temporarily banned."""

    def __init__(self, expires_at: str, reason: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="USER_TEMPORARILY_BANNED",
            message="Account is temporarily banned",
            details={"expires_at": expires_at, "reason": reason} if reason else {"expires_at": expires_at},
        )


# ============================================================================
# MODERATION ERRORS (MODERATION_***)
# ============================================================================


class ModerationPhotoRejectedError(APIException):
    """Main photo was rejected during moderation."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="MODERATION_PHOTO_REJECTED",
            message="Your main photo was rejected. Please upload a clear photo showing your face.",
        )


# ============================================================================
# RATE LIMIT ERROR
# ============================================================================


class RateLimitExceededError(APIException):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int, limit: str, endpoint: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please try again later.",
            details={
                "retry_after": retry_after,
                "limit": limit,
                "endpoint": endpoint,
            },
        )


# ============================================================================
# DATABASE ERROR
# ============================================================================


class DatabaseError(APIException):
    """Database operation failed."""

    def __init__(self, request_id: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            message="An unexpected error occurred. Please try again.",
            details={"request_id": request_id},
        )
