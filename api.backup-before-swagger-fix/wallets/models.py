from django.conf import settings
from django.db import models

class Wallet(models.Model):
    NETWORK_BSC = 'bsc'
    NETWORK_CHOICES = [(NETWORK_BSC, 'BNB Smart Chain')]
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [(STATUS_ACTIVE, 'Active'), (STATUS_PAUSED, 'Paused')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES, default=NETWORK_BSC)
    derivation_index = models.PositiveIntegerField(unique=True)
    address = models.CharField(max_length=42, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} -> {self.address}'

class WalletState(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
