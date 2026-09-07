from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('files', '0004_alter_file_object_key')]

    operations = [
        migrations.AddField(
            model_name='file',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
