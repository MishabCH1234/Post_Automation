from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet
import base64
import hashlib


def _get_cipher():
    key = settings.FERNET_KEY
    if not key:
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    instagram_token = models.TextField(blank=True)

    def set_token(self, token):
        self.instagram_token = _get_cipher().encrypt(token.encode()).decode()

    def get_token(self):
        if not self.instagram_token:
            return ""
        return _get_cipher().decrypt(self.instagram_token.encode()).decode()

    def __str__(self):
        return self.user.username
