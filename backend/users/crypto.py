from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    key = getattr(settings, 'CREDENTIAL_ENCRYPTION_KEY', None)
    if not key:
        raise RuntimeError('CREDENTIAL_ENCRYPTION_KEY is not configured.')
    return Fernet(key.encode())


def encrypt_value(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
