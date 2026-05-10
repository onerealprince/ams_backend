import uuid

from django.db import models


class ApplicationType(models.TextChoices):
    SCHOOL = 'school', 'School'
    PROGRAMME = 'programme', 'Programme'
    UNIVERSITY_PROVISIONAL = 'university_provisional', 'University Provisional'
    UNIVERSITY_FULL = 'university_full', 'University Full'


class ApplicationStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    PENDING_OFFICER_ASSIGNMENT = 'pending_officer_assignment', 'Pending Officer Assignment'
    UNDER_OFFICER_REVIEW = 'under_officer_review', 'Under Officer Review'
    ADDITIONAL_INFO_REQUESTED = 'additional_info_requested', 'Additional Information Requested'
    SITE_INSPECTION_SCHEDULED = 'site_inspection_scheduled', 'Site Inspection Scheduled'
    PENDING_BOARD_DECISION = 'pending_board_decision', 'Pending Board Decision'
    BOARD_DECISION_RECORDED = 'board_decision_recorded', 'Board Decision Recorded'
    LICENSE_ISSUED = 'license_issued', 'License Issued'


class AccreditationApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    reference_number = models.CharField(max_length=100, unique=True)
    institution = models.ForeignKey('institutions.Institution', on_delete=models.CASCADE, related_name='applications')
    type = models.CharField(max_length=30, choices=ApplicationType.choices)
    form_data = models.JSONField(default=dict)

    current_status = models.CharField(max_length=60, choices=ApplicationStatus.choices, default=ApplicationStatus.DRAFT)
    current_step = models.CharField(max_length=100, blank=True)

    submission_date = models.DateTimeField(null=True, blank=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference_number
