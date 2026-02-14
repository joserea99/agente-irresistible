from typing import Tuple, Optional, List, Dict
from datetime import datetime, timedelta
from .supabase_service import supabase_service

# Deprecated: DB_PATH & init_db are no longer needed as we use Supabase

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
            # Initialize with 15 days trial implicitly for the session
            return {
                "id": user.id,
                "email": user.email,
                "role": "member",
                "subscription_status": "trial",
                "trial_ends_at": (datetime.now() + timedelta(days=15)).isoformat(),
                "full_name": user.user_metadata.get("full_name", "")
            }, "success"

        # Initialize trial if it's null (for existing users who didn't have this field)
        if not profile.get("trial_ends_at") and profile.get("subscription_status") == "trial":
            try:
                # Set 15 days from now
                trial_end = datetime.now() + timedelta(days=15)
                supabase_service.update_profile(user.id, {
                    "trial_ends_at": trial_end.isoformat(),
                    "subscription_status": "trial" # ensure status is set
                })
                profile["trial_ends_at"] = trial_end.isoformat()
            except Exception as e:
                print(f"Error initializing trial: {e}")

        # 3. Check Subscription Status
        status = profile.get("subscription_status", "trial")
        
        if status == "active" or profile.get("role") == "admin":
             return profile, "success"

        if status == "trial":
            trial_end_str = profile.get("trial_ends_at")
            if trial_end_str:
                try:
                    # Parse timestamp (Supabase usually returns ISO 8601)
                    if isinstance(trial_end_str, str):
                        # Handle potential 'Z' or offset if needed, simple approach first
                        trial_end = datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
                    else:
                        trial_end = trial_end_str

                    if datetime.now(trial_end.tzinfo) > trial_end:
                         # Trial Expired
                         return None, "trial_expired"
                except Exception as e:
                    print(f"Error parsing trial date: {e}")
                    # If date error, fail safe to allow or block? Block is safer for SaaS
                    # But for now let's log and allow to avoid locking out due to format issues
                    pass

        return profile, "success"

    except Exception as e:
        print(f"Token verification error: {e}")
        return None, "invalid_token"


def get_all_users() -> List[Dict]:
    """Retrieves all users with their details (for Admin Dashboard)."""
    if not supabase_service.client: return []
    try:
        response = supabase_service.client.table("profiles").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

def delete_user(user_id: str) -> bool:
    """Deletes a user (Admin only)."""
    if not supabase_service.client: return False
    try:
        # Delete from Auth (requires Service Role Key)
        supabase_service.client.auth.admin.delete_user(user_id)
        return True
    except Exception as e:
        print(f"Error deleting user {user_id}: {e}")
        return False

def update_user_role(user_id: str, role: str):
    """Updates a user's role."""
    supabase_service.update_profile(user_id, {"role": role})

# --- Backward Compatibility Stubs (to be removed after Frontend update) ---

def verify_user(username, password, device_fingerprint="unknown"):
    """
    DEPRECATED: Frontend should now use Supabase JS Client to login.
    This function is kept temporarily if there are legacy server-side login calls.
    """
    try:
        response = supabase_service.client.auth.sign_in_with_password({
            "email": username,
            "password": password
        })
        if response.user:
            profile = supabase_service.get_profile(response.user.id)
            if profile:
                 return (profile.get('full_name'), profile.get('role'), profile.get('subscription_status')), "success"
            return (response.user.user_metadata.get('full_name'), "member", "trial"), "success"
    except Exception:
        pass
    return None, "invalid_credentials"

def add_user(username, password, full_name, role="member"):
    """DEPRECATED: Use Supabase Auth checkouts."""
    try:
        supabase_service.client.auth.sign_up({
            "email": username,
            "password": password,
            "options": {
                "data": { "full_name": full_name }
            }
        })
        return True
    except:
        return False

