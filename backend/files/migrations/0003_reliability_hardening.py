from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('files', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='uploadsession',
            name='part_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddIndex(model_name='file', index=models.Index(fields=['user', 'deleted_at'], name='files_file_user_id_deleted_idx')),
        migrations.AddIndex(model_name='file', index=models.Index(fields=['user', 'folder'], name='files_file_user_id_folder_idx')),
        migrations.AddIndex(model_name='uploadsession', index=models.Index(fields=['state', 'expires_at'], name='files_upload_state_exp_idx')),
        migrations.AddIndex(model_name='uploadsession', index=models.Index(fields=['user', 'state'], name='files_upload_user_state_idx')),
    ]
