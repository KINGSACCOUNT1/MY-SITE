"""
REST API Views for Elite Wealth Capital.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from investments.models import Investment, InvestmentPlan, Deposit, Withdrawal, Transaction
from .serializers import (
    UserSerializer, InvestmentSerializer, InvestmentPlanSerializer,
    DepositSerializer, WithdrawalSerializer, TransactionSerializer,
    BalanceSerializer, DashboardStatsSerializer
)

User = get_user_model()


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of an object or admins to access it."""
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff:
            return True
        
        # Check if object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For User objects
        return obj == request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user information.
    Only the authenticated user can view their own profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """Users can only see their own profile, admins see all."""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class InvestmentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing investment plans.
    All authenticated users can view active plans.
    """
    serializer_class = InvestmentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only show active investment plans to regular users."""
        if self.request.user.is_staff:
            return InvestmentPlan.objects.all()
        return InvestmentPlan.objects.filter(is_active=True)


class InvestmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing investments.
    Users can view and create their own investments.
    """
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """Users can only see their own investments."""
        if self.request.user.is_staff:
            return Investment.objects.all().select_related('user', 'investment_plan')
        return Investment.objects.filter(user=self.request.user).select_related('investment_plan')
    
    def perform_create(self, serializer):
        """Set the user when creating an investment."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active investments for the user."""
        queryset = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get all completed investments for the user."""
        queryset = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an investment (if allowed)."""
        investment = self.get_object()
        
        if investment.status != 'active':
            return Response(
                {'error': 'Only active investments can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        investment.status = 'cancelled'
        investment.save()
        
        return Response({'message': 'Investment cancelled successfully.'})


class DepositViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing deposits.
    Users can create deposits and view their own deposit history.
    """
    serializer_class = DepositSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """Users can only see their own deposits."""
        if self.request.user.is_staff:
            return Deposit.objects.all().select_related('user')
        return Deposit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user when creating a deposit."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending deposits for the user."""
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Get all approved deposits for the user."""
        queryset = self.get_queryset().filter(status='approved')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class WithdrawalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing withdrawals.
    Users can create withdrawal requests and view their history.
    """
    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """Users can only see their own withdrawals."""
        if self.request.user.is_staff:
            return Withdrawal.objects.all().select_related('user')
        return Withdrawal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user when creating a withdrawal."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending withdrawals for the user."""
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending withdrawal."""
        withdrawal = self.get_object()
        
        if withdrawal.status != 'pending':
            return Response(
                {'error': 'Only pending withdrawals can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        withdrawal.status = 'cancelled'
        withdrawal.save()
        
        return Response({'message': 'Withdrawal cancelled successfully.'})


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing transaction history.
    Users can only view their own transactions.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """Users can only see their own transactions."""
        if self.request.user.is_staff:
            return Transaction.objects.all().select_related('user')
        return Transaction.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions (last 10)."""
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BalanceView(APIView):
    """
    API view for getting user balance information.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user's balance information."""
        try:
            profile = request.user.profile
            
            data = {
                'account_balance': profile.account_balance,
                'total_invested': profile.total_invested,
                'total_earned': profile.total_earned,
                'total_withdrawn': profile.total_withdrawn,
                'active_investments_count': Investment.objects.filter(
                    user=request.user,
                    status='active'
                ).count(),
                'pending_withdrawals_count': Withdrawal.objects.filter(
                    user=request.user,
                    status='pending'
                ).count()
            }
            
            serializer = BalanceSerializer(data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardStatsView(APIView):
    """
    API view for getting dashboard statistics.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics for current user."""
        try:
            profile = request.user.profile
            
            # Calculate ROI
            roi_percentage = 0
            if profile.total_invested > 0:
                roi_percentage = (profile.total_earned / profile.total_invested) * 100
            
            data = {
                'total_balance': profile.account_balance,
                'total_invested': profile.total_invested,
                'total_earned': profile.total_earned,
                'active_investments': Investment.objects.filter(
                    user=request.user,
                    status='active'
                ).count(),
                'completed_investments': Investment.objects.filter(
                    user=request.user,
                    status='completed'
                ).count(),
                'pending_deposits': Deposit.objects.filter(
                    user=request.user,
                    status='pending'
                ).count(),
                'pending_withdrawals': Withdrawal.objects.filter(
                    user=request.user,
                    status='pending'
                ).count(),
                'roi_percentage': round(roi_percentage, 2)
            }
            
            serializer = DashboardStatsSerializer(data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
