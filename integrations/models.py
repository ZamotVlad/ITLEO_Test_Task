from django.conf import settings
from django.db import models


class GoogleAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="google_account"
    )
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    is_connected = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"GoogleAccount({self.user.username})"
