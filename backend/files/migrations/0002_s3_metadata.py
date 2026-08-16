from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('files', '0001_initial')]

    operations = [
        migrations.AddField(model_name='file', name='object_key', field=models.CharField(default='legacy/', max_length=1024)),
        migrations.AddField(model_name='file', name='storage_class', field=models.CharField(default='STANDARD', max_length=50)),
        migrations.RemoveField(model_name='file', name='file'),
    ]
