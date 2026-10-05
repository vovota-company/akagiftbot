from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('auth','0012_alter_user_first_name_max_length')]
    operations = [migrations.CreateModel(name='Subscription', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('plan', models.CharField(default='annual', max_length=32)),
        ('price', models.DecimalField(decimal_places=6, default=80, max_digits=20)),
        ('currency', models.CharField(default='USDT', max_length=12)),
        ('payment_status', models.CharField(default='pending', max_length=20)),
        ('start_at', models.DateTimeField(blank=True, null=True)),
        ('end_at', models.DateTimeField(blank=True, null=True)),
        ('transaction_id', models.CharField(blank=True, default='', max_length=128)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('updated_at', models.DateTimeField(auto_now=True)),
        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='auth.user')),
    ])]
