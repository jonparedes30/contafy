/**
 * Contafy Charts — Configuración estándar para Chart.js
 *
 * Uso:
 *   <script src="{% static 'js/contafy_charts.js' %}"></script>
 *
 *   const chart = new Chart(ctx, {
 *     type: 'bar',
 *     data: { labels: [...], datasets: [{ data: [...], backgroundColor: CONTAFY_CHART_COLORS.income }] },
 *     options: { ...CONTAFY_CHART_DEFAULTS, /* overrides aquí *\/ },
 *   });
 *
 * Ver docs/DESIGN_SYSTEM.md sección 8 para reglas y ejemplos.
 */

window.CONTAFY_CHART_COLORS = {
    // Serie principal de 8 colores (para datasets múltiples)
    palette: [
        '#10b981',  // 1. Verde brand
        '#3b82f6',  // 2. Azul brand
        '#f59e0b',  // 3. Ámbar
        '#ef4444',  // 4. Rojo
        '#8b5cf6',  // 5. Púrpura
        '#14b8a6',  // 6. Teal
        '#f97316',  // 7. Naranja
        '#06b6d4',  // 8. Cyan
    ],
    // Semánticos FIJOS (no intercambiables)
    income:  '#10b981',  // ingresos siempre verde
    expense: '#ef4444',  // gastos siempre rojo
    profit:  '#3b82f6',  // utilidad siempre azul
    warning: '#f59e0b',  // alertas siempre ámbar

    // Transparencias para fills
    fillAlpha:   0.15,
    borderAlpha: 1,

    // Ejes y grid
    grid:      '#e2e8f0',
    axisText:  '#64748b',
    tooltipBg: 'rgba(15, 23, 42, 0.95)',
    tooltipBorder: 'rgba(16, 185, 129, 0.5)',

    /**
     * Devuelve una versión con alpha del color dado.
     * @example getAlpha('#10b981', 0.15) → 'rgba(16, 185, 129, 0.15)'
     */
    getAlpha(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },
};

window.CONTAFY_CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    plugins: {
        legend: {
            position: 'top',
            labels: {
                font: { family: 'Inter', size: 12, weight: '500' },
                color: '#64748b',
                padding: 16,
                usePointStyle: true,
                pointStyle: 'circle',
                boxWidth: 8,
            },
        },
        tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            titleColor: '#fff',
            bodyColor: 'rgba(255,255,255,.85)',
            borderColor: 'rgba(16,185,129,.5)',
            borderWidth: 1,
            titleFont: { family: 'Inter', size: 13, weight: '700' },
            bodyFont:  { family: 'Inter', size: 12 },
            padding: 12,
            cornerRadius: 8,
            displayColors: true,
            boxPadding: 4,
        },
    },
    scales: {
        x: {
            grid: { display: false, drawBorder: false },
            ticks: { font: { family: 'Inter', size: 11 }, color: '#64748b' },
        },
        y: {
            grid: { color: '#e2e8f0', drawBorder: false },
            ticks: { font: { family: 'Inter', size: 11 }, color: '#64748b' },
            beginAtZero: true,
        },
    },
};

/**
 * Configura Chart.js global con el Design System Contafy.
 * Se ejecuta automáticamente cuando Chart.js esté disponible.
 *
 * Sobreescribe TODOS los defaults de Chart.js para que cada gráfico,
 * sin necesidad de configuración explícita, herede:
 *   - Fuente Inter
 *   - Colores brand verde/rojo/azul/ámbar
 *   - Leyendas con puntos circulares
 *   - Tooltips navy con borde verde brand
 *   - Grid Y limpio (sin grid X)
 *   - Animaciones suaves
 */
