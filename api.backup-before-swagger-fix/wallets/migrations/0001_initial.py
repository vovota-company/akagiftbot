from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('auth', '0012_alter_user_first_name_max_length')]
    operations = [
        migrations.CreateModel(name='Wallet', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('network', models.CharField(choices=[('bsc','BNB Smart Chain')], default='bsc', max_length=20)),
            ('derivation_index', models.PositiveIntegerField(unique=True)),
            ('address', models.CharField(db_index=True, max_length=42, unique=True)),
            ('status', models.CharField(choices=[('active','Active'),('paused','Paused')], default='active', max_length=20)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to='auth.user')),
        ]),
        migrations.CreateModel(name='WalletState', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('key', models.CharField(max_length=64, unique=True)),
            ('value', models.CharField(max_length=255)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
    ]
