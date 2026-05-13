from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.institutions.models import Institution

from .models import UserRole
from .serializers import (
    LoginStartSerializer,
    LoginVerifySerializer,
    RegisterSerializer,
    ResendOtpSerializer,
    VerifyOtpSerializer,
)
from .services import issue_email_otp, issue_login_otp, verify_email_otp, verify_login_otp


def _dashboard_path_for_role(role: str) -> str:
    return {
        UserRole.ADMIN: '/dashboard/system-administrator',
        UserRole.INSTITUTION_CONTACT: '/dashboard/ipc',
        UserRole.BOARD_MEMBER: '/dashboard/board-member',
        UserRole.OFFICER: '/dashboard/compliance',
        UserRole.INSPECTOR: '/dashboard/inspector',
        UserRole.DG: '/dashboard/dg',
        UserRole.CASE_MANAGER: '/dashboard/case-manager',
        UserRole.APPEALS_TRIBUNAL: '/dashboard/appeals-tribunal',
    }.get(role, '/dashboard')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({'id': user.id, 'email': user.email, 'role': getattr(user, 'role', None)})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    **Flow A — SRS self-service sign-up (Institution Primary Contact)**

    Creates `Institution` + `User` immediately, then sends registration email OTP.
    Client completes `POST /api/v1/auth/verify-otp/`.

    **Flow B — no portal account yet:** use `POST /api/v1/institutions/onboarding-requests/`
    (anonymous onboarding; SA/compliance/board then create the user).

    Disable Flow A in production if only Flow B is allowed: `AMS_ALLOW_SELF_SERVICE_REGISTRATION=false`.
    """
    if not getattr(settings, 'AMS_ALLOW_SELF_SERVICE_REGISTRATION', True):
        return Response(
            {
                'detail': (
                    'Self-service sign-up is disabled. Submit an institution onboarding request '
                    'at POST /api/v1/institutions/onboarding-requests/ or contact your administrator.'
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        validate_password(data['password'])
    except ValidationError as exc:
        return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    reg_no = data['institution_registration_number']
    with transaction.atomic():
        if User.objects.filter(email__iexact=data['email'].strip()).exists():
            return Response({'detail': 'Account exists. Log in instead?'}, status=status.HTTP_400_BAD_REQUEST)

        institution = Institution.objects.create(
            name=data['institution_name'],
            registration_number=reg_no,
        )

        user = User.objects.create_user(
            email=data['email'].strip().lower(),
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone_number=data.get('phone_number', ''),
            institution=institution,
        )

    try:
        issue_email_otp(user)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            'detail': 'OTP sent to email.',
            'registration_flow': 'self_service_portal_account',
            'next_step': 'POST /api/v1/auth/verify-otp/ with email and otp',
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = VerifyOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=data['email'].strip())
    except User.DoesNotExist:
        return Response({'detail': 'Provide a valid email'}, status=status.HTTP_400_BAD_REQUEST)

    ok = verify_email_otp(user, data['otp'])
    if not ok:
        return Response(
            {
                'detail': (
                    'Invalid or expired registration OTP. '
                    'For login MFA after password, use POST /api/v1/auth/login/verify/ instead.'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({'detail': 'Email verified.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    serializer = ResendOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=data['email'].strip())
    except User.DoesNotExist:
        return Response({'detail': 'Provide a valid email'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        issue_email_otp(user)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'OTP resent.'})


def _login_precheck_user(user):
    """Shared gate before password or OTP MFA for existing accounts."""
    if user.locked_until and user.locked_until > timezone.now():
        return Response({'detail': 'Too many failed attempts'}, status=status.HTTP_403_FORBIDDEN)
    if not user.is_email_verified:
        return Response(
            {
                'detail': (
                    'This email is not verified yet. '
                    'If you self-registered, complete OTP verification first, '
                    'or ask an admin to verify the account.'
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


@api_view(['POST'])
@permission_classes([AllowAny])
def login_start(request):
    """Phase 1: validate email + password, then send login OTP (MFA) to email."""
    serializer = LoginStartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email_raw = serializer.validated_data['email'].strip()
    password = serializer.validated_data['password']

    User = get_user_model()
    user = User.objects.filter(email__iexact=email_raw).first()
    if not user:
        return Response({'detail': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

    blocked = _login_precheck_user(user)
    if blocked is not None:
        return blocked

    auth_user = authenticate(request, username=user.email, password=password)
    if auth_user is None:
        user.failed_login_attempts = min(user.failed_login_attempts + 1, 100)
        if user.failed_login_attempts >= 5:
            user.locked_until = timezone.now() + timedelta(minutes=15)
            user.failed_login_attempts = 0
            user.save(update_fields=['locked_until', 'failed_login_attempts'])
        else:
            user.save(update_fields=['failed_login_attempts'])
        if user.check_password(password) and not user.is_active:
            return Response({'detail': 'This account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)

    user.failed_login_attempts = 0
    user.locked_until = None
    user.save(update_fields=['failed_login_attempts', 'locked_until'])

    try:
        issue_login_otp(user)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'OTP sent to email.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_verify(request):
    """Phase 1: verify login OTP and return JWTs plus role (session substitute)."""
    serializer = LoginVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email_raw = serializer.validated_data['email'].strip()
    otp = serializer.validated_data['otp']

    User = get_user_model()
    try:
        user = User.objects.get(email__iexact=email_raw)
    except User.DoesNotExist:
        return Response({'detail': 'Provide a valid email'}, status=status.HTTP_400_BAD_REQUEST)

    blocked = _login_precheck_user(user)
    if blocked is not None:
        return blocked

    if not verify_login_otp(user, otp):
        return Response(
            {
                'detail': (
                    'Invalid or expired login code. '
                    'Use the code from the "AMS Login OTP" email and POST to /api/v1/auth/login/verify/.'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,
            'dashboard_path': _dashboard_path_for_role(user.role),
        },
        status=status.HTTP_200_OK,
    )
