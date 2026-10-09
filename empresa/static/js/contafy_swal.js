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
        confirmButtonColor: '#0f2a47',  // azul marino (marca)
        cancelButtonColor:  '#5d6978',  // gris (cancelar)
        denyButtonColor:    '#a3333d',  // rojo sobrio
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
                    confirmButtonColor: '#0f2a47',
                    cancelButtonColor: '#5d6978',
                    denyButtonColor: '#a3333d',
                }, args[0]);
            }
            return _origFire.apply(this, args);
        };
    }
}

window.ContafySwal = (function () {
    const COLORS = {
        green:  '#1b7466',
        red:    '#a3333d',
        amber:  '#9a6a12',
        blue:   '#1b5f8c',
        slate:  '#5d6978',
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

// === Avisos del sistema en lugar de alert() nativo ===
// Las pantallas llaman alert() en muchos lugares; aquí se muestra con el
// diseño de Contafy. Como alert() nativo bloquea y SweetAlert no, el mensaje
// se guarda un momento en sessionStorage: si la pantalla recarga o redirige
// justo después (alert + location.reload), el aviso aparece en la siguiente.
(function () {
    if (typeof Swal === 'undefined') return;
    const CLAVE = 'cf_aviso_pendiente';
    const VIGENCIA_MS = 15000;

    function tipo(msg) {
        const m = msg.toLowerCase();
        if (/^error|error al|no se pudo|no se registr|falló|fallo|denegad/.test(m)) return 'error';
        if (/exitosa|registrad|cread|guardad|enviad|actualizad|eliminad|copiad|complet/.test(m)) return 'success';
        if (/por favor|requerid|selecciona|seleccione|agrega|agregue|insuficiente|ingresa|ingrese|debe|inválid|invalid/.test(m)) return 'warning';
        return 'info';
    }

    function guardar(v) { try { sessionStorage.setItem(CLAVE, v); } catch (e) { /* sin almacenamiento */ } }
    function limpiar()  { try { sessionStorage.removeItem(CLAVE); } catch (e) { /* sin almacenamiento */ } }

    function mostrar(msg) {
        const icono = tipo(msg);
        return Swal.fire({
            icon: icono,
            text: msg,
            confirmButtonText: 'Aceptar',
            buttonsStyling: false,
            customClass: {
                popup: 'contafy-swal',
                confirmButton: icono === 'error' ? 'btn btn-danger' : 'btn btn-primary',
            },
        }).then(limpiar);
    }

    window.alert = function (msg) {
        msg = String(msg === undefined || msg === null ? '' : msg);
        guardar(JSON.stringify({ m: msg, t: Date.now() }));
        mostrar(msg);
    };

    // Aviso que quedó pendiente porque la pantalla anterior recargó o redirigió
    let pendiente = null;
    try { pendiente = JSON.parse(sessionStorage.getItem(CLAVE) || 'null'); } catch (e) { pendiente = null; }
    limpiar();
    if (pendiente && pendiente.m && Date.now() - pendiente.t < VIGENCIA_MS) {
        mostrar(pendiente.m);
    }
})();
