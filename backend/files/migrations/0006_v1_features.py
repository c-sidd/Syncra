from django.db import migrations, models
import uuid
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[('files','0005_file_deleted_at')]
    operations=[
      migrations.AddField(model_name='uploadsession',name='part_count',field=models.PositiveIntegerField(default=0)),
      migrations.AddIndex(model_name='file',index=models.Index(fields=['user','deleted_at'],name='files_user_deleted_idx')),
      migrations.AddIndex(model_name='file',index=models.Index(fields=['user','folder'],name='files_user_folder_idx')),
      migrations.CreateModel(name='ShareLink',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('token',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),('expires_at',models.DateTimeField(blank=True,null=True)),('is_active',models.BooleanField(default=True)),('created_at',models.DateTimeField(auto_now_add=True)),('created_by',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,to='auth.user')),('file',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='share_links',to='files.file'))])
    ]
