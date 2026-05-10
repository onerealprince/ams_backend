from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.institutions.models import Institution

from .serializers import RegisterSerializer, ResendOtpSerializer, VerifyOtpSerializer
from .services import issue_email_otp, verify_email_otp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({'id': user.id, 'email': user.email, 'role': getattr(user, 'role', None)})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        validate_password(data['password'])
    except ValidationError as exc:
        return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    with transaction.atomic():
        if User.objects.filter(email=data['email']).exists():
            return Response({'detail': 'Account exists. Log in instead?'}, status=status.HTTP_400_BAD_REQUEST)

        institution = Institution.objects.create(
            name=data['institution_name'],
            registration_number=data['institution_registration_number'],
        )

        user = User.objects.create_user(
            email=data['email'],
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

    return Response({'detail': 'OTP sent to email.'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = VerifyOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    User = get_user_model()
    try:
        user = User.objects.get(email=data['email'])
    except User.DoesNotExist:
        return Response({'detail': 'Provide a valid email'}, status=status.HTTP_400_BAD_REQUEST)

    ok = verify_email_otp(user, data['otp'])
    if not ok:
        return Response({'detail': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'Email verified.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    serializer = ResendOtpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    User = get_user_model()
    try:
        user = User.objects.get(email=data['email'])
    except User.DoesNotExist:
        return Response({'detail': 'Provide a valid email'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        issue_email_otp(user)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'detail': 'OTP resent.'})


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        User = get_user_model()
        email = request.data.get('email')
        if email:
            user = User.objects.filter(email=email).first()
            if user and user.locked_until and user.locked_until > timezone.now():
                return Response({'detail': 'Too many failed attempts'}, status=status.HTTP_403_FORBIDDEN)
            if user and not user.is_email_verified:
                return Response({'detail': "Account doesn’t exist"}, status=status.HTTP_403_FORBIDDEN)

        response = super().post(request, *args, **kwargs)

        if response.status_code != 200 and email:
            user = User.objects.filter(email=email).first()
            if user:
                user.failed_login_attempts = min(user.failed_login_attempts + 1, 100)
                if user.failed_login_attempts >= 5:
                    user.locked_until = timezone.now() + timedelta(minutes=15)
                    user.failed_login_attempts = 0
                    user.save(update_fields=['locked_until', 'failed_login_attempts'])
                else:
                    user.save(update_fields=['failed_login_attempts'])

        if response.status_code == 200 and email:
            user = User.objects.filter(email=email).first()
            if user:
                user.failed_login_attempts = 0
                user.locked_until = None
                user.save(update_fields=['failed_login_attempts', 'locked_until'])

        return response
