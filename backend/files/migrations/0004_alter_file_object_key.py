from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('files', '0003_uploadsession')]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='object_key',
            field=models.CharField(max_length=1024),
        ),
    ]
