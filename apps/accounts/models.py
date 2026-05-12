from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    INSTITUTION_CONTACT = 'institution_contact', 'Institution Contact'
    OFFICER = 'officer', 'Accreditation Officer'
    INSPECTOR = 'inspector', 'Inspector'
    BOARD_MEMBER = 'board_member', 'Board Member'
    DG = 'dg', 'Director General'
    CASE_MANAGER = 'case_manager', 'Case Manager'
    ADMIN = 'admin', 'System Administrator'
    APPEALS_TRIBUNAL = 'appeals_tribunal', 'Appeals Tribunal User'


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        # Phase 1: SA / root accounts are created by developers; no registration OTP flow.
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)

    role = models.CharField(max_length=50, choices=UserRole.choices, default=UserRole.INSTITUTION_CONTACT)
    is_mfa_enabled = models.BooleanField(default=False)

    is_email_verified = models.BooleanField(default=False)
    email_otp_hash = models.CharField(max_length=128, blank=True)
    email_otp_created_at = models.DateTimeField(null=True, blank=True)
    # Login MFA OTP (after password); stored in DB so dev server reload does not drop it (unlike LocMem cache).
    login_otp_hash = models.CharField(max_length=128, blank=True)
    login_otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_resend_count = models.PositiveSmallIntegerField(default=0)
    otp_resend_window_started_at = models.DateTimeField(null=True, blank=True)
    otp_last_sent_at = models.DateTimeField(null=True, blank=True)

    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    institution = models.ForeignKey('institutions.Institution', null=True, blank=True, on_delete=models.SET_NULL)

    active_assignments_count = models.PositiveSmallIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
