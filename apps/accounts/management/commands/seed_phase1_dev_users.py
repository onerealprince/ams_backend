from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, UserRole
from apps.institutions.models import Institution


class Command(BaseCommand):
    help = (
        'Create or update Phase 1 dummy users (meeting docs: SA + IPC). '
        'Also marks existing superusers as email-verified so login works.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default='DevPass-AMS-2026!1',
            help='Password for seeded users (must meet strong password rules).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']

        verified_superusers = User.objects.filter(is_superuser=True).update(is_email_verified=True)
        if verified_superusers:
            self.stdout.write(self.style.SUCCESS(f'Marked {verified_superusers} superuser(s) as email-verified.'))

        sa, created = User.objects.get_or_create(
            email='sa@ams.dev',
            defaults={
                'first_name': 'System',
                'last_name': 'Admin',
                'role': UserRole.ADMIN,
                'is_email_verified': True,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            sa.set_password(password)
            sa.save()
            self.stdout.write(self.style.SUCCESS(f'Created SA: sa@ams.dev'))
        else:
            sa.set_password(password)
            sa.is_email_verified = True
            sa.role = UserRole.ADMIN
            sa.save()
            self.stdout.write(self.style.SUCCESS(f'Updated SA: sa@ams.dev'))

        institution, _ = Institution.objects.get_or_create(
            registration_number='DEV000000001',
            defaults={'name': 'Dev Institution (Phase 1)'},
        )

        ipc, ipc_created = User.objects.get_or_create(
            email='ipc@ams.dev',
            defaults={
                'first_name': 'IPC',
                'last_name': 'Contact',
                'role': UserRole.INSTITUTION_CONTACT,
                'institution': institution,
                'is_email_verified': True,
            },
        )
        if ipc_created:
            ipc.set_password(password)
            ipc.save()
            self.stdout.write(self.style.SUCCESS(f'Created IPC: ipc@ams.dev'))
        else:
            ipc.set_password(password)
            ipc.is_email_verified = True
            ipc.institution = institution
            ipc.role = UserRole.INSTITUTION_CONTACT
            ipc.save()
            self.stdout.write(self.style.SUCCESS(f'Updated IPC: ipc@ams.dev'))

        self.stdout.write('')
        self.stdout.write('Login with email + password, then OTP from console (dev email backend):')
        self.stdout.write(f'  SA:  sa@ams.dev  / {password}')
        self.stdout.write(f'  IPC: ipc@ams.dev / {password}')
