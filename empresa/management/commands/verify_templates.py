from django.core.management.base import BaseCommand
from django.template import loader
from django.template.base import TemplateSyntaxError
import sys

class Command(BaseCommand):
    help = 'Verifies template syntax'

    def handle(self, *args, **options):
        try:
            from django.template import Template, Context
            Template("{% ifequal 1 1 %}ok{% endifequal %}")
            self.stdout.write(self.style.SUCCESS("IFEQUAL_SUPPORTED"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"IFEQUAL_NOT_SUPPORTED: {e}"))

        try:
            loader.get_template('empresa/listar_productos_final.html')
            self.stdout.write(self.style.SUCCESS("TEMPLATE_VALID"))
        except TemplateSyntaxError as e:
            self.stdout.write(self.style.ERROR(f"TEMPLATE_ERROR: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"OTHER_ERROR: {e}"))
