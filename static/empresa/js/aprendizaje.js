/**
 * Academia CONTAFY - JavaScript tipo Duolingo
 */

class AcademiaApp {
    constructor() {
        this.currentStep = 0;
        this.simulacionActiva = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupToasts();
        this.checkConnection();
    }

    setupEventListeners() {
        document.querySelectorAll('.paso-header').forEach((header, index) => {
            header.addEventListener('click', () => this.toggleStep(index));
        });

        document.querySelectorAll('[data-action="start-simulation"]').forEach(btn => {
            btn.addEventListener('click', (e) => this.startSimulation(e));
        });
    }

    toggleStep(stepIndex) {
        const stepItem = document.querySelector(`[data-step="${stepIndex}"]`);
        const content = stepItem.querySelector('.paso-contenido');
        const numero = stepItem.querySelector('.paso-numero');
        
        document.querySelectorAll('.paso-contenido').forEach(c => {
            if (c !== content) c.classList.remove('activo');
        });
        
        content.classList.toggle('activo');
        
        if (content.classList.contains('activo')) {
            this.currentStep = stepIndex;
            numero.classList.add('activo');
        } else {
            numero.classList.remove('activo');
        }
    }

    async startSimulation(event) {
        const btn = event.target;
        const tipoSimulacion = btn.dataset.tipoSimulacion;
        const leccionId = btn.dataset.leccionId;
        
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Iniciando...';
        
        try {
            const response = await fetch('/api/academia/simulacion/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    tipo_simulacion_id: parseInt(tipoSimulacion),
                    leccion_id: leccionId ? parseInt(leccionId) : null,
                    modo_sandbox: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.simulacionActiva = data;
                this.showSimulationModal(data);
            } else {
                this.showError('Error al iniciar simulación');
            }
        } catch (error) {
            this.showError('Error de conexión');
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Iniciar Simulación';
        }
    }

    showSimulationModal(simulacion) {
        const modalHtml = `
            <div class="modal fade modal-simulacion" id="simulacionModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-flask"></i>
                                ${simulacion.tipo_simulacion.nombre}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="sandbox-badge">
                                <i class="fas fa-shield-alt"></i>
                                Práctica (Sandbox)
                            </div>
                            ${this.generateSimulationForm(simulacion)}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Cancelar
                            </button>
                            <button type="button" class="btn-duolingo btn-primary" onclick="academia.finalizarSimulacion()">
                                Finalizar Simulación
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('simulacionModal'));
        modal.show();
        
        document.getElementById('simulacionModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('simulacionModal').remove();
        });
    }

    generateSimulationForm(simulacion) {
        return `
            <form class="simulacion-form" data-simulacion-id="${simulacion.id}">
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group-simulacion">
                            <label>Producto</label>
                            <input type="text" name="producto" class="form-control-simulacion" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group-simulacion">
                            <label>Cliente</label>
                            <input type="text" name="cliente" class="form-control-simulacion">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-4">
                        <div class="form-group-simulacion">
                            <label>Cantidad</label>
                            <input type="number" name="cantidad" class="form-control-simulacion" min="1" required>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-group-simulacion">
                            <label>Precio Unitario</label>
                            <input type="number" name="precio_unitario" class="form-control-simulacion" step="0.01" min="0" required>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-group-simulacion">
                            <label>Subtotal</label>
                            <input type="number" name="subtotal" class="form-control-simulacion" step="0.01" readonly>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group-simulacion">
                            <label>IVA (12%)</label>
                            <input type="number" name="iva" class="form-control-simulacion" step="0.01" readonly>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group-simulacion">
                            <label>Total</label>
                            <input type="number" name="total" class="form-control-simulacion" step="0.01" readonly>
                        </div>
                    </div>
                </div>
            </form>
        `;
    }

    async finalizarSimulacion() {
        if (!this.simulacionActiva) return;
        
        const form = document.querySelector('.simulacion-form');
        const formData = new FormData(form);
        const datos = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch(`/api/academia/simulacion/${this.simulacionActiva.id}/finalizar/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ datos_usuario: datos })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleSimulationResult(result);
            } else {
                this.showError('Error al procesar simulación');
            }
        } catch (error) {
            this.showError('Error de conexión');
        }
    }

    handleSimulationResult(result) {
        const { resultado } = result;
        
        bootstrap.Modal.getInstance(document.getElementById('simulacionModal')).hide();
        
        if (resultado.exito) {
            this.showSuccess(`¡Excelente! Puntuación: ${resultado.puntuacion}`);
            
            if (resultado.xp_otorgada) {
                this.showXPGain(resultado.xp_otorgada);
            }
            
            this.markStepCompleted(this.currentStep);
        } else {
            this.showError(`Simulación fallida. ${resultado.feedback?.join(', ') || ''}`);
        }
    }

    showXPGain(xp) {
        const toastHtml = `
            <div class="toast toast-xp" role="alert">
                <div class="toast-header">
                    <i class="fas fa-star text-warning"></i>
                    <strong class="me-auto">¡XP Ganado!</strong>
                </div>
                <div class="toast-body">
                    <span class="xp-animation">+${xp} XP</span>
                </div>
            </div>
        `;
        
        this.showToast(toastHtml, 3000);
    }

    showToast(html, duration = 5000) {
        const container = document.querySelector('.toast-container') || this.createToastContainer();
        container.insertAdjacentHTML('beforeend', html);
        
        const toast = container.lastElementChild;
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }

    markStepCompleted(stepIndex) {
        const stepItem = document.querySelector(`[data-step="${stepIndex}"]`);
        const numero = stepItem.querySelector('.paso-numero');
        
        stepItem.classList.add('completado');
        numero.classList.remove('activo', 'pendiente');
        numero.classList.add('completado');
    }

    setupToasts() {
        if (!document.querySelector('.toast-container')) {
            this.createToastContainer();
        }
    }

    checkConnection() {
        const updateStatus = (online) => {
            let status = document.querySelector('.connection-status');
            if (!status) {
                status = document.createElement('div');
                status.className = 'connection-status';
                document.body.appendChild(status);
            }
            
            status.className = `connection-status ${online ? 'online' : 'offline'}`;
            status.textContent = online ? 'Conectado' : 'Sin conexión';
        };
        
        window.addEventListener('online', () => updateStatus(true));
        window.addEventListener('offline', () => updateStatus(false));
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showSuccess(message) {
        this.showToast(`
            <div class="toast" role="alert">
                <div class="toast-header bg-success text-white">
                    <i class="fas fa-check-circle"></i>
                    <strong class="me-auto">¡Éxito!</strong>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `);
    }

    showError(message) {
        this.showToast(`
            <div class="toast" role="alert">
                <div class="toast-header bg-danger text-white">
                    <i class="fas fa-exclamation-circle"></i>
                    <strong class="me-auto">Error</strong>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `);
    }
}

let academia;
document.addEventListener('DOMContentLoaded', () => {
    academia = new AcademiaApp();
});

document.addEventListener('input', (e) => {
    if (e.target.matches('[name="cantidad"], [name="precio_unitario"]')) {
        const form = e.target.closest('form');
        const cantidad = parseFloat(form.querySelector('[name="cantidad"]').value) || 0;
        const precio = parseFloat(form.querySelector('[name="precio_unitario"]').value) || 0;
        
        const subtotal = cantidad * precio;
        const iva = subtotal * 0.12;
        const total = subtotal + iva;
        
        form.querySelector('[name="subtotal"]').value = subtotal.toFixed(2);
        form.querySelector('[name="iva"]').value = iva.toFixed(2);
        form.querySelector('[name="total"]').value = total.toFixed(2);
    }
});