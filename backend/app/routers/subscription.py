
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from ..services.stripe_service import stripe_service
from ..services.auth_service import verify_token
import os

router = APIRouter()

class CheckoutRequest(BaseModel):
    return_url: str

class PortalRequest(BaseModel):
    return_url: str

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    profile, error = verify_token(token)
    if error != "success" or not profile:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
    return profile, error

@router.post("/checkout")
async def create_checkout_session(request: CheckoutRequest, token_data: tuple = Depends(get_current_user)):
    """
    Creates a Stripe Checkout Session.
    """
    user_profile, error = token_data
    if error != "success" or not user_profile:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = user_profile.get("id")
        email = user_profile.get("email") # Ensure auth_service returns email in profile or we fetch it
        
        # fallback if email not in profile (it should be)
        if not email:
             raise HTTPException(status_code=400, detail="User email not found")

        checkout_url = stripe_service.create_checkout_session(
            user_id=user_id,
            email=email,
            return_url=request.return_url
        )
        return {"url": checkout_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portal")
async def create_portal_session(request: PortalRequest, token_data: tuple = Depends(get_current_user)):
    """
    Creates a Stripe Customer Portal Session.
    """
    user_profile, error = token_data
    if error != "success" or not user_profile:
        raise HTTPException(status_code=401, detail="Unauthorized")

    stripe_customer_id = user_profile.get("stripe_customer_id")
    if not stripe_customer_id:
         raise HTTPException(status_code=400, detail="No billing account found for this user.")

    try:
        portal_url = stripe_service.create_portal_session(
            customer_id=stripe_customer_id,
            return_url=request.return_url
        )
        return {"url": portal_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handles Stripe Webhooks.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        # In a real app, verify signature here using stripe library
        # event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        # For now, we'll assume the service handles the logic if we pass the payload/sig
        # But commonly we just process the JSON if we trust the source (NOT SAFE FOR PROD without sig check)
        
        # Let's do proper signature verification
        import stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_completed(session)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await handle_subscription_deleted(subscription)

    return {"status": "success"}

async def handle_checkout_completed(session):
    """
    Update user profile with stripe_customer_id and subscription_status = active
    """
    from ..services.supabase_service import supabase_service
    
    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    
    if user_id and customer_id:
        print(f"💰 Payment success for User {user_id}. Activating subscription.")
        try:
             supabase_service.update_profile(user_id, {
                 "stripe_customer_id": customer_id,
                 "subscription_status": "active"
             })
        except Exception as e:
            print(f"Error updating profile after payment: {e}")

async def handle_subscription_deleted(subscription):
    """
    Deactivate user subscription
    """
    from ..services.supabase_service import supabase_service
    # We need to find the user by customer_id since subscription obj might not have metadata directly if not expanded
    # But usually we can search profile by stripe_customer_id
    customer_id = subscription.get("customer")
    
    if customer_id:
        print(f"❌ Subscription deleted for Customer {customer_id}. Downgrading.")
        try:
            # We assume we can query by stripe_customer_id. 
            # Since supabase_service might not have a find_by, we might need to add it or do a raw query via client
            res = supabase_service.client.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
            if res.data:
                for user in res.data:
                    supabase_service.update_profile(user['id'], {
                        "subscription_status": "canceled"
                    })
        except Exception as e:
            print(f"Error downgrading user: {e}")
