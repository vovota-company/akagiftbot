from django.conf import settings
from django.db import models

class Subscription(models.Model):
    PLAN_ANNUAL = 'annual'
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=32, default=PLAN_ANNUAL)
    price = models.DecimalField(max_digits=20, decimal_places=6, default=80)
    currency = models.CharField(max_length=12, default='USDT')
    payment_status = models.CharField(max_length=20, default=STATUS_PENDING)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=128, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
