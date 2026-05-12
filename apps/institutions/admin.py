from django.contrib import admin

from .models import Institution, InstitutionOnboardingRequest


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'type', 'status', 'created_at')
    search_fields = ('name', 'registration_number', 'primary_contact_email')


@admin.register(InstitutionOnboardingRequest)
class InstitutionOnboardingRequestAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number',
        'institution_name',
        'registration_number',
        'status',
        'primary_contact_email',
        'created_at',
    )
    list_filter = ('status', 'institution_type')
    search_fields = ('reference_number', 'institution_name', 'registration_number', 'primary_contact_email')
    readonly_fields = ('id', 'reference_number', 'created_at', 'updated_at')
