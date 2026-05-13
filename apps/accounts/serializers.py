import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.institutions.models import Institution, InstitutionOnboardingRequest, InstitutionOnboardingStatus


User = get_user_model()
REGISTRATION_NUMBER_PATTERN = re.compile(r'^[A-Z0-9]{6,12}$')


class RegisterSerializer(serializers.Serializer):
    """
    SRS-style self-service sign-up: creates Institution + User immediately, then email OTP.

    Use this when the IPC may create their own portal account. For “no account until SA/board
    approves”, use POST /api/v1/institutions/onboarding-requests/ instead (anonymous onboarding).
    """

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    institution_name = serializers.CharField(max_length=255)
    institution_registration_number = serializers.CharField(max_length=12)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=12)

    def validate_email(self, value):
        email = (value or '').strip().lower()
        if InstitutionOnboardingRequest.objects.filter(
            primary_contact_email__iexact=email,
            status__in=InstitutionOnboardingStatus.open_request_statuses(),
        ).exists():
            raise serializers.ValidationError(
                'An institution onboarding request is already in progress for this email. '
                'Wait for staff to finish review, or contact support—do not use self-service sign-up yet.'
            )
        return value

    def validate_institution_registration_number(self, value):
        raw = (value or '').strip().upper()
        if not REGISTRATION_NUMBER_PATTERN.match(raw):
            raise serializers.ValidationError(
                'Registration number must be 6–12 uppercase letters or digits (e.g. GSL123456).'
            )
        if Institution.objects.filter(registration_number=raw).exists():
            raise serializers.ValidationError(
                'This institution is already registered. Sign in with your institutional email instead.'
            )
        blocking = InstitutionOnboardingRequest.objects.filter(
            registration_number=raw,
            status__in=InstitutionOnboardingStatus.open_request_statuses(),
        )
        if blocking.exists():
            raise serializers.ValidationError(
                'An onboarding request is already in progress for this registration number. '
                'Wait for staff approval before creating a portal account, or contact support.'
            )
        return raw


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=10)


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginStartSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=10)
