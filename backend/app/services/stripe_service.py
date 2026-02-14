
import stripe
import os
from typing import Optional, Dict

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
PRODUCT_PRICE_ID = "price_H5ggYJDqQq" # Placeholder, needs to be replaced with env var or real ID

class StripeService:
    def __init__(self):
        self.api_key = stripe.api_key
        if not self.api_key:
            print("⚠️ Warning: STRIPE_SECRET_KEY not set.")

    def create_checkout_session(self, user_id: str, email: str, return_url: str) -> str:
        """
        Creates a Stripe Checkout Session for a subscription.
        Returns the URL to redirect the user to.
        """
        try:
            # We use metadata to link the Stripe session back to our Supabase user
            checkout_session = stripe.checkout.Session.create(
                customer_email=email,
                line_items=[
                    {
                        # Provide the exact Price ID (e.g. price_1234) of the product you want to sell
                        # For dynamic prices, we might need to look it up or pass it in.
                        # Using a placeholder environment variable for now.
                        'price': os.environ.get("STRIPE_PRICE_ID"),
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
            print(f"Error creating checkout session: {e}")
            raise e

    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        """
        Creates a Billing Portal session for users to manage their subscription.
        """
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return portal_session.url
        except Exception as e:
            print(f"Error creating portal session: {e}")
            raise e

    def get_subscription_status(self, subscription_id: str) -> str:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return sub.status
        except Exception:
            return "unknown"

stripe_service = StripeService()
