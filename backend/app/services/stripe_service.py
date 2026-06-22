import stripe
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class StripeService:
    def __init__(self):
        self.api_key = stripe.api_key
        self.price_id = os.environ.get("STRIPE_PRICE_ID")

        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set. Subscription features are disabled.")
        if not self.price_id:
            logger.warning("STRIPE_PRICE_ID not set. Subscription features are disabled.")

    def _check_configured(self):
        """Raise a clear error if Stripe is not configured."""
        if not self.api_key:
            raise ValueError(
                "Stripe is not configured. Please add STRIPE_SECRET_KEY to your Railway environment variables. "
                "Get your key at: https://dashboard.stripe.com/apikeys"
            )
        if not self.price_id:
            raise ValueError(
                "Stripe Price ID is not configured. Please add STRIPE_PRICE_ID to your Railway environment variables. "
                "Create a product at: https://dashboard.stripe.com/products"
            )

    def create_checkout_session(self, user_id: str, email: str, return_url: str) -> str:
        """
        Creates a Stripe Checkout Session for a subscription.
        Returns the URL to redirect the user to.
        """
        self._check_configured()
        try:
            # We use metadata to link the Stripe session back to our Supabase user
            checkout_session = stripe.checkout.Session.create(
                customer_email=email,
                line_items=[
                    {
                        'price': self.price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=return_url + '?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=return_url + '?canceled=true',
                metadata={
                    "user_id": user_id
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id
                    }
                },
                allow_promotion_codes=True,
                automatic_tax={'enabled': True}
            )
            return checkout_session.url
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise e

    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        """
        Creates a Billing Portal session for users to manage their subscription.
        """
        self._check_configured()
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return portal_session.url
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            raise e

    def get_subscription_status(self, subscription_id: str) -> str:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return sub.status
        except Exception:
            return "unknown"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.price_id)

stripe_service = StripeService()
