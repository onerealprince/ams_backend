from django.urls import path

from .views import institution_onboarding_register

urlpatterns = [
    path(
        'institutions/onboarding-requests/',
        institution_onboarding_register,
        name='institution_onboarding_register',
    ),
    # Backward-compatible alias (same handler)
    path('institutions/', institution_onboarding_register, name='institution_onboarding_register_legacy'),
]
