import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.benchmarking_real_service import BenchmarkingRealService
from empresa.models import Empresa

# Probar con empresa Angel
empresa = Empresa.objects.get(id=4)
print(f"Empresa: {empresa.nombre}")
print(f"Usuario empresa: {empresa.usuarios.first()}")

resultado = BenchmarkingRealService.obtener_benchmarking_completo(empresa)
print(f"Resultado keys: {resultado.keys()}")
print(f"Comparaciones: {len(resultado['comparaciones'])}")
print(f"Posiciones: {len(resultado['posiciones'])}")
print(f"Recomendaciones: {len(resultado['recomendaciones'])}")

for nivel, datos in resultado['comparaciones'].items():
    if datos['tiene_datos']:
        print(f"{nivel}: {datos['total_empresas']} empresas")
    else:
        print(f"{nivel}: {datos['razon']}")