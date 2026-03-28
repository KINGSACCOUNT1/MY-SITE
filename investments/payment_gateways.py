"""
Payment Gateway Integrations for Elite Wealth Capital.
Handles Stripe, PayPal, and Cryptocurrency payments.
"""

import os
import json
import stripe
import paypalrestsdk
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from typing import Dict, Optional, Tuple

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize PayPal
paypalrestsdk.configure({
    "mode": os.getenv('PAYPAL_MODE', 'sandbox'),  # sandbox or live
    "client_id": os.getenv('PAYPAL_CLIENT_ID'),
    "client_secret": os.getenv('PAYPAL_CLIENT_SECRET')
})


class StripePaymentGateway:
    """Handle Stripe payment processing."""
    
    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = 'usd',
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Create a Stripe Payment Intent.
        
        Args:
            amount: Amount in dollars (will be converted to cents)
            currency: Currency code (default: usd)
            metadata: Additional metadata for the payment
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            return True, {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'status': intent.status
            }
            
        except stripe.error.StripeError as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def verify_payment(payment_intent_id: str) -> Tuple[bool, Dict]:
        """
        Verify a Stripe payment.
        
        Args:
            payment_intent_id: The Payment Intent ID to verify
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return True, {
                'status': intent.status,
                'amount': Decimal(intent.amount) / 100,
                'currency': intent.currency,
                'metadata': intent.metadata
            }
            
        except stripe.error.StripeError as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def create_checkout_session(
        amount: Decimal,
        currency: str = 'usd',
        success_url: str = None,
        cancel_url: str = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Create a Stripe Checkout Session for hosted payment page.
        
        Args:
            amount: Amount in dollars
            currency: Currency code
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            metadata: Additional metadata
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            amount_cents = int(amount * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': 'Investment Deposit',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            
            return True, {
                'session_id': session.id,
                'url': session.url
            }
            
        except stripe.error.StripeError as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str) -> Tuple[bool, Dict]:
        """
        Handle Stripe webhook events.
        
        Args:
            payload: Request body
            sig_header: Stripe-Signature header
            
        Returns:
            Tuple of (success: bool, event_data: dict)
        """
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            return True, {
                'type': event['type'],
                'data': event['data']['object']
            }
            
        except Exception as e:
            return False, {'error': str(e)}


class PayPalPaymentGateway:
    """Handle PayPal payment processing."""
    
    @staticmethod
    def create_payment(
        amount: Decimal,
        currency: str = 'USD',
        return_url: str = None,
        cancel_url: str = None,
        description: str = 'Investment Deposit'
    ) -> Tuple[bool, Dict]:
        """
        Create a PayPal payment.
        
        Args:
            amount: Amount to charge
            currency: Currency code
            return_url: URL to redirect after payment approval
            cancel_url: URL to redirect if payment is cancelled
            description: Payment description
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description
                }]
            })
            
            if payment.create():
                # Extract approval URL
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return True, {
                    'payment_id': payment.id,
                    'approval_url': approval_url,
                    'status': payment.state
                }
            else:
                return False, {'error': payment.error}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def execute_payment(payment_id: str, payer_id: str) -> Tuple[bool, Dict]:
        """
        Execute an approved PayPal payment.
        
        Args:
            payment_id: PayPal payment ID
            payer_id: Payer ID from PayPal redirect
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                transaction = payment.transactions[0]
                
                return True, {
                    'payment_id': payment.id,
                    'status': payment.state,
                    'amount': Decimal(transaction.amount.total),
                    'currency': transaction.amount.currency
                }
            else:
                return False, {'error': payment.error}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def verify_payment(payment_id: str) -> Tuple[bool, Dict]:
        """
        Verify a PayPal payment.
        
        Args:
            payment_id: PayPal payment ID
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            transaction = payment.transactions[0]
            
            return True, {
                'payment_id': payment.id,
                'status': payment.state,
                'amount': Decimal(transaction.amount.total),
                'currency': transaction.amount.currency
            }
            
        except Exception as e:
            return False, {'error': str(e)}


class CryptoPaymentGateway:
    """Handle Cryptocurrency payment processing via Coinbase Commerce."""
    
    API_URL = 'https://api.commerce.coinbase.com'
    
    @staticmethod
    def _get_headers() -> Dict:
        """Get API request headers."""
        api_key = os.getenv('COINBASE_COMMERCE_API_KEY')
        return {
            'Content-Type': 'application/json',
            'X-CC-Api-Key': api_key,
            'X-CC-Version': '2018-03-22'
        }
    
    @staticmethod
    def create_charge(
        amount: Decimal,
        currency: str = 'USD',
        name: str = 'Investment Deposit',
        description: str = '',
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Create a cryptocurrency charge.
        
        Args:
            amount: Amount in fiat currency
            currency: Fiat currency code
            name: Charge name
            description: Charge description
            metadata: Additional metadata
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            import requests
            
            url = f"{CryptoPaymentGateway.API_URL}/charges"
            headers = CryptoPaymentGateway._get_headers()
            
            data = {
                'name': name,
                'description': description,
                'pricing_type': 'fixed_price',
                'local_price': {
                    'amount': str(amount),
                    'currency': currency
                },
                'metadata': metadata or {}
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                charge_data = response.json()['data']
                
                return True, {
                    'charge_id': charge_data['id'],
                    'hosted_url': charge_data['hosted_url'],
                    'addresses': charge_data['addresses'],
                    'pricing': charge_data['pricing']
                }
            else:
                return False, {'error': response.json()}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def verify_charge(charge_id: str) -> Tuple[bool, Dict]:
        """
        Verify a cryptocurrency charge.
        
        Args:
            charge_id: Coinbase Commerce charge ID
            
        Returns:
            Tuple of (success: bool, data: dict)
        """
        try:
            import requests
            
            url = f"{CryptoPaymentGateway.API_URL}/charges/{charge_id}"
            headers = CryptoPaymentGateway._get_headers()
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                charge_data = response.json()['data']
                
                return True, {
                    'charge_id': charge_data['id'],
                    'status': charge_data['timeline'][-1]['status'],
                    'pricing': charge_data['pricing'],
                    'payments': charge_data.get('payments', [])
                }
            else:
                return False, {'error': response.json()}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str) -> Tuple[bool, Dict]:
        """
        Handle Coinbase Commerce webhook events.
        
        Args:
            payload: Request body
            sig_header: X-CC-Webhook-Signature header
            
        Returns:
            Tuple of (success: bool, event_data: dict)
        """
        import hmac
        import hashlib
        
        webhook_secret = os.getenv('COINBASE_COMMERCE_WEBHOOK_SECRET')
        
        try:
            # Verify signature
            expected_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_sig, sig_header):
                return False, {'error': 'Invalid signature'}
            
            event_data = json.loads(payload)
            
            return True, {
                'event_type': event_data['event']['type'],
                'charge_id': event_data['event']['data']['id'],
                'data': event_data['event']['data']
            }
            
        except Exception as e:
            return False, {'error': str(e)}
