
import uuid

from django.conf import settings
from django.db import models


class VirusScanStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CLEAN = 'clean', 'Clean'
    INFECTED = 'infected', 'Infected'
    FAILED = 'failed', 'Failed'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey('applications.AccreditationApplication', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100)

    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_hash = models.CharField(max_length=64, blank=True)
    virus_scan_status = models.CharField(max_length=20, choices=VirusScanStatus.choices, default=VirusScanStatus.PENDING)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} {self.id}"
