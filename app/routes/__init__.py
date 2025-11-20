"""
Route aggregation.
"""
from fastapi import APIRouter

from app.routes import (
    captain,
    heartbeat,
    interests,
    moderation,
    photos,
    profile,
    search,
    settings,
    subscription,
    verification,
)

api_router = APIRouter()

# IMPORTANT: search.router MUST come before profile.router to avoid /search matching /{user_id}
api_router.include_router(search.router, tags=["User Search"])
api_router.include_router(profile.router, tags=["Profile Management"])
api_router.include_router(photos.router, tags=["Photo Management"])
api_router.include_router(interests.router, tags=["Interest Tags"])
api_router.include_router(settings.router, tags=["User Settings"])
api_router.include_router(subscription.router, tags=["Subscription Management"])
api_router.include_router(captain.router, tags=["Captain Program"])
api_router.include_router(verification.router, tags=["Trust & Verification"])
api_router.include_router(heartbeat.router, tags=["Activity Tracking"])
api_router.include_router(moderation.router, tags=["Admin Moderation"])
