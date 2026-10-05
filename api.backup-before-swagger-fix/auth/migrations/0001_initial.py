from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [('auth', '0012_alter_user_first_name_max_length')]
    operations = [migrations.CreateModel(name='UserProfile', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('google_sub', models.CharField(max_length=255, unique=True)),
        ('referral_code', models.CharField(blank=True, max_length=32, null=True, unique=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
    ])]