function _applyContafyDefaults() {
    if (typeof Chart === 'undefined') return false;

    // --- Tipografía global ---
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#64748b';

    // --- Colores brand por defecto para datasets ---
    Chart.defaults.backgroundColor = 'rgba(16, 185, 129, 0.8)';
    Chart.defaults.borderColor = '#10b981';
    Chart.defaults.elements.bar.backgroundColor = 'rgba(16, 185, 129, 0.8)';
    Chart.defaults.elements.bar.borderColor = '#10b981';
    Chart.defaults.elements.bar.borderRadius = 4;

    // --- Líneas con tensión suave y puntos visibles ---
    if (Chart.defaults.elements.line) {
        Chart.defaults.elements.line.tension = 0.35;
        Chart.defaults.elements.line.borderWidth = 2.5;
        Chart.defaults.elements.line.borderColor = '#10b981';
    }
    if (Chart.defaults.elements.point) {
        Chart.defaults.elements.point.radius = 4;
        Chart.defaults.elements.point.hoverRadius = 7;
        Chart.defaults.elements.point.borderWidth = 2;
        Chart.defaults.elements.point.backgroundColor = '#fff';
        Chart.defaults.elements.point.borderColor = '#10b981';
    }

    // --- Doughnut/Pie sin borde ancho ---
    if (Chart.defaults.elements.arc) {
        Chart.defaults.elements.arc.borderWidth = 2;
        Chart.defaults.elements.arc.borderColor = '#fff';
    }

    // --- Leyendas con puntos circulares ---
    if (Chart.defaults.plugins && Chart.defaults.plugins.legend) {
        Chart.defaults.plugins.legend.position = 'top';
        Chart.defaults.plugins.legend.labels = {
            ...Chart.defaults.plugins.legend.labels,
            font: { family: 'Inter', size: 12, weight: '500' },
            color: '#64748b',
            padding: 16,
            usePointStyle: true,
            pointStyle: 'circle',
            boxWidth: 8,
        };
    }

    // --- Tooltips navy brand ---
    if (Chart.defaults.plugins && Chart.defaults.plugins.tooltip) {
        Object.assign(Chart.defaults.plugins.tooltip, {
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            titleColor: '#fff',
            bodyColor: 'rgba(255,255,255,.9)',
            borderColor: 'rgba(16,185,129,.5)',
            borderWidth: 1,
            titleFont: { family: 'Inter', size: 13, weight: '700' },
            bodyFont:  { family: 'Inter', size: 12 },
            padding: 12,
            cornerRadius: 8,
            displayColors: true,
            boxPadding: 4,
        });
    }

    // --- Escalas: grid limpio ---
    if (Chart.defaults.scales) {
        // Linear (y por defecto)
        if (Chart.defaults.scales.linear) {
            Chart.defaults.scales.linear.grid = {
                color: '#e2e8f0',
                drawBorder: false,
                drawTicks: false,
            };
            Chart.defaults.scales.linear.ticks = {
                font: { family: 'Inter', size: 11 },
                color: '#64748b',
                padding: 8,
            };
            Chart.defaults.scales.linear.beginAtZero = true;
        }
        // Category (x por defecto)
        if (Chart.defaults.scales.category) {
            Chart.defaults.scales.category.grid = {
                display: false,
                drawBorder: false,
            };
            Chart.defaults.scales.category.ticks = {
                font: { family: 'Inter', size: 11 },
                color: '#64748b',
                padding: 8,
            };
        }
    }

    // --- Locale español para fechas ---
    try {
        if (Chart.defaults.locale !== undefined) {
            Chart.defaults.locale = 'es-EC';
        }
    } catch (e) {}

    // --- Animación suave ---
    Chart.defaults.animation = {
        duration: 800,
        easing: 'easeOutQuart',
    };

    console.log('[contafy_charts] Defaults aplicados ✓');
    return true;
}

// Aplica al cargar si Chart.js ya existe
if (typeof Chart !== 'undefined') {
    _applyContafyDefaults();
}

// También intenta aplicar después de DOMContentLoaded (por si Chart.js se carga después)
document.addEventListener('DOMContentLoaded', function () {
    if (!_applyContafyDefaults()) {
        // Reintentar cada 100ms hasta máximo 2s
        let intentos = 0;
        const intervalo = setInterval(function () {
            intentos++;
            if (_applyContafyDefaults() || intentos > 20) {
                clearInterval(intervalo);
            }
        }, 100);
    }
});

window.contafyChartsInit = _applyContafyDefaults;  // mantener compatibilidad
