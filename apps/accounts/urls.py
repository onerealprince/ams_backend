from django.urls import path

from .views import CustomTokenObtainPairView, me, register, resend_otp, verify_otp

urlpatterns = [
    path('auth/register/', register, name='auth_register'),
    path('auth/verify-otp/', verify_otp, name='auth_verify_otp'),
    path('auth/resend-otp/', resend_otp, name='auth_resend_otp'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair_custom'),
    path('me/', me, name='me'),
]
