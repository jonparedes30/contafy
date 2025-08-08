from django.core.management.base import BaseCommand
from empresa.models import Empresa
from empresa.services.workflows_ia import ejecutar_workflows_automaticos

class Command(BaseCommand):
    help = 'Activa workflows automáticos de IA para todas las empresas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            help='Nombre específico de empresa (opcional)'
        )

    def handle(self, *args, **options):
        self.stdout.write("Activando workflows automáticos de IA...")
        
        if options['empresa']:
            try:
                empresa = Empresa.objects.get(nombre__icontains=options['empresa'])
                empresas = [empresa]
                self.stdout.write(f"Ejecutando para empresa: {empresa.nombre}")
            except Empresa.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Empresa '{options['empresa']}' no encontrada"))
                return
        else:
            empresas = Empresa.objects.all()
            self.stdout.write(f"Ejecutando para {empresas.count()} empresas")
        
        total_alertas = 0
        
        for empresa in empresas:
            self.stdout.write(f"\n--- {empresa.nombre} ---")
            
            try:
                resultados = ejecutar_workflows_automaticos(empresa)
                
                # Mostrar resultados
                workflows = resultados['workflows']
                
                # Stock bajo
                if workflows.get('stock_bajo'):
                    stock_count = len(workflows['stock_bajo'])
                    self.stdout.write(f"[STOCK] {stock_count} productos con stock bajo")
                    for item in workflows['stock_bajo'][:3]:  # Mostrar solo 3
                        self.stdout.write(f"  - {item['producto']}: {item['stock_actual']} unidades")
                    total_alertas += stock_count
                
                # Cobros vencidos
                if workflows.get('cobros_vencidos'):
                    cobros_count = len(workflows['cobros_vencidos'])
                    total_vencido = sum(c['monto'] for c in workflows['cobros_vencidos'])
                    self.stdout.write(f"[COBROS] {cobros_count} cuentas vencidas: ${total_vencido:.2f}")
                    total_alertas += cobros_count
                
                # Metas en riesgo
                if workflows.get('alertas_metas'):
                    metas_count = len(workflows['alertas_metas'])
                    self.stdout.write(f"[METAS] {metas_count} metas en riesgo")
                    total_alertas += metas_count
                
                # Flujo de caja crítico
                if workflows.get('flujo_caja'):
                    self.stdout.write(self.style.WARNING(f"[CRÍTICO] {workflows['flujo_caja']['mensaje']}"))
                    total_alertas += 1
                
                # Anomalías en ventas
                if workflows.get('anomalias_ventas'):
                    self.stdout.write(self.style.WARNING(f"[VENTAS] {workflows['anomalias_ventas']['mensaje']}"))
                    total_alertas += 1
                
                # WhatsApp
                if empresa.telefono_whatsapp:
                    self.stdout.write(f"[WHATSAPP] Alertas enviadas a {empresa.telefono_whatsapp}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error procesando {empresa.nombre}: {str(e)}"))
        
        self.stdout.write(f"\n{self.style.SUCCESS('Workflows ejecutados exitosamente!')}")
        self.stdout.write(f"Total de alertas generadas: {total_alertas}")
        
        if total_alertas > 0:
            self.stdout.write("\nRecomendaciones:")
            self.stdout.write("- Revisar productos con stock bajo")
            self.stdout.write("- Contactar clientes con pagos vencidos")
            self.stdout.write("- Ajustar estrategias para metas en riesgo")
        else:
            self.stdout.write(self.style.SUCCESS("¡Todo funcionando correctamente!"))