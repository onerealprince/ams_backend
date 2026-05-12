import secrets
import uuid
from datetime import datetime

from django.core.validators import RegexValidator
from django.db import models


class InstitutionType(models.TextChoices):
    SCHOOL = 'school', 'School'
    UNIVERSITY = 'university', 'University'


class InstitutionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    REVOKED = 'revoked', 'Revoked'


class InstitutionOnboardingStatus(models.TextChoices):
    """Workflow for public registration → SA → Compliance → Board → account creation."""

    PENDING_SA_REVIEW = 'pending_sa_review', 'Pending SA review'
    WITH_COMPLIANCE = 'with_compliance', 'With compliance'
    COMPLIANCE_DONE = 'compliance_done', 'Compliance review complete'
    PENDING_BOARD = 'pending_board', 'Pending board decision'
    BOARD_APPROVED = 'board_approved', 'Board approved'
    BOARD_REJECTED = 'board_rejected', 'Board rejected'
    REJECTED = 'rejected', 'Rejected'
    ACCOUNT_CREATED = 'account_created', 'IPC account created'
    WITHDRAWN = 'withdrawn', 'Withdrawn by applicant'

    @classmethod
    def open_request_statuses(cls):
        """Requests that still reserve the registration number (no duplicate submissions)."""
        return [
            cls.PENDING_SA_REVIEW,
            cls.WITH_COMPLIANCE,
            cls.COMPLIANCE_DONE,
            cls.PENDING_BOARD,
            cls.BOARD_APPROVED,
        ]


class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    registration_number = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(regex=r'^[A-Z0-9]{6,12}$')],
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=InstitutionType.choices, default=InstitutionType.SCHOOL)

    address_street = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=100, blank=True)
    address_postal_code = models.CharField(max_length=30, blank=True)
    address_country = models.CharField(max_length=100, blank=True)

    primary_contact_email = models.EmailField(blank=True)
    secondary_contact_email = models.EmailField(blank=True)

    status = models.CharField(max_length=20, choices=InstitutionStatus.choices, default=InstitutionStatus.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.registration_number})"


class InstitutionOnboardingRequest(models.Model):
    """
    Public institution + IPC registration payload.
    Does not create User or active Institution until SA/onboarding workflow completes (per SRS/architecture).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=32, unique=True, editable=False, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=InstitutionOnboardingStatus.choices,
        default=InstitutionOnboardingStatus.PENDING_SA_REVIEW,
        db_index=True,
    )

    institution_name = models.CharField(max_length=255)
    institution_type = models.CharField(max_length=20, choices=InstitutionType.choices, default=InstitutionType.SCHOOL)
    registration_number = models.CharField(
        max_length=12,
        validators=[RegexValidator(regex=r'^[A-Z0-9]{6,12}$')],
        db_index=True,
    )

    address_street = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=100, blank=True)
    address_postal_code = models.CharField(max_length=30, blank=True)
    address_country = models.CharField(max_length=100, blank=True)

    primary_contact_email = models.EmailField()
    secondary_contact_email = models.EmailField(blank=True)

    ipc_first_name = models.CharField(max_length=150)
    ipc_last_name = models.CharField(max_length=150)
    ipc_phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reference_number} ({self.registration_number})'

    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = datetime.now().year
            for _ in range(20):
                candidate = f'ONB-{year}-{secrets.token_hex(3).upper()}'
                if not InstitutionOnboardingRequest.objects.filter(reference_number=candidate).exists():
                    self.reference_number = candidate
                    break
            else:
                self.reference_number = f'ONB-{year}-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)
