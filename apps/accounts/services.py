import hashlib
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone


OTP_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_RESENDS_PER_WINDOW = 5
RESEND_WINDOW = timedelta(hours=1)


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def generate_otp(length: int = 6) -> str:
    digits = '0123456789'
    return ''.join(secrets.choice(digits) for _ in range(length))


def issue_email_otp(user, *, subject: str = 'AMS Email Verification OTP') -> None:
    now = timezone.now()

    if user.otp_last_sent_at and now - user.otp_last_sent_at < RESEND_COOLDOWN:
        raise ValueError('OTP Already Submitted')

    if not user.otp_resend_window_started_at or now - user.otp_resend_window_started_at >= RESEND_WINDOW:
        user.otp_resend_window_started_at = now
        user.otp_resend_count = 0

    if user.otp_resend_count >= MAX_RESENDS_PER_WINDOW:
        raise ValueError('Maximum Resend Attempt Reached')

    otp = generate_otp()
    user.email_otp_hash = _hash_otp(otp)
    user.email_otp_created_at = now
    user.otp_last_sent_at = now
    user.otp_resend_count += 1
    user.save(update_fields=[
        'email_otp_hash',
        'email_otp_created_at',
        'otp_last_sent_at',
        'otp_resend_count',
        'otp_resend_window_started_at',
    ])

    send_mail(
        subject=subject,
        message=f'Your verification OTP is: {otp}. It expires in 10 minutes.',
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


def verify_email_otp(user, otp: str) -> bool:
    if not user.email_otp_created_at or not user.email_otp_hash:
        return False

    now = timezone.now()
    if now - user.email_otp_created_at > OTP_TTL:
        return False

    if _hash_otp(otp) != user.email_otp_hash:
        return False

    user.is_email_verified = True
    user.email_otp_hash = ''
    user.save(update_fields=['is_email_verified', 'email_otp_hash'])
    return True
