from django.conf import settings
from django.db import models
from api.wallets.models import Wallet

class BlockchainState(models.Model):
    network = models.CharField(max_length=20, unique=True)
    last_scanned_block = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class Transaction(models.Model):
    TYPE_DEPOSIT = 'deposit'
    TYPE_SWEEP = 'sweep'
    TYPE_GAS_TOPUP = 'gas_topup'
    TYPE_CHOICES = [(TYPE_DEPOSIT, 'Deposit'), (TYPE_SWEEP, 'Sweep'), (TYPE_GAS_TOPUP, 'Gas top-up')]
    STATUS_DETECTED = 'detected'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PROCESSING = 'processing'
    STATUS_COLLECTED = 'collected'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(x, x.title()) for x in (STATUS_DETECTED, STATUS_CONFIRMED, STATUS_PROCESSING, STATUS_COLLECTED, STATUS_FAILED)]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    asset = models.CharField(max_length=32, default='USDT')
    network = models.CharField(max_length=20, default='bsc')
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    fee = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    tx_hash = models.CharField(max_length=66, db_index=True)
    log_index = models.PositiveIntegerField(default=0)
    block_number = models.BigIntegerField()
    confirmations = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DETECTED)
    collected_tx_hash = models.CharField(max_length=66, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['tx_hash', 'log_index', 'type'], name='uniq_chain_event_type')]
        ordering = ['-detected_at']

class LedgerEntry(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='ledger_entries', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    account = models.CharField(max_length=64)
    asset = models.CharField(max_length=32, default='USDT')
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    direction = models.CharField(max_length=8, choices=[('credit','Credit'), ('debit','Debit')])
    created_at = models.DateTimeField(auto_now_add=True)
