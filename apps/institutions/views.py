from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import InstitutionOnboardingRequestSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def institution_onboarding_register(request):
    """
    Public institution + IPC registration (architecture: POST /api/v1/institutions/).
    Creates InstitutionOnboardingRequest for SA/compliance/board workflow — no User yet.
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
        },
        status=status.HTTP_201_CREATED,
    )
