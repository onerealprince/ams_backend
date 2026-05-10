import uuid

from django.db import models


class LicenseStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    REVOKED = 'revoked', 'Revoked'
    EXPIRED = 'expired', 'Expired'
    CLOSED = 'closed', 'Closed'


class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license_number = models.CharField(max_length=100, unique=True)
    institution = models.OneToOneField('institutions.Institution', on_delete=models.CASCADE, related_name='license')

    type = models.CharField(max_length=20, choices=[('provisional', 'Provisional'), ('full', 'Full')])
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)

    conditions = models.JSONField(default=list)
    crypto_signature = models.TextField(blank=True)
    qr_code_secret = models.UUIDField(default=uuid.uuid4, editable=False)

    board_resolution_reference = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=LicenseStatus.choices, default=LicenseStatus.ACTIVE)

    def __str__(self):
        return self.license_number
