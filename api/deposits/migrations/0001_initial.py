from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('auth','0012_alter_user_first_name_max_length'), ('wallets','0001_initial')]
    operations = [
        migrations.CreateModel(name='BlockchainState', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('network', models.CharField(max_length=20, unique=True)),
            ('last_scanned_block', models.BigIntegerField(default=0)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='Transaction', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('type', models.CharField(choices=[('deposit','Deposit'),('sweep','Sweep'),('gas_topup','Gas topup')], max_length=20)),
            ('asset', models.CharField(default='USDT', max_length=32)),
            ('network', models.CharField(default='bsc', max_length=20)),
            ('amount', models.DecimalField(decimal_places=18, max_digits=36)),
            ('fee', models.DecimalField(decimal_places=18, default=0, max_digits=36)),
            ('tx_hash', models.CharField(db_index=True, max_length=66)),
            ('log_index', models.PositiveIntegerField(default=0)),
            ('block_number', models.BigIntegerField()),
            ('confirmations', models.PositiveIntegerField(default=0)),
            ('status', models.CharField(choices=[('detected','Detected'),('confirmed','Confirmed'),('processing','Processing'),('collected','Collected'),('failed','Failed')], default='detected', max_length=20)),
            ('collected_tx_hash', models.CharField(blank=True, default='', max_length=66)),
            ('error_message', models.TextField(blank=True, default='')),
            ('detected_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='auth.user')),
            ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='wallets.wallet')),
        ]),
        migrations.CreateModel(name='LedgerEntry', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('account', models.CharField(max_length=64)),
            ('asset', models.CharField(default='USDT', max_length=32)),
            ('amount', models.DecimalField(decimal_places=18, max_digits=36)),
            ('direction', models.CharField(choices=[('credit','Credit'),('debit','Debit')], max_length=8)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ledger_entries', to='deposits.transaction')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='auth.user')),
        ]),
        migrations.AddConstraint(model_name='transaction', constraint=models.UniqueConstraint(fields=('tx_hash','log_index','type'), name='uniq_chain_event_type')),
    ]
