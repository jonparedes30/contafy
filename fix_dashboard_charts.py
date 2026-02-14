import os

content = """{% extends "empresa/base.html" %}
{% load empresa_filters %}
{% load l10n %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<div class="container-fluid mt-4">
  <!-- Header Clean -->
  <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 page-header">
    <div>
      <h1 class="h3 mb-1 fw-bold text-dark">Dashboard Financiero</h1>
      <p class="text-muted mb-0">Vista operativa en tiempo real</p>
    </div>
    <form method="get" class="d-flex flex-wrap gap-2 align-items-end">
      <div>
        <label class="form-label mb-1 small text-muted">Desde</label>
        <input type="date" name="fecha_inicio" class="form-control form-control-sm"
          value="{{ request.GET.fecha_inicio|default:'' }}">
      </div>
      <div>
        <label class="form-label mb-1 small text-muted">Hasta</label>
        <input type="date" name="fecha_fin" class="form-control form-control-sm"
          value="{{ request.GET.fecha_fin|default:'' }}">
      </div>
      <button type="submit" class="btn btn-primary btn-sm">
        <i class="bi bi-funnel"></i> Filtrar
      </button>
      <a href="{% url 'empresa:dashboard' %}" class="btn btn-outline-secondary btn-sm">
        <i class="bi bi-arrow-clockwise"></i>
      </a>
    </form>
  </div>

  <!-- KPIs filtrados - Clean Style -->
  <div class="row g-4 mb-4">
    <div class="col-xl-3 col-md-6">
      <div class="card kpi-card success h-100">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="kpi-icon-wrapper success mb-0">
              <i class="bi bi-currency-dollar"></i>
            </div>
            <span class="badge bg-success bg-opacity-10 text-success rounded-pill px-2 py-1" id="badge-ventas">Up</span>
          </div>
          <div class="kpi-value" id="kpi-ventas">${{ ventas|floatformat:2 }}</div>
          <div class="kpi-label">Ventas Totales</div>
        </div>
      </div>
    </div>
    <div class="col-xl-3 col-md-6">
      <div class="card kpi-card danger h-100">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="kpi-icon-wrapper danger mb-0">
              <i class="bi bi-cash-stack"></i>
            </div>
            <span class="badge bg-danger bg-opacity-10 text-danger rounded-pill px-2 py-1" id="badge-gastos">Down</span>
          </div>
          <div class="kpi-value" id="kpi-gastos">${{ gastos|floatformat:2 }}</div>
          <div class="kpi-label">Gastos Totales</div>
        </div>
      </div>
    </div>
    <div class="col-xl-3 col-md-6">
      <div class="card kpi-card warning h-100">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="kpi-icon-wrapper warning mb-0">
              <i class="bi bi-bag-check"></i>
            </div>

          </div>
          <div class="kpi-value" id="kpi-compras">${{ compras|floatformat:2 }}</div>
          <div class="kpi-label">Compras Totales</div>
        </div>
      </div>
    </div>
    <div class="col-xl-3 col-md-6">
      <div class="card kpi-card primary h-100">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="kpi-icon-wrapper primary mb-0">
              <i class="bi bi-piggy-bank"></i>
            </div>
            <span class="badge bg-primary bg-opacity-10 text-primary rounded-pill px-2 py-1"
              id="badge-utilidad">Net</span>
          </div>
          <div class="kpi-value" id="kpi-utilidad">${{ utilidad_neta|floatformat:2 }}</div>
          <div class="kpi-label">Utilidad Neta</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Gráfico de barras: Ventas vs Gastos -->
  <div class="row mb-4">
    <div class="col-12">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-bar-chart text-success me-2"></i>
            Análisis de Ventas vs Gastos
          </h5>
          <div class="d-flex gap-3">
            <div class="d-flex align-items-center">
              <span class="chart-legend-item bg-success me-2"></span>
              <span class="small text-muted">Ventas</span>
            </div>
            <div class="d-flex align-items-center">
              <span class="chart-legend-item bg-danger me-2"></span>
              <span class="small text-muted">Gastos</span>
            </div>
          </div>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 400px;">
            <canvas id="ventasGastosChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Gráfico de distribución de gastos -->
  <div class="row mb-4">
    <div class="col-12">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-pie-chart text-info me-2"></i>
            Top 10 Gastos por Descripción
          </h5>
          <div class="d-flex align-items-center" data-bs-toggle="tooltip" title="{{ mensaje_gasto_frecuente }}">
            <i class="bi bi-info-circle text-muted"></i>
          </div>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 400px;">
            <canvas id="distribucionGastosChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Top 5 productos y productos sin movimiento -->
  <div class="row mb-4 g-4">
    <div class="col-md-8">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-trophy text-warning me-2"></i>
            Top 5 Productos Más Vendidos
          </h5>
          <small class="text-muted">{{ mensaje_producto_mas_vendido }}</small>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 350px;">
            <canvas id="productosMasVendidosChart"></canvas>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-exclamation-triangle text-danger me-2"></i>
            Productos sin Movimiento
          </h5>
        </div>
        <div class="card-body">
          <div class="text-center mb-4">
            <div class="display-6 fw-bold text-danger">{{ productos_criticos_count }}</div>
            <small class="text-muted">Sin ventas (30 días)</small>
          </div>
          {% if productos_sin_movimiento %}
          <div class="list-group list-group-flush small" style="max-height: 250px; overflow-y: auto;">
            {% for producto in productos_sin_movimiento %}
            <div class="list-group-item px-0 py-2 border-bottom-dashed">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <div class="fw-semibold text-dark">{{ producto.nombre|truncatechars:20 }}</div>
                  <div class="text-muted" style="font-size: 0.75rem;">Stock: {{ producto.stock }}</div>
                </div>
                <div class="text-end text-danger fw-bold">
                  ${{ producto.valor_inmovilizado|floatformat:0 }}
                </div>
              </div>
            </div>
            {% endfor %}
          </div>
          {% else %}
          <div class="text-center text-success py-4">
            <i class="bi bi-check-circle fs-3 mb-2"></i>
            <p class="small mb-0">¡Inventario saludable!</p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>



  <!-- NUEVOS REPORTES COMERCIALES -->



  <!-- Rotación de inventario y márgenes por categoría -->
  <div class="row mb-4 g-4">
    <div class="col-md-8">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-arrow-repeat text-info me-2"></i>
            Rotación de Inventario
          </h5>
          <small class="text-muted">
            {% if user.empresa.categoria == 'manufactura' %}
            Materias primas vs Productos manufacturados
            {% else %}
            Velocidad de venta por categoría
            {% endif %}
          </small>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 350px;">
            <canvas id="rotacionInventarioChart"></canvas>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-percent text-success me-2"></i>
            Márgenes
          </h5>
          <small class="text-muted">Top: {{ categoria_mas_rentable }}</small>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 350px;">
            <canvas id="margenesCategoriaChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Análisis de rentabilidad temporal -->
  <div class="row mb-4">
    <div class="col-12">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-graph-up-arrow text-primary me-2"></i>
            Evolución de Rentabilidad
          </h5>
          <div class="d-flex gap-3">
            <div class="d-flex align-items-center">
              <span class="chart-legend-item bg-success me-2"></span>
              <span class="small text-muted">Bruto</span>
            </div>
            <div class="d-flex align-items-center">
              <span class="chart-legend-item bg-primary me-2"></span>
              <span class="small text-muted">Neto</span>
            </div>
          </div>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 400px;">
            <canvas id="rentabilidadTemporalChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Gráfico de histórico de utilidades -->
  <div class="row mb-4">
    <div class="col-12">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-graph-up text-primary me-2"></i>
            Histórico de Utilidades
          </h5>
          <div class="d-flex align-items-center">
            <span class="badge bg-light text-dark border">
              <i class="bi bi-info-circle me-1"></i> {{ mensaje_tendencia }}
            </span>
          </div>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 400px;">
            <canvas id="historicoUtilidadesChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>




  <!-- Comparación con el Sector -->
  <div class="row mb-4">
    <div class="col-md-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-bar-chart-line text-primary me-2"></i>
            Comparación con el Sector
          </h5>
          <small class="text-muted">Tu margen vs promedio del sector {{ user.empresa.categoria }}</small>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 300px;">
            <canvas id="comparacionSectorChart"></canvas>
          </div>
        </div>
      </div>
    </div>
    <div class="col-md-6">
      <div class="card border-0 shadow-sm h-100">
        <div class="card-header bg-white py-3">
          <h5 class="mb-0 fw-bold">
            <i class="bi bi-speedometer2 text-warning me-2"></i>
            Rotación vs Benchmark
          </h5>
          <small class="text-muted">Tu rotación: {{ rotacion_promedio }}x vs sector: {{ rotacion_sector }}x</small>
        </div>
        <div class="card-body">
          <div class="chart-container" style="height: 300px;">
            <canvas id="rotacionBenchmarkChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- KPIs extras -->
  <div class="row mb-4 g-4">
    <!-- Margen Neto -->
    <div class="col-lg-3 col-md-6">
      <div class="card border-0 shadow-sm h-100 hover-scale">
        <div class="card-body text-center p-4">
          <div class="mb-3 text-primary">
            <i class="bi bi-percent fs-1"></i>
          </div>
          <h3 class="fw-bold mb-1">{{ margen_neto|floatformat:2 }}%</h3>
          <div class="text-muted small text-uppercase fw-bold">Margen Neto</div>
        </div>
      </div>
    </div>
    <!-- Ratio Gastos/Ventas -->
    <div class="col-lg-3 col-md-6">
      <div class="card border-0 shadow-sm h-100 hover-scale">
        <div class="card-body text-center p-4">
          <div class="mb-3 text-danger">
            <i class="bi bi-pie-chart fs-1"></i>
          </div>
          <h3 class="fw-bold mb-1" id="kpi-ratio">{{ ratio_gastos_ventas|floatformat:2 }}%</h3>
          <div class="text-muted small text-uppercase fw-bold">Ratio Gastos/Ventas</div>
        </div>
      </div>
    </div>
    <!-- Rotación Promedio -->
    <div class="col-lg-3 col-md-6">
      <div class="card border-0 shadow-sm h-100 hover-scale">
        <div class="card-body text-center p-4">
          <div class="mb-3 text-info">
            <i class="bi bi-arrow-repeat fs-1"></i>
          </div>
          <h3 class="fw-bold mb-1">{{ rotacion_promedio }}x</h3>
          <div class="text-muted small text-uppercase fw-bold">Rotación Promedio</div>
        </div>
      </div>
    </div>
    <!-- Productos Críticos -->
    <div class="col-lg-3 col-md-6">
      <div class="card border-0 shadow-sm h-100 hover-scale">
        <div class="card-body text-center p-4">
          <div class="mb-3 text-warning">
            <i class="bi bi-exclamation-triangle fs-1"></i>
          </div>
          <h3 class="fw-bold mb-1">{{ productos_criticos_count }}</h3>
          <div class="text-muted small text-uppercase fw-bold">Productos Críticos</div>
        </div>
      </div>
    </div>
    <!-- Categoría Más Rentable -->
    <div class="col-lg-3 col-md-6">
      <div class="card border-0 shadow-sm h-100 hover-scale">
        <div class="card-body text-center p-4">
          <div class="mb-3 text-success">
            <i class="bi bi-trophy fs-1"></i>
          </div>
          <h5 class="fw-bold mb-1 text-truncate" title="{{ categoria_mas_rentable }}">{{
            categoria_mas_rentable|default:"N/A" }}</h5>
          <div class="text-muted small text-uppercase fw-bold">Categoría Top</div>
        </div>
      </div>
    </div>
    <!-- Estado Actual -->
    <div class="col-lg-3 col-md-6">
      <div class="card border-0 shadow-sm h-100 hover-scale">
        <div class="card-body text-center p-4">
          <div class="mb-3">
            <i
              class="bi bi-bell-fill fs-1 {% if estado_actual == 'Saludable' %}text-success{% elif estado_actual == 'Estable' %}text-warning{% else %}text-danger{% endif %}"></i>
          </div>
          <span
            class="badge rounded-pill px-3 py-2 mb-1 fs-6 {% if estado_actual == 'Saludable' %}bg-success{% elif estado_actual == 'Estable' %}bg-warning text-dark{% else %}bg-danger{% endif %}">
            {{ estado_actual }}
          </span>
          <div class="text-muted small text-uppercase fw-bold mt-2">Estado Actual</div>
        </div>
      </div>
    </div>
    <!-- Última actualización -->
    <div class="col-lg-6 col-md-12">
      <div class="card border-0 shadow-sm h-100 bg-light">
        <div class="card-body d-flex flex-column justify-content-center align-items-center p-4">
          <div class="d-flex align-items-center mb-3">
            <i class="bi bi-clock-history fs-4 text-muted me-2"></i>
            <span class="text-muted">Última actualización</span>
          </div>
          <h5 class="fw-bold mb-3" id="kpi-actualizacion">{{ fecha_ultima_actualizacion }}</h5>
          <button onclick="window.location.href='{% url 'empresa:dashboard' %}'"
            class="btn btn-outline-primary btn-sm rounded-pill px-4">
            <i class="bi bi-arrow-clockwise me-1"></i> Actualizar Ahora
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Scripts para animaciones y gráficos -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
<script>
  document.addEventListener('DOMContentLoaded', function () {
    // Debug: Verificar datos recibidos
    console.log('DEBUG - Datos recibidos en JavaScript:');
    console.log('Labels:', {{ labels| safe }});
  console.log('Ventas data:', {{ ventas_data| safe }});
  console.log('Gastos data:', {{ gastos_data| safe }});
  console.log('Descripciones gastos:', {{ descripciones_gastos| safe }});
  console.log('Montos gastos:', {{ montos_gastos| safe }});

  // Check for empty data
  if (!{{ labels | safe }} || {{ labels | safe }}.length === 0) console.warn('WARNING: Labels array is empty');
  if (!{{ ventas_data | safe }} || {{ ventas_data | safe }}.length === 0) console.warn('WARNING: Ventas data array is empty');
  if (!{{ gastos_data | safe }} || {{ gastos_data | safe }}.length === 0) console.warn('WARNING: Gastos data array is empty');

  const ctx = document.getElementById('ventasGastosChart');
  if (!ctx) {
    console.error('ERROR: No se encontró el elemento ventasGastosChart');
    return;
  }

  new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: {
      labels: {{ labels| safe }},
    datasets: [
    {
      label: 'Ventas',
      data: {{ ventas_data| safe }},
    backgroundColor: 'rgba(76, 175, 80, 0.8)',
    borderColor: 'rgba(76, 175, 80, 1)',
    borderWidth: 2,
    borderRadius: 6,
    hoverBackgroundColor: 'rgba(76, 175, 80, 1)'
        },
    {
      label: 'Gastos',
      data: {{ gastos_data| safe }},
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
    borderColor: 'rgba(244, 67, 54, 1)',
    borderWidth: 2,
    borderRadius: 6,
    hoverBackgroundColor: 'rgba(244, 67, 54, 1)'
        }
  ]
    },
    options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 1500,
      easing: 'easeInOutQuart'
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(44, 62, 80, 0.95)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: 'rgba(76, 175, 80, 0.5)',
        borderWidth: 2,
        cornerRadius: 8,
        displayColors: true,
        padding: 10,
        callbacks: {
          label: function (context) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return label + ': $' + value.toLocaleString();
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold'
          },
          color: '#2c3e50'
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(44, 62, 80, 0.1)',
          lineWidth: 1
        },
        ticks: {
          font: {
            size: 12
          },
          color: '#2c3e50',
          callback: function (value) {
            return '$' + value.toLocaleString();
          }
        }
      }
    }
  }
  });

  // Gráfico de distribución de gastos
  const ctxGastos = document.getElementById('distribucionGastosChart');
  if (!ctxGastos) {
    console.error('ERROR: No se encontró el elemento distribucionGastosChart');
    return;
  }

  new Chart(ctxGastos.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: {{ descripciones_gastos| safe }},
    datasets: [{
      data: {{ montos_gastos| safe }},
    backgroundColor: {{ colores_gastos| safe }},
    borderWidth: 3,
    borderColor: '#ffffff',
    hoverBorderWidth: 4,
    hoverBorderColor: '#2c3e50'
      }]
    },
    options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 2000,
      easing: 'easeInOutQuart'
    },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
          font: {
            size: 14,
            weight: 'bold'
          },
          color: '#2c3e50'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(44, 62, 80, 0.95)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: 'rgba(52, 152, 219, 0.5)',
        borderWidth: 2,
        cornerRadius: 8,
        displayColors: true,
        padding: 10
      }
    },
    cutout: '60%'
  }
  });

  // Gráfico de productos más vendidos
  const ctxProductos = document.getElementById('productosMasVendidosChart');
  if (ctxProductos) {
    new Chart(ctxProductos.getContext('2d'), {
      type: 'bar',
      data: {
        labels: {{ nombres_productos|safe }},
        datasets: [{
          label: 'Ventas ($)',
          data: {{ totales_ventas|safe }},
          backgroundColor: 'rgba(255, 193, 7, 0.8)',
          borderColor: 'rgba(255, 193, 7, 1)',
          borderWidth: 1,
          borderRadius: 5
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(44, 62, 80, 0.95)',
            callbacks: {
              label: function (context) {
                return 'Ventas: $' + context.parsed.x.toLocaleString();
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              callback: function (value) {
                return '$' + value.toLocaleString();
              }
            }
          }
        }
      }
    });
  }

  // NUEVOS GRÁFICOS: Rotación y Márgenes

  // 1. Gráfico de Rotación de Inventario (Comparativo)
  const ctxRotacion = document.getElementById('rotacionInventarioChart');
  if (ctxRotacion) {
    new Chart(ctxRotacion.getContext('2d'), {
      type: 'bar',
      data: {
        labels: {{ nombres_categorias|safe }},
        datasets: [{
          label: 'Rotación (x veces)',
          data: {{ rotacion_categoria|safe }},
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Veces al año'
            }
          }
        }
      }
    });
  }

  // 2. Gráfico de Márgenes por Categoría
  const ctxMargenes = document.getElementById('margenesCategoriaChart');
  if (ctxMargenes) {
    new Chart(ctxMargenes.getContext('2d'), {
      type: 'bar', // Changed from radar to bar for better visibility
      data: {
        labels: {{ nombres_categorias| safe }},
        datasets: [{
          label: 'Margen Bruto (%)',
          data: {{ margenes_categoria| safe }},
          backgroundColor: {{ colores_categorias| safe }}, // Use category colors
          borderColor: 'rgba(40, 167, 69, 1)',
          borderWidth: 1,
          borderRadius: 5
        }]
      },
      options: {
        indexAxis: 'y', // Horizontal bar recommended for long category names
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
           tooltip: {
            backgroundColor: 'rgba(44, 62, 80, 0.95)',
            callbacks: {
              label: function (context) {
                return 'Margen: ' + context.parsed.x + '%';
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Porcentaje (%)'
            }
          }
        }
      }
    });
  }

  // 3. Gráfico de Rentabilidad Temporal (Line Chart)
  const ctxRentabilidad = document.getElementById('rentabilidadTemporalChart');
  if (ctxRentabilidad) {
    new Chart(ctxRentabilidad.getContext('2d'), {
      type: 'line',
      data: {
        labels: {{ labels| safe }},
    datasets: [
    {
      label: 'Margen Bruto (%)',
      data: {{ margenes_brutos_mensuales| safe }},
    backgroundColor: 'rgba(40, 167, 69, 0.1)',
    borderColor: '#28a745',
    borderWidth: 3,
    tension: 0.4,
    fill: true
        },
    {
      label: 'Margen Neto (%)',
      data: {{ margenes_netos_mensuales| safe }},
    backgroundColor: 'rgba(23, 162, 184, 0.1)',
    borderColor: '#17a2b8',
    borderWidth: 3,
    tension: 0.4,
    fill: true
        }
  ]
    },
    options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        backgroundColor: 'rgba(44, 62, 80, 0.95)',
        callbacks: {
          label: function (context) {
            return context.dataset.label + ': ' + context.parsed.y + '%';
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Porcentaje (%)'
        }
      }
    }
  }
    });
  }

  // 4. Gráfico de Comparación con el Sector
  const ctxSector = document.getElementById('comparacionSectorChart');
  if (ctxSector) {
    new Chart(ctxSector.getContext('2d'), {
      type: 'bar',
      data: {
        labels: ['Tu Empresa', 'Promedio Sector', 'Mejor del Sector'],
        datasets: [{
          label: 'Margen (%)',
          data: [{{ margen_neto|unlocalize }}, {{ promedio_sector|unlocalize }}, {{ mejor_sector|unlocalize }}],
          backgroundColor: [
            {{ margen_neto|unlocalize }} > {{ mejor_sector|unlocalize }} ? 'rgba(40, 167, 69, 0.8)' :
            {{ margen_neto|unlocalize }} > {{ promedio_sector|unlocalize }} ? 'rgba(255, 193, 7, 0.8)' :
            'rgba(220, 53, 69, 0.8)',
            'rgba(108, 117, 125, 0.6)',
            'rgba(40, 167, 69, 0.6)'
          ],
          borderColor: [
            {{ margen_neto|unlocalize }} > {{ mejor_sector|unlocalize }} ? '#28a745' :
            {{ margen_neto|unlocalize }} > {{ promedio_sector|unlocalize }} ? '#ffc107' :
            '#dc3545',
            '#6c757d',
            '#28a745'
          ],
          borderWidth: 2,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(44, 62, 80, 0.95)',
            callbacks: {
              label: function(context) {
                const value = context.parsed.y;
                let status = '';
                if (context.dataIndex === 0) {
                  status = value > {{ mejor_sector|unlocalize }} ? ' - EXCELENTE' :
                          value > {{ promedio_sector|unlocalize }} ? ' - BUENO' : ' - NECESITA MEJORAR';
                }
                return 'Margen: ' + value + '%' + status;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: Math.max({{ margen_neto|unlocalize }}, {{ mejor_sector|unlocalize }}) + 5,
            ticks: {
              callback: function(value) {
                return value + '%';
              }
            },
            title: {
              display: true,
              text: 'Margen de Utilidad (%)'
            }
          }
        }
      }
    });
  }

  // 5. Gráfico de Rotación vs Benchmark
  const ctxBenchmark = document.getElementById('rotacionBenchmarkChart');
  if (ctxBenchmark) {
    new Chart(ctxBenchmark.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Tu Rotación', 'Benchmark Sector'],
        datasets: [{
          data: [{{ rotacion_promedio|unlocalize }}, {{ rotacion_sector|unlocalize }}],
          backgroundColor: [
            {{ rotacion_promedio|unlocalize }} >= {{ rotacion_sector|unlocalize }} ? 'rgba(40, 167, 69, 0.8)' : 'rgba(255, 193, 7, 0.8)',
            'rgba(108, 117, 125, 0.4)'
          ],
          borderColor: [
            {{ rotacion_promedio|unlocalize }} >= {{ rotacion_sector|unlocalize }} ? '#28a745' : '#ffc107',
            '#6c757d'
          ],
          borderWidth: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              font: { size: 12, weight: 'bold' }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(44, 62, 80, 0.95)',
            callbacks: {
              label: function(context) {
                const value = context.parsed;
                let status = '';
                if (context.dataIndex === 0) {
                  status = value >= {{ rotacion_sector|unlocalize }} ? ' - EXCELENTE' :
                          value >= {{ rotacion_sector|unlocalize }} * 0.7 ? ' - BUENA' : ' - BAJA';
                }
                return context.label + ': ' + value + 'x' + status;
              }
            }
          }
        },
        cutout: '60%'
      }
    });
  }

  // 6. Gráfico de Histórico de Utilidades
  const ctxUtilidades = document.getElementById('historicoUtilidadesChart');
  if(ctxUtilidades) {
    new Chart(ctxUtilidades.getContext('2d'), {
      type: 'line',
      data: {
        labels: {{ labels| safe }},
    datasets: [{
      label: 'Utilidad Neta ($)',
      data: {{ utilidades_mensuales| safe }},
    backgroundColor: 'rgba(13, 110, 253, 0.1)',
    borderColor: '#0d6efd',
    borderWidth: 3,
    pointBackgroundColor: '#fff',
    pointBorderColor: '#0d6efd',
    pointBorderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 6,
    fill: true,
    tension: 0.3
        }]
      },
    options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(44, 62, 80, 0.95)',
        callbacks: {
          label: function (context) {
            return 'Utilidad: $' + context.parsed.y.toLocaleString();
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { borderDash: [2, 4] },
        ticks: {
          callback: function (value) {
            return '$' + value.toLocaleString();
          }
        }
      }
    }
  }
    });
  }

});
</script>
{% endblock %}"""

file_path = os.path.join(r"c:\Proyectos\contafy\empresa\templates\empresa\dashboard.html")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully overwrote {file_path}")
