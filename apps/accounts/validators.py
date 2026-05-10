import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    def validate(self, password, user=None):
        errors = []

        if len(password) < 12:
            errors.append('Password must be at least 12 characters long.')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least 1 uppercase letter.')
        if not re.search(r'\d', password):
            errors.append('Password must contain at least 1 number.')
        if not re.search(r'[^A-Za-z0-9]', password):
            errors.append('Password must contain at least 1 special character.')

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return 'Your password must be at least 12 characters long and include uppercase, number, and special character.'
