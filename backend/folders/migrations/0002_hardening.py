from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('folders', '0001_initial')]

    operations = [
        migrations.AddConstraint(
            model_name='folder',
            constraint=models.UniqueConstraint(fields=('user', 'parent', 'name'), name='unique_folder_name_per_parent'),
        ),
        migrations.AddIndex(
            model_name='folder',
            index=models.Index(fields=['user', 'parent'], name='folders_folder_user_parent_idx'),
        ),
    ]
