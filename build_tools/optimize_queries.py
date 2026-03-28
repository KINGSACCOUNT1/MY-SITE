"""Database query optimization utilities and guidelines."""

OPTIMIZATION_GUIDE = """
Database Query Optimization Guidelines
======================================

1. USE SELECT_RELATED for Foreign Keys:
   ----------------------------------------
   # Bad: Causes N+1 queries
   investments = Investment.objects.filter(user=request.user)
   for inv in investments:
       print(inv.plan.name)  # Additional query for each plan
   
   # Good: Single JOIN query
   investments = Investment.objects.select_related('plan', 'user').filter(user=request.user)
   for inv in investments:
       print(inv.plan.name)  # No additional queries

2. USE PREFETCH_RELATED for Many-to-Many and Reverse FKs:
   --------------------------------------------------------
   # Bad: Causes N+1 queries
   users = CustomUser.objects.all()
   for user in users:
       print(user.investments.count())  # Additional query per user
   
   # Good: Separate optimized query
   users = CustomUser.objects.prefetch_related('investments')
   for user in users:
       print(user.investments.count())  # No additional queries

3. ADD DATABASE INDEXES:
   -----------------------
   class Investment(models.Model):
       class Meta:
           indexes = [
               models.Index(fields=['user', 'status']),
               models.Index(fields=['start_date', 'end_date']),
               models.Index(fields=['-created_at']),
           ]

4. USE ONLY() for Specific Fields:
   ---------------------------------
   # Bad: Fetches all fields
   users = CustomUser.objects.all()
   
   # Good: Only fetches needed fields
   users = CustomUser.objects.only('id', 'email', 'first_name', 'last_name')

5. USE VALUES() for Dictionaries:
   -------------------------------
   # When you only need specific fields as dicts
   user_data = CustomUser.objects.values('id', 'email', 'balance')

6. USE ANNOTATE for Aggregations:
   ---------------------------------
   from django.db.models import Sum, Count
   
   users = CustomUser.objects.annotate(
       total_invested=Sum('investments__amount'),
       investment_count=Count('investments')
   )

7. USE BULK_CREATE for Multiple Inserts:
   ----------------------------------------
   # Bad: Multiple INSERT queries
   for data in large_dataset:
       Model.objects.create(**data)
   
   # Good: Single INSERT query
   Model.objects.bulk_create([Model(**data) for data in large_dataset])

8. USE UPDATE() for Bulk Updates:
   ---------------------------------
   # Bad: Multiple UPDATE queries
   for obj in queryset:
       obj.status = 'processed'
       obj.save()
   
   # Good: Single UPDATE query
   queryset.update(status='processed')
"""


def print_optimization_guide():
    """Print database optimization guidelines."""
    print(OPTIMIZATION_GUIDE)


def check_model_indexes():
    """Check which models have indexes defined."""
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth.settings')
    django.setup()
    
    from django.apps import apps
    
    print("=" * 60)
    print("Model Index Report")
    print("=" * 60)
    print()
    
    for model in apps.get_models():
        if model._meta.app_label in ['accounts', 'investments', 'dashboard', 'kyc', 'notifications', 'tasks']:
            indexes = model._meta.indexes
            if indexes:
                print(f"✓ {model._meta.label}: {len(indexes)} indexes")
                for idx in indexes:
                    print(f"  - {idx.fields}")
            else:
                print(f"✗ {model._meta.label}: No indexes defined")
    
    print()
    print("=" * 60)


if __name__ == '__main__':
    print_optimization_guide()
    print()
    
    # Uncomment to check current indexes:
    # check_model_indexes()
