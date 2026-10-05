from django.contrib import admin
from .models import BlockchainState, Transaction, LedgerEntry
admin.site.register(BlockchainState)
admin.site.register(Transaction)
admin.site.register(LedgerEntry)
