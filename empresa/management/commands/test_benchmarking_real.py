from django.core.management.base import BaseCommand
from empresa.models import Empresa
from empresa.services.benchmarking_real_service import BenchmarkingRealService

class Command(BaseCommand):
    help = 'Prueba el sistema de benchmarking con datos reales'

    def add_arguments(self, parser):
        parser.add_argument('--empresa-id', type=int, help='ID de la empresa a analizar')

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                self.analizar_empresa(empresa)
            except Empresa.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Empresa con ID {empresa_id} no encontrada'))
        else:
            # Analizar todas las empresas de manufactura
            empresas_manufactura = Empresa.objects.filter(categoria='manufactura')
            for empresa in empresas_manufactura:
                self.analizar_empresa(empresa)
                self.stdout.write('-' * 50)

    def analizar_empresa(self, empresa):
        self.stdout.write(f"\n=== ANALISIS BENCHMARKING: {empresa.nombre} ===")
        self.stdout.write(f"Categoria: {empresa.get_categoria_display()}")
        self.stdout.write(f"Tipo: {empresa.tipo_negocio}")
        self.stdout.write(f"Ubicacion: {empresa.ciudad}, {empresa.provincia}")
        
        # Obtener benchmarking completo
        resultado = BenchmarkingRealService.obtener_benchmarking_completo(empresa)
        
        # Mostrar métricas propias
        metricas = resultado['metricas_propias']
        self.stdout.write(f"\n--- METRICAS PROPIAS ---")
        self.stdout.write(f"Ventas mensuales: ${metricas['ventas_mensuales']:,.2f}")
        self.stdout.write(f"Margen bruto: {metricas['margen_bruto']:.1f}%")
        self.stdout.write(f"Margen neto: {metricas['margen_neto']:.1f}%")
        self.stdout.write(f"Crecimiento mensual: {metricas['crecimiento_mensual']:.1f}%")
        
        # Mostrar comparaciones
        self.stdout.write(f"\n--- COMPARACIONES ---")
        for nivel, datos in resultado['comparaciones'].items():
            if datos['tiene_datos']:
                self.stdout.write(f"\n{nivel.upper()}: {datos['nombre_grupo']}")
                self.stdout.write(f"  Empresas comparables: {datos['total_empresas']}")
                self.stdout.write(f"  Ventas promedio: ${datos['ventas_promedio']:,.2f}")
                self.stdout.write(f"  Margen neto promedio: {datos['margen_neto_promedio']:.1f}%")
                
                # Comparación
                if metricas['ventas_mensuales'] > datos['ventas_promedio']:
                    self.stdout.write(f"  [+] Ventas: SUPERIOR al promedio")
                else:
                    self.stdout.write(f"  [-] Ventas: Por debajo del promedio")
                    
                if metricas['margen_neto'] > datos['margen_neto_promedio']:
                    self.stdout.write(f"  [+] Rentabilidad: SUPERIOR al promedio")
                else:
                    self.stdout.write(f"  [-] Rentabilidad: Por debajo del promedio")
            else:
                self.stdout.write(f"\n{nivel.upper()}: {datos['razon']}")
        
        # Mostrar posiciones
        self.stdout.write(f"\n--- POSICIONES ---")
        if resultado['posiciones']:
            for nivel, pos in resultado['posiciones'].items():
                self.stdout.write(f"{nivel}: Top {pos['percentil_ventas']}% en ventas, Top {pos['percentil_margen']}% en margen")
        else:
            self.stdout.write("No hay posiciones calculables (datos insuficientes)")
        
        # Mostrar recomendaciones
        self.stdout.write(f"\n--- RECOMENDACIONES ---")
        if resultado['recomendaciones']:
            for rec in resultado['recomendaciones']:
                icon = "[OK]" if rec['tipo'] == 'success' else "[WARN]" if rec['tipo'] == 'warning' else "[INFO]"
                area = rec.get('area', 'General')
                self.stdout.write(f"{icon} {area}: {rec['mensaje']}")
                if 'accion' in rec:
                    self.stdout.write(f"   -> {rec['accion']}")
        else:
            self.stdout.write("No hay recomendaciones disponibles (datos insuficientes)")