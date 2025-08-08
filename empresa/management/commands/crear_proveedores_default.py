from django.core.management.base import BaseCommand
from empresa.models import Empresa, Proveedor


class Command(BaseCommand):
    help = 'Crea proveedores por defecto para empresas que no tienen ninguno'

    def handle(self, *args, **options):
        empresas_sin_proveedores = []
        proveedores_creados = 0

        for empresa in Empresa.objects.all():
            if not Proveedor.objects.filter(empresa=empresa).exists():
                # Crear proveedor por defecto
                proveedor = Proveedor.objects.create(
                    empresa=empresa,
                    nombre='Proveedor General',
                    ruc='9999999999999',
                    telefono='',
                    email='',
                    direccion='',
                    dias_credito=30,
                    activo=True
                )
                empresas_sin_proveedores.append(empresa.nombre)
                proveedores_creados += 1

        if proveedores_creados > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se crearon {proveedores_creados} proveedores por defecto para las siguientes empresas:'
                )
            )
            for empresa_nombre in empresas_sin_proveedores:
                self.stdout.write(f'  - {empresa_nombre}')
        else:
            self.stdout.write(
                self.style.SUCCESS('Todas las empresas ya tienen al menos un proveedor.')
            )