from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial') if False else ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AWSConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='My S3 Storage', max_length=100)),
                ('access_key_id', models.CharField(max_length=255)),
                ('secret_access_key', models.TextField()),
                ('region', models.CharField(default='us-east-1', max_length=100)),
                ('bucket_name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='aws_connection', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
