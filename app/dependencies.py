"""
Common dependencies for API routes using Python 3.11 Annotated syntax.
"""
from typing import Annotated

from fastapi import Depends

from app.core.security import TokenPayload, get_current_user

from app.services.interest_service import InterestService, get_interest_service
from app.services.moderation_service import ModerationService, get_moderation_service
from app.services.photo_service import PhotoService, get_photo_service
from app.services.profile_service import ProfileService, get_profile_service
from app.services.search_service import SearchService, get_search_service
from app.services.settings_service import SettingsService, get_settings_service
from app.services.subscription_service import SubscriptionService, get_subscription_service
from app.services.verification_service import VerificationService, get_verification_service

# User Dependencies
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]

# Service Dependencies
InterestSvc = Annotated[InterestService, Depends(get_interest_service)]
ModerationSvc = Annotated[ModerationService, Depends(get_moderation_service)]
PhotoSvc = Annotated[PhotoService, Depends(get_photo_service)]
ProfileSvc = Annotated[ProfileService, Depends(get_profile_service)]
SearchSvc = Annotated[SearchService, Depends(get_search_service)]
SettingsSvc = Annotated[SettingsService, Depends(get_settings_service)]
SubscriptionSvc = Annotated[SubscriptionService, Depends(get_subscription_service)]
VerificationSvc = Annotated[VerificationService, Depends(get_verification_service)]