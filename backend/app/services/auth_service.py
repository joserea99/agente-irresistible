import logging
from typing import Tuple, Optional, List, Dict
from datetime import datetime, timedelta
from .supabase_service import supabase_service
from ..core.config import settings

logger = logging.getLogger(__name__)


def verify_token(token: str) -> Tuple[Optional[dict], str]:
    """
    Verifies a Supabase JWT and returns the user profile.
    Returns: (profile_dict, error_message)
    """
    if not supabase_service.client:
        return None, "database_connection_error"

    try:
        # 1. Verify specific token with Supabase Auth
        user_response = supabase_service.client.auth.get_user(token)
        user = user_response.user

        if not user:
            return None, "invalid_token"

        # 2. Fetch public profile (roles, subscription)
        profile = supabase_service.get_profile(user.id)

        if not profile:
            # Fallback for race condition where trigger hasn't run yet
            return {
                "id": user.id,
                "email": user.email,
                "role": "member",
                "subscription_status": "trial",
                "trial_ends_at": (datetime.now() + timedelta(days=settings.trial_days)).isoformat(),
                "full_name": user.user_metadata.get("full_name", "")
            }, "success"

        # Inject email from auth user if missing in profile
        if not profile.get("email") and user.email:
            profile["email"] = user.email

        # Initialize trial if it's null
        if not profile.get("trial_ends_at") and profile.get("subscription_status") == "trial":
            try:
                trial_end = datetime.now() + timedelta(days=settings.trial_days)
                supabase_service.update_profile(user.id, {
                    "trial_ends_at": trial_end.isoformat(),
                    "subscription_status": "trial"
                })
                profile["trial_ends_at"] = trial_end.isoformat()
            except Exception as e:
                logger.error(f"Error initializing trial: {e}")

        # 3. Check Subscription Status
        status = profile.get("subscription_status", "trial")

        if status == "active" or profile.get("role") == "admin":
             return profile, "success"

        if status == "trial":
            trial_end_str = profile.get("trial_ends_at")
            if trial_end_str:
                try:
                    if isinstance(trial_end_str, str):
                        trial_end = datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
                    else:
                        trial_end = trial_end_str

                    if datetime.now(trial_end.tzinfo) > trial_end:
                         return None, "trial_expired"
                except Exception as e:
                    logger.error(f"Error parsing trial date: {e}")

        return profile, "success"

    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None, "invalid_token"


def get_all_users() -> List[Dict]:
    """Retrieves all users with their details (for Admin Dashboard)."""
    if not supabase_service.client: return []
    try:
        response = supabase_service.client.table("profiles").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []

def delete_user(user_id: str) -> bool:
    """Deletes a user (Admin only)."""
    if not supabase_service.client: return False
    try:
        supabase_service.client.auth.admin.delete_user(user_id)
        return True
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return False

def update_user_role(user_id: str, role: str):
    """Updates a user's role."""
    supabase_service.update_profile(user_id, {"role": role})

def update_user_subscription(user_id: str, status: str):
    """Updates a user's subscription status."""
    data = {"subscription_status": status}

    if status == "active":
        data["trial_ends_at"] = None
    elif status == "trial":
        data["trial_ends_at"] = (datetime.now() + timedelta(days=settings.trial_days - 1)).isoformat()

    if not supabase_service.update_profile(user_id, data):
        raise Exception("Failed to update user subscription in database.")
