import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Institution, InstitutionOnboardingRequest, InstitutionOnboardingStatus


REGISTRATION_NUMBER_PATTERN = re.compile(r'^[A-Z0-9]{6,12}$')


class InstitutionOnboardingRequestSerializer(serializers.ModelSerializer):
    """Public institution + IPC registration (pending onboarding request only)."""

    class Meta:
        model = InstitutionOnboardingRequest
        fields = (
            'institution_name',
            'institution_type',
            'registration_number',
            'address_street',
            'address_city',
            'address_postal_code',
            'address_country',
            'primary_contact_email',
            'secondary_contact_email',
            'ipc_first_name',
            'ipc_last_name',
            'ipc_phone',
        )
        extra_kwargs = {
            'institution_type': {'required': False},
            'address_street': {'required': False, 'allow_blank': True},
            'address_city': {'required': False, 'allow_blank': True},
            'address_postal_code': {'required': False, 'allow_blank': True},
            'address_country': {'required': False, 'allow_blank': True},
            'secondary_contact_email': {'required': False, 'allow_blank': True},
            'ipc_phone': {'required': False, 'allow_blank': True},
        }

    def validate_registration_number(self, value):
        raw = (value or '').strip().upper()
        if not REGISTRATION_NUMBER_PATTERN.match(raw):
            raise serializers.ValidationError(
                'Registration number must be 6–12 uppercase letters or digits (e.g. GSL123456).'
            )
        if Institution.objects.filter(registration_number=raw).exists():
            raise serializers.ValidationError('An institution with this registration number already exists.')

        blocking = InstitutionOnboardingRequest.objects.filter(
            registration_number=raw,
            status__in=InstitutionOnboardingStatus.open_request_statuses(),
        )
        if blocking.exists():
            raise serializers.ValidationError(
                'A registration request for this number is already in progress.'
            )
        return raw

    def validate_primary_contact_email(self, value):
        email = (value or '').strip().lower()
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('An account with this email already exists. Log in instead.')
        if InstitutionOnboardingRequest.objects.filter(
            primary_contact_email__iexact=email,
            status__in=InstitutionOnboardingStatus.open_request_statuses(),
        ).exists():
            raise serializers.ValidationError(
                'An onboarding request with this contact email is already in progress.'
            )
        return email
