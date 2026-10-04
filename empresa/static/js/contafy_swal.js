/**
 * Contafy Swal — Configuración estándar para SweetAlert2
 *
 * Uso:
 *   <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
 *   <script src="{% static 'js/contafy_swal.js' %}"></script>
 *
 *   // Confirmar eliminación
 *   ContafySwal.confirmDelete('¿Eliminar producto?', 'Esta acción no se puede deshacer')
 *     .then(result => { if (result.isConfirmed) { /* ... *\/ } });
 *
 *   // Toast de éxito
 *   ContafySwal.toast.success('Guardado correctamente');
 *
 * Ver docs/DESIGN_SYSTEM.md sección 11 para reglas.
 */

// === Override global de defaults de SweetAlert2 ===
// Hace que TODOS los Swal.fire() del sistema usen colores brand
// automáticamente, sin necesidad de modificar las llamadas existentes.
if (typeof Swal !== 'undefined') {
    Swal.mixin({
        confirmButtonColor: '#10b981',  // verde brand
        cancelButtonColor:  '#94a3b8',  // slate brand
        denyButtonColor:    '#ef4444',  // rojo brand
        iconColor: undefined,            // mantiene iconos por defecto (verde/rojo/ámbar)
    });
    // Sobreescribir defaults estáticos también
    Object.assign(Swal.mixin().getSwal ? Swal : {}, {});
    if (Swal.update) {
        const _origFire = Swal.fire;
        Swal.fire = function(...args) {
            // Si recibe un objeto config, mergear defaults brand
            if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
                args[0] = Object.assign({
                    confirmButtonColor: '#10b981',
                    cancelButtonColor: '#94a3b8',
                    denyButtonColor: '#ef4444',
                }, args[0]);
            }
            return _origFire.apply(this, args);
        };
    }
}

window.ContafySwal = (function () {
    const COLORS = {
        green:  '#10b981',
        red:    '#ef4444',
        amber:  '#f59e0b',
        blue:   '#3b82f6',
        slate:  '#94a3b8',
    };

    // Configuración base compartida
    const baseConfig = {
        buttonsStyling: false,
        customClass: {
            popup: 'contafy-swal',
            title: 'contafy-swal-title',
            confirmButton: 'btn btn-primary',
            cancelButton:  'btn btn-outline-secondary mx-2',
            denyButton:    'btn btn-outline-danger mx-2',
        },
    };

    return {
        /**
         * Confirmar eliminación (icono warning, botón rojo)
         */
        confirmDelete(title = '¿Eliminar registro?', text = 'Esta acción no se puede deshacer') {
            return Swal.fire({
                ...baseConfig,
                title,
                text,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar',
                customClass: { ...baseConfig.customClass, confirmButton: 'btn btn-danger' },
            });
        },

        /**
         * Confirmar acción genérica (azul/info)
         */
        confirm(title, text = '', confirmText = 'Confirmar', cancelText = 'Cancelar') {
            return Swal.fire({
                ...baseConfig,
                title, text,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: confirmText,
                cancelButtonText: cancelText,
            });
        },

        /**
         * Mostrar éxito (modal)
         */
        success(title, text = '') {
            return Swal.fire({
                ...baseConfig,
                title, text,
                icon: 'success',
                confirmButtonText: 'Entendido',
            });
        },

        /**
         * Mostrar error (modal)
         */
        error(title = 'Error', text = '') {
            return Swal.fire({
                ...baseConfig,
                title, text,
                icon: 'error',
                confirmButtonText: 'Cerrar',
                customClass: { ...baseConfig.customClass, confirmButton: 'btn btn-danger' },
            });
        },

        /**
         * Advertencia (modal con ámbar)
         */
        warning(title, text = '') {
            return Swal.fire({
                ...baseConfig,
                title, text,
                icon: 'warning',
                confirmButtonText: 'Entendido',
                customClass: { ...baseConfig.customClass, confirmButton: 'btn btn-warning' },
            });
        },

        /**
         * Información (modal con azul)
         */
        info(title, text = '') {
            return Swal.fire({
                ...baseConfig,
                title, text,
                icon: 'info',
                confirmButtonText: 'Entendido',
            });
        },

        /**
         * Toasts — notificaciones no bloqueantes en top-end
         */
        toast: {
            _mixin: null,
            _ensure() {
                if (!this._mixin) {
                    this._mixin = Swal.mixin({
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 3500,
                        timerProgressBar: true,
                        didOpen: (toast) => {
                            toast.addEventListener('mouseenter', Swal.stopTimer);
                            toast.addEventListener('mouseleave', Swal.resumeTimer);
                        },
                    });
                }
                return this._mixin;
            },
            success(title) { return this._ensure().fire({ icon: 'success', title }); },
            error(title)   { return this._ensure().fire({ icon: 'error',   title }); },
            warning(title) { return this._ensure().fire({ icon: 'warning', title }); },
            info(title)    { return this._ensure().fire({ icon: 'info',    title }); },
        },

        // Acceso a colores por si se necesita
        colors: COLORS,
    };
})();
