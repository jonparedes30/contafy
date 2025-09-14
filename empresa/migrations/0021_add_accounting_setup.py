# Generated migration for accounting setup
from django.db import migrations

def create_accounting_setup_data(apps, schema_editor):
    """Create basic accounting setup data if needed"""
    pass

def reverse_accounting_setup_data(apps, schema_editor):
    """Reverse accounting setup data"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0020_add_slug_and_audit_fields'),
    ]

    operations = [
        migrations.RunPython(
            create_accounting_setup_data,
            reverse_accounting_setup_data,
        ),
    ]