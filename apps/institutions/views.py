from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import InstitutionOnboardingRequestSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def institution_onboarding_register(request):
    """
    **Flow B — Anonymous institution onboarding (architecture / meeting flow)**

    Creates `InstitutionOnboardingRequest` only. **No** `User` or live `Institution` record yet.
    After SA → compliance → board → account creation, the IPC gets credentials / onboarding link.

    **Flow A — SRS self-service portal account:** `POST /api/v1/auth/register/` then verify-otp.

    Canonical URL: `POST /api/v1/institutions/onboarding-requests/`
    (`POST /api/v1/institutions/` is kept as an alias.)
    """
    serializer = InstitutionOnboardingRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    return Response(
        {
            'id': str(instance.id),
            'reference_number': instance.reference_number,
            'status': instance.status,
            'detail': 'Registration submitted. You will be contacted after review.',
            'registration_flow': 'anonymous_onboarding_no_portal_account',
            'next_step': 'Wait for staff; no login until an account is created for you.',
        },
        status=status.HTTP_201_CREATED,
    )
