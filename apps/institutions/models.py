import uuid
from django.core.validators import RegexValidator
from django.db import models

class InstitutionType(models.TextChoices):
    SCHOOL = 'school', 'School'
    UNIVERSITY = 'university', 'University'

class InstitutionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    REVOKED = 'revoked', 'Revoked'

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
