"""
Advanced Portfolio Analytics for Elite Wealth Capital.
Provides ROI calculations, diversification analysis, and performance metrics.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone


class PortfolioAnalytics:
    """Advanced portfolio analytics and calculations."""
    
    @staticmethod
    def calculate_roi(
        initial_investment: Decimal,
        current_value: Decimal,
        period_days: Optional[int] = None
    ) -> Dict:
        """
        Calculate Return on Investment (ROI).
        
        Args:
            initial_investment: Initial investment amount
            current_value: Current portfolio value
            period_days: Number of days (for annualized ROI)
            
        Returns:
            Dictionary with ROI metrics
        """
        if initial_investment == 0:
            return {
                'roi_percentage': Decimal('0'),
                'profit_loss': Decimal('0'),
                'annualized_roi': Decimal('0')
            }
        
        profit_loss = current_value - initial_investment
        roi_percentage = (profit_loss / initial_investment) * 100
        
        # Calculate annualized ROI if period is provided
        annualized_roi = roi_percentage
        if period_days and period_days > 0:
            years = Decimal(period_days) / Decimal('365')
            if years > 0:
                annualized_roi = ((current_value / initial_investment) ** (1 / float(years)) - 1) * 100
        
        return {
            'roi_percentage': round(roi_percentage, 2),
            'profit_loss': round(profit_loss, 2),
            'annualized_roi': round(Decimal(annualized_roi), 2),
            'initial_investment': initial_investment,
            'current_value': current_value
        }
    
    @staticmethod
    def calculate_portfolio_diversification(investments) -> Dict:
        """
        Analyze portfolio diversification across investment plans.
        
        Args:
            investments: QuerySet of Investment objects
            
        Returns:
            Dictionary with diversification metrics
        """
        from investments.models import Investment
        
        # Group by investment plan
        plan_distribution = investments.values(
            'investment_plan__name',
            'investment_plan__risk_level'
        ).annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        )
        
        total_invested = sum(item['total_amount'] or 0 for item in plan_distribution)
        
        if total_invested == 0:
            return {
                'diversification_score': 0,
                'plan_distribution': [],
                'risk_distribution': {},
                'recommendation': 'Start investing to build a diversified portfolio'
            }
        
        # Calculate percentages
        plan_data = []
        risk_distribution = {'Low': 0, 'Medium': 0, 'High': 0}
        
        for item in plan_distribution:
            percentage = (item['total_amount'] / total_invested) * 100
            plan_data.append({
                'plan_name': item['investment_plan__name'],
                'amount': item['total_amount'],
                'percentage': round(percentage, 2),
                'count': item['count'],
                'risk_level': item['investment_plan__risk_level']
            })
            
            # Aggregate by risk level
            risk_level = item['investment_plan__risk_level']
            if risk_level in risk_distribution:
                risk_distribution[risk_level] += percentage
        
        # Calculate diversification score (0-100)
        # Higher score = better diversification
        num_plans = len(plan_data)
        if num_plans == 0:
            diversification_score = 0
        elif num_plans == 1:
            diversification_score = 30
        else:
            # Calculate using Herfindahl-Hirschman Index (HHI)
            # Lower HHI = better diversification
            hhi = sum((item['percentage'] / 100) ** 2 for item in plan_data)
            diversification_score = min(100, int((1 - hhi) * 150))
        
        # Generate recommendation
        if diversification_score >= 75:
            recommendation = 'Excellent diversification! Your portfolio is well-balanced.'
        elif diversification_score >= 50:
            recommendation = 'Good diversification. Consider adding more investment types.'
        elif diversification_score >= 30:
            recommendation = 'Moderate diversification. Spread investments across more plans.'
        else:
            recommendation = 'Poor diversification. Diversify to reduce risk.'
        
        return {
            'diversification_score': diversification_score,
            'plan_distribution': sorted(plan_data, key=lambda x: x['percentage'], reverse=True),
            'risk_distribution': {k: round(v, 2) for k, v in risk_distribution.items()},
            'total_invested': total_invested,
            'num_plans': num_plans,
            'recommendation': recommendation
        }
    
    @staticmethod
    def assess_portfolio_risk(investments) -> Dict:
        """
        Assess overall portfolio risk based on investment allocations.
        
        Args:
            investments: QuerySet of Investment objects
            
        Returns:
            Dictionary with risk assessment
        """
        risk_weights = {'Low': 1, 'Medium': 2, 'High': 3}
        
        risk_data = investments.values(
            'investment_plan__risk_level'
        ).annotate(
            total_amount=Sum('amount')
        )
        
        total_invested = sum(item['total_amount'] or 0 for item in risk_data)
        
        if total_invested == 0:
            return {
                'risk_score': 0,
                'risk_level': 'N/A',
                'recommendation': 'No active investments'
            }
        
        # Calculate weighted risk score
        weighted_risk = 0
        for item in risk_data:
            risk_level = item['investment_plan__risk_level']
            weight = risk_weights.get(risk_level, 2)
            percentage = item['total_amount'] / total_invested
            weighted_risk += weight * percentage
        
        # Normalize to 0-100 scale
        risk_score = int((weighted_risk / 3) * 100)
        
        # Determine overall risk level
        if risk_score <= 33:
            risk_level = 'Low Risk'
            recommendation = 'Conservative portfolio. Consider higher-yield options for growth.'
        elif risk_score <= 66:
            risk_level = 'Moderate Risk'
            recommendation = 'Balanced portfolio. Good mix of safety and growth potential.'
        else:
            risk_level = 'High Risk'
            recommendation = 'Aggressive portfolio. Ensure you can handle potential volatility.'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'risk_breakdown': {
                item['investment_plan__risk_level']: {
                    'amount': item['total_amount'],
                    'percentage': round((item['total_amount'] / total_invested) * 100, 2)
                }
                for item in risk_data
            }
        }
    
    @staticmethod
    def calculate_performance_comparison(
        user_roi: Decimal,
        period_days: int = 30
    ) -> Dict:
        """
        Compare user's performance against market benchmarks.
        
        Args:
            user_roi: User's ROI percentage
            period_days: Period for comparison
            
        Returns:
            Dictionary with comparison metrics
        """
        # Benchmark returns (annualized)
        benchmarks = {
            'S&P 500': Decimal('10.5'),
            'Bonds': Decimal('4.5'),
            'Gold': Decimal('7.8'),
            'Real Estate': Decimal('8.6')
        }
        
        # Adjust benchmarks for period
        period_factor = Decimal(period_days) / Decimal('365')
        adjusted_benchmarks = {
            name: round(value * period_factor, 2)
            for name, value in benchmarks.items()
        }
        
        # Calculate performance vs benchmarks
        comparisons = {}
        for name, benchmark_roi in adjusted_benchmarks.items():
            difference = user_roi - benchmark_roi
            outperformance = (difference / benchmark_roi * 100) if benchmark_roi != 0 else 0
            
            comparisons[name] = {
                'benchmark_roi': benchmark_roi,
                'difference': round(difference, 2),
                'outperformance_percentage': round(outperformance, 2),
                'status': 'Outperforming' if difference > 0 else 'Underperforming'
            }
        
        # Overall assessment
        avg_benchmark = sum(adjusted_benchmarks.values()) / len(adjusted_benchmarks)
        overall_status = 'Outperforming' if user_roi > avg_benchmark else 'Underperforming'
        
        return {
            'user_roi': user_roi,
            'average_benchmark': round(avg_benchmark, 2),
            'comparisons': comparisons,
            'overall_status': overall_status,
            'period_days': period_days
        }
    
    @staticmethod
    def generate_profit_loss_report(investments, period: str = '30d') -> Dict:
        """
        Generate detailed profit/loss report for a period.
        
        Args:
            investments: QuerySet of Investment objects
            period: Period string ('7d', '30d', '90d', '1y')
            
        Returns:
            Dictionary with P/L report
        """
        # Parse period
        period_map = {
            '7d': 7,
            '30d': 30,
            '90d': 90,
            '1y': 365
        }
        days = period_map.get(period, 30)
        start_date = timezone.now() - timedelta(days=days)
        
        # Filter investments within period
        period_investments = investments.filter(created_at__gte=start_date)
        
        # Calculate metrics
        total_invested = period_investments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        total_earned = period_investments.aggregate(
            total=Sum('total_earned')
        )['total'] or Decimal('0')
        
        active_count = period_investments.filter(status='active').count()
        completed_count = period_investments.filter(status='completed').count()
        
        # Calculate by plan
        by_plan = period_investments.values(
            'investment_plan__name'
        ).annotate(
            invested=Sum('amount'),
            earned=Sum('total_earned'),
            count=Count('id')
        )
        
        plan_performance = []
        for item in by_plan:
            invested = item['invested'] or Decimal('0')
            earned = item['earned'] or Decimal('0')
            roi = ((earned / invested) * 100) if invested > 0 else Decimal('0')
            
            plan_performance.append({
                'plan_name': item['investment_plan__name'],
                'invested': invested,
                'earned': earned,
                'profit': earned,
                'roi': round(roi, 2),
                'count': item['count']
            })
        
        return {
            'period': period,
            'period_days': days,
            'start_date': start_date,
            'total_invested': total_invested,
            'total_earned': total_earned,
            'net_profit': total_earned,
            'avg_roi': round((total_earned / total_invested * 100) if total_invested > 0 else 0, 2),
            'active_investments': active_count,
            'completed_investments': completed_count,
            'by_plan': sorted(plan_performance, key=lambda x: x['roi'], reverse=True)
        }
    
    @staticmethod
    def get_best_worst_performers(investments, limit: int = 5) -> Dict:
        """
        Get best and worst performing investments.
        
        Args:
            investments: QuerySet of Investment objects
            limit: Number of top/bottom performers to return
            
        Returns:
            Dictionary with best and worst performers
        """
        # Calculate ROI for each investment
        investments_with_roi = []
        
        for inv in investments:
            if inv.amount > 0:
                roi = (inv.total_earned / inv.amount) * 100
                investments_with_roi.append({
                    'id': inv.id,
                    'plan_name': inv.investment_plan.name,
                    'amount': inv.amount,
                    'earned': inv.total_earned,
                    'roi': round(roi, 2),
                    'status': inv.status,
                    'created_at': inv.created_at
                })
        
        # Sort by ROI
        sorted_investments = sorted(
            investments_with_roi,
            key=lambda x: x['roi'],
            reverse=True
        )
        
        best_performers = sorted_investments[:limit]
        worst_performers = sorted_investments[-limit:] if len(sorted_investments) > limit else []
        
        return {
            'best_performers': best_performers,
            'worst_performers': worst_performers[::-1],  # Reverse to show worst first
            'total_count': len(investments_with_roi)
        }
    
    @staticmethod
    def get_portfolio_timeline_data(investments, period: str = '30d') -> Dict:
        """
        Get portfolio performance data for timeline charts.
        
        Args:
            investments: QuerySet of Investment objects
            period: Period string ('7d', '30d', '90d', '1y')
            
        Returns:
            Dictionary with timeline data for charting
        """
        period_map = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}
        days = period_map.get(period, 30)
        
        # Generate date points
        end_date = timezone.now()
        date_points = []
        
        for i in range(days, -1, -1):
            date_point = end_date - timedelta(days=i)
            date_points.append(date_point)
        
        # Calculate portfolio value at each point
        timeline_data = []
        
        for date_point in date_points:
            # Get investments active at this date
            active_invs = investments.filter(
                created_at__lte=date_point,
                status__in=['active', 'completed']
            )
            
            total_value = active_invs.aggregate(
                total=Sum(F('amount') + F('total_earned'))
            )['total'] or Decimal('0')
            
            timeline_data.append({
                'date': date_point.strftime('%Y-%m-%d'),
                'value': float(total_value)
            })
        
        return {
            'period': period,
            'timeline': timeline_data
        }
