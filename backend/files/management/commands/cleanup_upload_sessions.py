from django.core.management.base import BaseCommand
from django.utils import timezone
from botocore.exceptions import BotoCoreError, ClientError

from files.models import UploadSession
from users.views import get_s3_client


class Command(BaseCommand):
    help = 'Abort expired multipart uploads and remove stale upload sessions.'

    def handle(self, *args, **options):
        now = timezone.now()
        sessions = UploadSession.objects.filter(state=UploadSession.State.PENDING, expires_at__lte=now).select_related('user')
        cleaned = 0
        for session in sessions:
            if session.is_multipart and session.multipart_upload_id:
                client, connection = get_s3_client(session.user)
                if client and connection:
                    try:
                        client.abort_multipart_upload(Bucket=connection.bucket_name, Key=session.object_key, UploadId=session.multipart_upload_id)
                    except (ClientError, BotoCoreError):
                        self.stderr.write(f'Could not abort upload session {session.pk}; keeping it for retry.')
                        continue
            session.state = UploadSession.State.ABORTED
            session.save(update_fields=['state'])
            cleaned += 1
        deleted, _ = UploadSession.objects.filter(state__in=[UploadSession.State.COMPLETED, UploadSession.State.ABORTED], created_at__lt=now - timezone.timedelta(days=7)).delete()
        self.stdout.write(self.style.SUCCESS(f'Cleaned {cleaned} expired sessions; removed {deleted} stale records.'))
