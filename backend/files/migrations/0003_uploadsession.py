from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import files.models


class Migration(migrations.Migration):
    dependencies = [
        ('files', '0002_s3_metadata'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_key', models.CharField(max_length=1024, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('size', models.BigIntegerField()),
                ('content_type', models.CharField(default='application/octet-stream', max_length=255)),
                ('is_multipart', models.BooleanField(default=False)),
                ('multipart_upload_id', models.CharField(blank=True, max_length=255)),
                ('state', models.CharField(choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('ABORTED', 'Aborted')], default='PENDING', max_length=16)),
                ('expires_at', models.DateTimeField(default=files.models.upload_expiry)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('folder', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='upload_sessions', to='folders.folder')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upload_sessions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
