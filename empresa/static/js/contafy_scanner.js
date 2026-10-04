/**
 * Contafy Scanner — escáner único para Ventas (POS), Compras e Inventario.
 *
 * 1. Lee el código de barras EN VIVO con la cámara (BarcodeDetector nativo o
 *    ZXing como respaldo): gratis, sin internet para leer, sin Google.
 * 2. Si el producto no tiene código, "Identificar por foto" envía una foto a la IA.
 * 3. También permite escribir el código a mano.
 *
 * Uso:
 *   ContafyScanner.abrir({
 *     contexto: 'venta' | 'compra' | 'inventario',
 *     endpoint: "{% url 'empresa:vision_search_api' %}",
 *     onResultado: (data) => { ... },  // misma respuesta que vision_search_api
 *     seguirSiNoEncontrado: true,      // opcional: no cerrar si el producto no existe (POS)
 *   });
 */
(function () {
    'use strict';

    const ZXING_URL = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.23.0/umd/index.min.js';
    const FORMATOS_NATIVOS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128'];

    let modal, bsModal, video, estado, opciones = {};
    let stream = null, detector = null, lectorZxing = null, bucle = null, buscando = false;

    function csrf() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function construirModal() {
        if (modal) return;
        const html = `
<div class="modal fade" id="contafyScannerModal" tabindex="-1" aria-labelledby="contafyScannerTitulo" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered modal-fullscreen-sm-down">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="contafyScannerTitulo"><i class="bi bi-upc-scan me-2"></i>Escanear producto</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body p-0">
        <div class="cfs-visor">
          <video class="cfs-video" playsinline muted autoplay></video>
          <div class="cfs-guia" aria-hidden="true"></div>
        </div>
        <div class="cfs-estado px-3 py-2 small" role="status" aria-live="polite">Activando cámara…</div>
        <form class="cfs-manual px-3 pb-3 d-flex gap-2">
          <input type="text" inputmode="numeric" class="form-control" placeholder="O escribe el código" aria-label="Código del producto" autocomplete="off">
          <button type="submit" class="btn btn-outline-secondary">Buscar</button>
        </form>
      </div>
      <div class="modal-footer justify-content-between">
        <button type="button" class="btn btn-outline-primary cfs-foto"><i class="bi bi-camera me-1"></i>Identificar por foto (IA)</button>
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      </div>
    </div>
  </div>
</div>
<style>
  #contafyScannerModal .cfs-visor { position: relative; background: #000; aspect-ratio: 4 / 3; overflow: hidden; }
  #contafyScannerModal .cfs-video { width: 100%; height: 100%; object-fit: cover; display: block; }
  #contafyScannerModal .cfs-guia { position: absolute; left: 12%; right: 12%; top: 35%; bottom: 35%;
      border: 3px solid rgba(16, 185, 129, .9); border-radius: 10px; box-shadow: 0 0 0 999px rgba(0, 0, 0, .35); }
  #contafyScannerModal .cfs-estado { min-height: 2.5rem; }
  #contafyScannerModal .cfs-estado.error { color: #b91c1c; }
  #contafyScannerModal .cfs-estado.ok { color: #047857; }
</style>`;
        document.body.insertAdjacentHTML('beforeend', html);
        modal = document.getElementById('contafyScannerModal');
        video = modal.querySelector('.cfs-video');
        estado = modal.querySelector('.cfs-estado');
        bsModal = new bootstrap.Modal(modal);

        modal.addEventListener('shown.bs.modal', iniciarCamara);
        modal.addEventListener('hidden.bs.modal', detener);
        modal.querySelector('.cfs-foto').addEventListener('click', identificarPorFoto);
        modal.querySelector('.cfs-manual').addEventListener('submit', (e) => {
            e.preventDefault();
            const input = e.target.querySelector('input');
            if (input.value.trim()) buscar({ codigo: input.value.trim() });
        });
    }

    function mostrar(texto, tipo) {
        estado.textContent = texto;
        estado.className = 'cfs-estado px-3 py-2 small' + (tipo ? ' ' + tipo : '');
    }

    function mensajeErrorCamara(err) {
        if (!window.isSecureContext) {
            return 'La cámara solo funciona en páginas seguras (https). Escribe el código o usa un lector USB.';
        }
        switch (err && err.name) {
            case 'NotAllowedError': return 'No diste permiso para usar la cámara. Actívalo en la configuración del navegador o escribe el código.';
            case 'NotFoundError': return 'No se encontró una cámara en este dispositivo. Escribe el código o usa un lector USB.';
            case 'NotReadableError': return 'Otra aplicación está usando la cámara. Ciérrala e inténtalo de nuevo.';
            default: return 'No se pudo abrir la cámara. Escribe el código o usa un lector USB.';
        }
    }

    function cargarZxing() {
        if (window.ZXing) return Promise.resolve(window.ZXing);
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = ZXING_URL;
            s.onload = () => resolve(window.ZXing);
            s.onerror = () => reject(new Error('No se pudo cargar el lector de códigos'));
            document.head.appendChild(s);
        });
    }

    async function iniciarCamara() {
        buscando = false;
        mostrar('Activando cámara…');
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.isSecureContext) {
            mostrar(mensajeErrorCamara(), 'error');
            return;
        }
        try {
            const pedirCamara = navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false,
            });
            const limite = new Promise((_, reject) => setTimeout(() => reject({ name: 'Timeout' }), 12000));
            stream = await Promise.race([pedirCamara, limite]);
            video.srcObject = stream;
            await video.play();
        } catch (err) {
            mostrar(mensajeErrorCamara(err), 'error');
            return;
        }
        mostrar('Apunta al código de barras dentro del recuadro.');
        iniciarLectura();
    }

    async function iniciarLectura() {
        try {
            if ('BarcodeDetector' in window) {
                const soportados = await window.BarcodeDetector.getSupportedFormats();
                const formatos = FORMATOS_NATIVOS.filter(f => soportados.includes(f));
                if (formatos.length) {
                    detector = new window.BarcodeDetector({ formats: formatos });
                    leerConDetectorNativo();
                    return;
                }
            }
            const ZXing = await cargarZxing();
            const hints = new Map();
            hints.set(ZXing.DecodeHintType.POSSIBLE_FORMATS, [
                ZXing.BarcodeFormat.EAN_13, ZXing.BarcodeFormat.EAN_8, ZXing.BarcodeFormat.UPC_A,
                ZXing.BarcodeFormat.UPC_E, ZXing.BarcodeFormat.CODE_128,
            ]);
            lectorZxing = new ZXing.BrowserMultiFormatReader(hints, 300);
            lectorZxing.decodeFromStream(stream, video, (resultado) => {
                if (resultado) codigoLeido(resultado.getText());
            });
        } catch (err) {
            console.warn('Lector de códigos no disponible', err);
            mostrar('Tu navegador no puede leer códigos con la cámara. Usa "Identificar por foto" o escribe el código.', 'error');
        }
    }

    function leerConDetectorNativo() {
        bucle = setInterval(async () => {
            if (buscando || !detector || video.readyState < 2) return;
            try {
                const codigos = await detector.detect(video);
                if (codigos.length) codigoLeido(codigos[0].rawValue);
            } catch (e) { /* cuadro sin código: seguir intentando */ }
        }, 250);
    }

    function codigoLeido(codigo) {
        if (buscando || !codigo) return;
        try { navigator.vibrate && navigator.vibrate(80); } catch (e) {}
        buscar({ codigo: String(codigo).trim() });
    }

    function capturarFoto() {
        if (!video || !video.videoWidth) return null;
        const canvas = document.createElement('canvas');
        const escala = Math.min(1, 1280 / video.videoWidth);
        canvas.width = Math.round(video.videoWidth * escala);
        canvas.height = Math.round(video.videoHeight * escala);
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/jpeg', 0.85);
    }

    function identificarPorFoto() {
        const foto = capturarFoto();
        if (!foto) {
            mostrar('La cámara aún no está lista para tomar la foto.', 'error');
            return;
        }
        buscar({ image: foto });
    }

    async function buscar(payload) {
        if (buscando) return;
        buscando = true;
        mostrar(payload.codigo ? `Buscando el código ${payload.codigo}…` : 'Analizando la foto…');
        try {
            const resp = await fetch(opciones.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                body: JSON.stringify(Object.assign({ contexto: opciones.contexto }, payload)),
            });
            const data = await resp.json().catch(() => ({ success: false }));
            if (!data.success) {
                mostrar(data.error || 'No se pudo identificar el producto.', 'error');
                buscando = false;
                return;
            }
            if (!data.found && opciones.seguirSiNoEncontrado) {
                // P. ej. en el POS: avisar y dejar la cámara abierta para el siguiente producto.
                mostrar(data.mensaje || 'Producto no encontrado.', 'error');
                setTimeout(() => { buscando = false; }, 1500);
                return;
            }
            mostrar(data.found ? 'Producto encontrado.' : (data.mensaje || 'Sin coincidencias.'), data.found ? 'ok' : 'error');
            bsModal.hide();
            if (typeof opciones.onResultado === 'function') opciones.onResultado(data);
        } catch (err) {
            console.error('Escáner:', err);
            mostrar('Sin conexión con el servidor. Inténtalo de nuevo.', 'error');
            buscando = false;
        }
    }

    function detener() {
        clearInterval(bucle);
        bucle = null;
        detector = null;
        try { lectorZxing && lectorZxing.reset(); } catch (e) {}
        lectorZxing = null;
        if (stream) stream.getTracks().forEach(t => t.stop());
        stream = null;
        if (video) video.srcObject = null;
        buscando = false;
    }

    window.ContafyScanner = {
        abrir(opts) {
            opciones = Object.assign({ contexto: 'compra' }, opts || {});
            if (!opciones.endpoint) throw new Error('ContafyScanner: falta endpoint');
            construirModal();
            modal.querySelector('.cfs-manual input').value = '';
            bsModal.show();
        },
    };
})();
