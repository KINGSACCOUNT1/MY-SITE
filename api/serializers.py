"""
REST API Serializers for Elite Wealth Capital.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from investments.models import Investment, InvestmentPlan, Deposit, Withdrawal, Transaction
from accounts.models import UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'date_joined', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']
    
    def get_profile(self, obj):
        """Get user profile data."""
        try:
            profile = obj.profile
            return {
                'phone_number': profile.phone_number,
                'country': profile.country,
                'kyc_verified': profile.kyc_verified,
                'account_balance': str(profile.account_balance),
                'total_invested': str(profile.total_invested),
                'total_withdrawn': str(profile.total_withdrawn),
            }
        except UserProfile.DoesNotExist:
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'user_email', 'phone_number', 'country', 'city',
            'address', 'kyc_verified', 'account_balance', 'total_invested',
            'total_earned', 'total_withdrawn', 'referral_code'
        ]
        read_only_fields = [
            'user', 'kyc_verified', 'account_balance', 'total_invested',
            'total_earned', 'total_withdrawn', 'referral_code'
        ]


class InvestmentPlanSerializer(serializers.ModelSerializer):
    """Serializer for InvestmentPlan model."""
    
    class Meta:
        model = InvestmentPlan
        fields = [
            'id', 'name', 'description', 'min_investment', 'max_investment',
            'roi_percentage', 'duration_days', 'risk_level', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for Investment model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    plan_name = serializers.CharField(source='investment_plan.name', read_only=True)
    plan_details = InvestmentPlanSerializer(source='investment_plan', read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Investment
        fields = [
            'id', 'user', 'user_email', 'investment_plan', 'plan_name',
            'plan_details', 'amount', 'expected_return', 'total_earned',
            'status', 'start_date', 'maturity_date', 'created_at',
            'days_remaining', 'progress_percentage'
        ]
        read_only_fields = [
            'id', 'user', 'expected_return', 'total_earned', 'status',
            'start_date', 'maturity_date', 'created_at', 'days_remaining'
        ]
    
    def get_progress_percentage(self, obj):
        """Calculate investment progress percentage."""
        if obj.status == 'completed':
            return 100
        
        from django.utils import timezone
        from datetime import timedelta
        
        if obj.maturity_date:
            total_days = (obj.maturity_date - obj.start_date).days
            elapsed_days = (timezone.now().date() - obj.start_date).days
            
            if total_days > 0:
                return min(100, int((elapsed_days / total_days) * 100))
        
        return 0


class DepositSerializer(serializers.ModelSerializer):
    """Serializer for Deposit model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Deposit
        fields = [
            'id', 'user', 'user_email', 'amount', 'payment_method',
            'transaction_id', 'status', 'proof_of_payment', 'admin_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'transaction_id', 'status', 'admin_notes',
            'created_at', 'updated_at'
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    """Serializer for Withdrawal model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'user', 'user_email', 'amount', 'withdrawal_method',
            'wallet_address', 'bank_account', 'status', 'admin_notes',
            'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'admin_notes', 'created_at', 'processed_at'
        ]


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_email', 'transaction_type', 'amount',
            'description', 'status', 'reference_id', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'reference_id', 'created_at']


class BalanceSerializer(serializers.Serializer):
    """Serializer for user balance information."""
    
    account_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_invested = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_withdrawn = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_investments_count = serializers.IntegerField()
    pending_withdrawals_count = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_invested = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_investments = serializers.IntegerField()
    completed_investments = serializers.IntegerField()
    pending_deposits = serializers.IntegerField()
    pending_withdrawals = serializers.IntegerField()
    roi_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
