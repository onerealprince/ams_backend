from django.urls import path

from .views import login_start, login_verify, me, register, resend_otp, verify_otp

urlpatterns = [
    path('auth/register/', register, name='auth_register'),
    path('auth/verify-otp/', verify_otp, name='auth_verify_otp'),
    path('auth/resend-otp/', resend_otp, name='auth_resend_otp'),
    path('auth/login/', login_start, name='auth_login_start'),
    path('auth/login/verify/', login_verify, name='auth_login_verify'),
    path('me/', me, name='me'),
]
