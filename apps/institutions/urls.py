from django.urls import path

from .views import institution_onboarding_register

urlpatterns = [
    path('institutions/', institution_onboarding_register, name='institution_onboarding_register'),
]
