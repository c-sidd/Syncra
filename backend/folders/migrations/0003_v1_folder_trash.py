from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[('folders','0002_hardening')]
    operations=[migrations.AddField(model_name='folder',name='deleted_at',field=models.DateTimeField(blank=True,null=True)),migrations.AddIndex(model_name='folder',index=models.Index(fields=['user','deleted_at'],name='folders_user_deleted_idx'))]
