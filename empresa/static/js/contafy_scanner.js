/**
 * Contafy Scanner — escáner único para Ventas (POS), Compras, Productos e Inventario.
 *
 * 1. Lee el código de barras EN VIVO con la cámara: BarcodeDetector nativo (Android,
 *    macOS) o ZXing como respaldo (Windows, iPhone). Gratis y sin Google.
 * 2. "Identificar por foto" envía una foto a la IA (solo si hay clave configurada).
 * 3. También permite escribir el código a mano.
 *
 * Uso:
 *   ContafyScanner.abrir({
 *     contexto: 'venta' | 'compra' | 'inventario',
 *     endpoint: window.CONTAFY_SCANNER_ENDPOINT,
 *     onResultado: (data, ui) => { ... },   // producto encontrado (misma respuesta que vision_search_api)
 *     continuo: true,                       // opcional (POS): la cámara sigue abierta tras cada producto;
 *                                           //   si onResultado devuelve un texto, se muestra como estado
 *     acciones: (data, ui) => [ {texto, icono, clase, alHacerClic} ],  // botones si no hay resultado
 *     onNoEncontrado: (data, ui) => { ... },  // opcional: el código nuevo es lo esperado (registrar producto)
 *   });
 *   ui = { cerrar() -> Promise, mostrar(texto, tipo), codigo }
 *
 *   ContafyRegistroRapido.abrir({ codigo }) -> Promise<producto | null>
 *     Abre el formulario completo de producto en una ventana sobre la pantalla actual
 *     (no se pierde el carrito ni la compra en curso) y devuelve el producto guardado.
 */
(function () {
    'use strict';

    const ZXING_URL = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.23.0/umd/index.min.js';
    const FORMATOS_NATIVOS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf'];
    const PAUSA_MISMO_CODIGO_MS = 2500;      // no repetir la misma lectura enseguida
    const PAUSA_NO_ENCONTRADO_MS = 8000;     // un código desconocido no se vuelve a consultar en 8 s
    const CLAVE_CAMARA = 'cf_scanner_camara';

    let modal, bsModal, video, estado, accionesEl, opciones = {};
    let stream = null, pista = null, detector = null, lectorZxing = null, bucle = null;
    let buscando = false, ultimo = { codigo: '', hasta: 0 }, camaras = [], linternaEncendida = false;
    let audio = null, alCerrar = [];

    // ---------------------------------------------------------------- utilidades
    function csrf() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function escapar(texto) {
        const div = document.createElement('div');
        div.textContent = texto == null ? '' : String(texto);
        return div.innerHTML;
    }

    function gtinValido(codigo) {
        if (!/^\d+$/.test(codigo) || ![8, 12, 13, 14].includes(codigo.length)) return true; // no es GTIN: no se valida
        const d = codigo.split('').map(Number);
        const verificador = d.pop();
        const suma = d.reverse().reduce((acc, n, i) => acc + n * (i % 2 === 0 ? 3 : 1), 0);
        return (10 - (suma % 10)) % 10 === verificador;
    }

    function pitido(tipo) {
        try {
            if (!audio) return;
            const osc = audio.createOscillator();
            const gan = audio.createGain();
            osc.frequency.value = tipo === 'error' ? 220 : 1200;
            gan.gain.value = 0.08;
            osc.connect(gan).connect(audio.destination);
            osc.start();
            osc.stop(audio.currentTime + (tipo === 'error' ? 0.25 : 0.09));
        } catch (e) { /* sin audio */ }
        try { navigator.vibrate && navigator.vibrate(tipo === 'error' ? [60, 60, 60] : 70); } catch (e) {}
    }

    // ---------------------------------------------------------------- interfaz
    function construirModal() {
        if (modal) return;
        const fotoActiva = !!window.CONTAFY_SCANNER_FOTO;
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
          <div class="cfs-guia" aria-hidden="true"><span class="cfs-linea"></span></div>
          <div class="cfs-controles">
            <button type="button" class="btn btn-sm cfs-btn-camara d-none" title="Cambiar de cámara" aria-label="Cambiar de cámara"><i class="bi bi-arrow-repeat"></i></button>
            <button type="button" class="btn btn-sm cfs-btn-linterna d-none" title="Linterna" aria-label="Encender linterna" aria-pressed="false"><i class="bi bi-lightbulb"></i></button>
          </div>
        </div>
        <div class="cfs-estado px-3 pt-2 small" role="status" aria-live="polite">Activando cámara…</div>
        <div class="cfs-acciones px-3 pt-2 d-none"></div>
        <form class="cfs-manual px-3 py-3 d-flex gap-2">
          <input type="text" inputmode="numeric" class="form-control" placeholder="O escriba el código" aria-label="Código del producto" autocomplete="off">
          <button type="submit" class="btn btn-outline-primary">Buscar</button>
        </form>
      </div>
      <div class="modal-footer ${fotoActiva ? 'justify-content-between' : ''}">
        ${fotoActiva ? '<button type="button" class="btn btn-outline-primary cfs-foto"><i class="bi bi-camera me-1"></i>Identificar por foto (IA)</button>' : ''}
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
      </div>
    </div>
  </div>
</div>
<style>
  #contafyScannerModal .cfs-visor { position: relative; background: #000; aspect-ratio: 4 / 3; overflow: hidden; }
  #contafyScannerModal .cfs-video { width: 100%; height: 100%; object-fit: cover; display: block; }
  #contafyScannerModal .cfs-guia { position: absolute; left: 10%; right: 10%; top: 32%; bottom: 32%;
      border: 3px solid var(--cf-logo-teal, #20a090); border-radius: 10px; box-shadow: 0 0 0 999px rgba(7, 21, 38, .45);
      transition: border-color .15s, background-color .15s; }
  #contafyScannerModal .cfs-linea { position: absolute; left: 6%; right: 6%; top: 50%; height: 2px;
      background: rgba(255, 255, 255, .55); animation: cfs-barrido 1.6s ease-in-out infinite alternate; }
  @keyframes cfs-barrido { from { transform: translateY(-28px); } to { transform: translateY(28px); } }
  #contafyScannerModal .cfs-guia.ok { border-color: #3ddc97; background: rgba(61, 220, 151, .18); }
  #contafyScannerModal .cfs-guia.error { border-color: #f06a74; background: rgba(240, 106, 116, .16); }
  #contafyScannerModal .cfs-controles { position: absolute; top: 10px; right: 10px; display: flex; gap: 8px; }
  #contafyScannerModal .cfs-controles .btn { background: rgba(7, 21, 38, .65); color: #fff; border: 1px solid rgba(255, 255, 255, .35);
      width: 40px; height: 40px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; }
  #contafyScannerModal .cfs-controles .btn[aria-pressed="true"] { background: #f5c542; color: #071526; }
  #contafyScannerModal .cfs-estado { min-height: 2rem; font-weight: 500; }
  #contafyScannerModal .cfs-estado.error { color: var(--cf-neg, #a3333d); }
  #contafyScannerModal .cfs-estado.ok { color: var(--cf-pos, #1f7a4d); }
  #contafyScannerModal .cfs-acciones .btn { margin: 0 .4rem .4rem 0; }
</style>`;
        document.body.insertAdjacentHTML('beforeend', html);
        modal = document.getElementById('contafyScannerModal');
        video = modal.querySelector('.cfs-video');
        estado = modal.querySelector('.cfs-estado');
        accionesEl = modal.querySelector('.cfs-acciones');
        bsModal = new bootstrap.Modal(modal);

        modal.addEventListener('shown.bs.modal', () => iniciarCamara());
        modal.addEventListener('hidden.bs.modal', () => {
            detener();
            const pendientes = alCerrar; alCerrar = [];
            pendientes.forEach(fn => fn());
        });
        modal.querySelector('.cfs-foto')?.addEventListener('click', identificarPorFoto);
        modal.querySelector('.cfs-btn-camara').addEventListener('click', cambiarCamara);
        modal.querySelector('.cfs-btn-linterna').addEventListener('click', alternarLinterna);
        modal.querySelector('.cfs-manual').addEventListener('submit', (e) => {
            e.preventDefault();
            const input = e.target.querySelector('input');
            const codigo = input.value.trim();
            if (codigo) { input.value = ''; buscar({ codigo }, true); }
        });
    }

    function mostrar(texto, tipo) {
        estado.textContent = texto;
        estado.className = 'cfs-estado px-3 pt-2 small' + (tipo ? ' ' + tipo : '');
    }

    function marcarGuia(tipo) {
        const guia = modal.querySelector('.cfs-guia');
        guia.classList.remove('ok', 'error');
        if (tipo) {
            guia.classList.add(tipo);
            setTimeout(() => guia.classList.remove(tipo), 900);
        }
    }

    function limpiarAcciones() {
        accionesEl.innerHTML = '';
        accionesEl.classList.add('d-none');
    }

    function mostrarAcciones(lista, ui) {
        limpiarAcciones();
        (lista || []).forEach((accion) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-sm ' + (accion.clase || 'btn-outline-primary');
            btn.innerHTML = (accion.icono ? `<i class="bi ${accion.icono} me-1"></i>` : '') + escapar(accion.texto);
            btn.addEventListener('click', () => accion.alHacerClic && accion.alHacerClic(ui));
            accionesEl.appendChild(btn);
        });
        if (accionesEl.children.length) accionesEl.classList.remove('d-none');
    }

    function crearUi(codigo) {
        return {
            codigo,
            mostrar,
            cerrar() {
                return new Promise((resolve) => {
                    if (!modal || !modal.classList.contains('show')) { resolve(); return; }
                    alCerrar.push(resolve);
                    bsModal.hide();
                });
            },
        };
    }

    // ---------------------------------------------------------------- cámara
    function mensajeErrorCamara(err) {
        if (!window.isSecureContext) {
            return 'La cámara solo funciona en páginas seguras (https). Escriba el código o use un lector USB.';
        }
        switch (err && err.name) {
            case 'NotAllowedError': return 'No se dio permiso para usar la cámara. Actívelo en la configuración del navegador (ícono del candado) o escriba el código.';
            case 'NotFoundError': return 'No se encontró una cámara en este dispositivo. Escriba el código o use un lector USB.';
            case 'NotReadableError': return 'Otra aplicación está usando la cámara. Ciérrela e inténtelo de nuevo.';
            case 'Timeout': return 'La cámara tardó demasiado en responder. Cierre y vuelva a abrir el escáner.';
            default: return 'No se pudo abrir la cámara. Escriba el código o use un lector USB.';
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

    function camaraGuardada() {
        try { return localStorage.getItem(CLAVE_CAMARA) || ''; } catch (e) { return ''; }
    }

    async function iniciarCamara(deviceId) {
        detenerLectura();
        buscando = false;
        mostrar('Activando cámara…');
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.isSecureContext) {
            mostrar(mensajeErrorCamara(), 'error');
            return;
        }
        const elegida = deviceId || camaraGuardada();
        const video_ = {
            width: { ideal: 1920 }, height: { ideal: 1080 },
            ...(elegida ? { deviceId: { exact: elegida } } : { facingMode: { ideal: 'environment' } }),
        };
        try {
            const limite = new Promise((_, reject) => setTimeout(() => reject({ name: 'Timeout' }), 12000));
            try {
                stream = await Promise.race([navigator.mediaDevices.getUserMedia({ video: video_, audio: false }), limite]);
            } catch (err) {
                // La cámara guardada ya no existe (otro equipo, se desconectó): usar la trasera por defecto.
                if (elegida && (err.name === 'OverconstrainedError' || err.name === 'NotFoundError')) {
                    try { localStorage.removeItem(CLAVE_CAMARA); } catch (e) {}
                    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
                } else {
                    throw err;
                }
            }
            video.srcObject = stream;
            await video.play();
        } catch (err) {
            mostrar(mensajeErrorCamara(err), 'error');
            return;
        }
        pista = stream.getVideoTracks()[0];
        await prepararControles();
        mostrar('Apunte al código de barras dentro del recuadro.');
        iniciarLectura();
    }

    async function prepararControles() {
        // Enfoque continuo (celulares) y linterna, si la cámara los admite.
        const capacidades = (pista && pista.getCapabilities) ? pista.getCapabilities() : {};
        try {
            if ((capacidades.focusMode || []).includes('continuous')) {
                await pista.applyConstraints({ advanced: [{ focusMode: 'continuous' }] });
            }
        } catch (e) { /* no admite enfoque */ }
        linternaEncendida = false;
        const btnLinterna = modal.querySelector('.cfs-btn-linterna');
        btnLinterna.classList.toggle('d-none', !capacidades.torch);
        btnLinterna.setAttribute('aria-pressed', 'false');

        try {
            camaras = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput');
        } catch (e) { camaras = []; }
        modal.querySelector('.cfs-btn-camara').classList.toggle('d-none', camaras.length < 2);
    }

    async function cambiarCamara() {
        if (camaras.length < 2) return;
        const actual = pista && pista.getSettings ? pista.getSettings().deviceId : '';
        const idx = camaras.findIndex(c => c.deviceId === actual);
        const siguiente = camaras[(idx + 1) % camaras.length];
        try { localStorage.setItem(CLAVE_CAMARA, siguiente.deviceId); } catch (e) {}
        detenerCamara();
        await iniciarCamara(siguiente.deviceId);
        const nombre = siguiente.label ? `: ${siguiente.label}` : '';
        mostrar(`Cámara cambiada${nombre}. Apunte al código de barras.`);
    }

    async function alternarLinterna() {
        if (!pista) return;
        try {
            linternaEncendida = !linternaEncendida;
            await pista.applyConstraints({ advanced: [{ torch: linternaEncendida }] });
            modal.querySelector('.cfs-btn-linterna').setAttribute('aria-pressed', String(linternaEncendida));
        } catch (e) {
            linternaEncendida = false;
            mostrar('Esta cámara no permite encender la linterna.', 'error');
        }
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
                ZXing.BarcodeFormat.UPC_E, ZXing.BarcodeFormat.CODE_128, ZXing.BarcodeFormat.CODE_39,
                ZXing.BarcodeFormat.ITF,
            ]);
            // Más intentos por cuadro: necesario con cámaras de laptop (foco fijo, poca luz).
            hints.set(ZXing.DecodeHintType.TRY_HARDER, true);
            lectorZxing = new ZXing.BrowserMultiFormatReader(hints, 150);
            lectorZxing.decodeFromStream(stream, video, (resultado) => {
                if (resultado) codigoLeido(resultado.getText());
            });
        } catch (err) {
            console.warn('Lector de códigos no disponible', err);
            mostrar('Este navegador no puede leer códigos con la cámara. Escriba el código o use un lector USB.', 'error');
        }
    }

    function leerConDetectorNativo() {
        bucle = setInterval(async () => {
            if (buscando || !detector || video.readyState < 2) return;
            try {
                const codigos = await detector.detect(video);
                if (codigos.length) codigoLeido(codigos[0].rawValue);
            } catch (e) { /* cuadro sin código: seguir intentando */ }
        }, 200);
    }

    function codigoLeido(bruto) {
        const codigo = String(bruto || '').trim();
        if (buscando || !codigo) return;
        if (!gtinValido(codigo)) return;                       // lectura parcial o borrosa
        if (codigo === ultimo.codigo && Date.now() < ultimo.hasta) return;
        buscar({ codigo }, false);
    }

    // ---------------------------------------------------------------- búsqueda
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
        buscar({ image: foto }, true);
    }

    async function buscar(payload, manual) {
        if (buscando) return;
        buscando = true;
        limpiarAcciones();
        if (payload.codigo) ultimo = { codigo: payload.codigo, hasta: Date.now() + PAUSA_MISMO_CODIGO_MS };
        mostrar(payload.codigo ? `Buscando el código ${payload.codigo}…` : 'Analizando la foto…');
        try {
            const resp = await fetch(opciones.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                body: JSON.stringify(Object.assign({ contexto: opciones.contexto }, payload)),
            });
            const data = await resp.json().catch(() => ({ success: false }));
            const ui = crearUi(data.codigo_detectado || payload.codigo || '');

            if (!data.success) {
                pitido('error');
                mostrar(data.error || 'No se pudo identificar el producto.', 'error');
                buscando = false;
                return;
            }

            if (!data.found && typeof opciones.onNoEncontrado === 'function' && data.motivo === 'no_existe') {
                pitido('ok');
                marcarGuia('ok');
                mostrar(`Código nuevo: ${ui.codigo}`, 'ok');
                opciones.onNoEncontrado(data, ui);
                setTimeout(() => { buscando = false; }, 700);
                return;
            }

            if (!data.found) {
                pitido('error');
                marcarGuia('error');
                if (payload.codigo) ultimo.hasta = Date.now() + PAUSA_NO_ENCONTRADO_MS;
                mostrar(data.mensaje || 'Producto no encontrado.', 'error');
                if (typeof opciones.acciones === 'function') mostrarAcciones(opciones.acciones(data, ui), ui);
                setTimeout(() => { buscando = false; }, manual ? 0 : 1200);
                return;
            }

            pitido('ok');
            marcarGuia('ok');
            if (opciones.continuo) {
                const texto = typeof opciones.onResultado === 'function' ? opciones.onResultado(data, ui) : '';
                mostrar(typeof texto === 'string' && texto ? texto : 'Producto encontrado.', 'ok');
                setTimeout(() => { buscando = false; }, 700);
                return;
            }
            mostrar('Producto encontrado.', 'ok');
            await ui.cerrar();
            if (typeof opciones.onResultado === 'function') opciones.onResultado(data, ui);
        } catch (err) {
            console.error('Escáner:', err);
            mostrar('Sin conexión con el servidor. Inténtelo de nuevo.', 'error');
            buscando = false;
        }
    }

    // ---------------------------------------------------------------- cierre
    function detenerLectura() {
        clearInterval(bucle);
        bucle = null;
        detector = null;
        try { lectorZxing && lectorZxing.reset(); } catch (e) {}
        lectorZxing = null;
    }

    function detenerCamara() {
        detenerLectura();
        if (stream) stream.getTracks().forEach(t => t.stop());
        stream = null;
        pista = null;
        if (video) video.srcObject = null;
    }

    function detener() {
        detenerCamara();
        buscando = false;
        limpiarAcciones();
    }

    window.ContafyScanner = {
        abrir(opts) {
            opciones = Object.assign({ contexto: 'compra', continuo: false }, opts || {});
            if (!opciones.endpoint) throw new Error('ContafyScanner: falta endpoint');
            // El sonido solo puede activarse tras un toque del usuario (este clic).
            try {
                audio = audio || new (window.AudioContext || window.webkitAudioContext)();
                if (audio.state === 'suspended') audio.resume();
            } catch (e) { audio = null; }
            construirModal();
            ultimo = { codigo: '', hasta: 0 };
            modal.querySelector('.cfs-manual input').value = '';
            limpiarAcciones();
            bsModal.show();
        },
        // Para pruebas: valida el dígito verificador de un código EAN/UPC.
        gtinValido,
    };

    // ======================================================================
    // Registro rápido de productos sin salir de la pantalla actual
    // ======================================================================
    let modalRegistro = null, bsRegistro = null, resolverRegistro = null, productoGuardado = null;

    function construirModalRegistro() {
        if (modalRegistro) return;
        document.body.insertAdjacentHTML('beforeend', `
<div class="modal fade" id="contafyRegistroModal" tabindex="-1" aria-labelledby="contafyRegistroTitulo" aria-hidden="true">
  <div class="modal-dialog modal-xl modal-dialog-scrollable modal-fullscreen-lg-down">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="contafyRegistroTitulo"><i class="bi bi-box-seam me-2"></i>Registrar producto nuevo</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body p-0">
        <iframe class="cfr-marco" title="Formulario de producto nuevo" allow="camera" style="width:100%;height:75vh;border:0;display:block"></iframe>
      </div>
    </div>
  </div>
</div>`);
        modalRegistro = document.getElementById('contafyRegistroModal');
        bsRegistro = new bootstrap.Modal(modalRegistro);
        modalRegistro.addEventListener('hidden.bs.modal', () => {
            modalRegistro.querySelector('.cfr-marco').src = 'about:blank';
            const resolver = resolverRegistro; resolverRegistro = null;
            if (resolver) resolver(productoGuardado);
        });
        window.addEventListener('message', (e) => {
            if (e.origin !== window.location.origin || !e.data || e.data.tipo !== 'contafy:producto-guardado') return;
            productoGuardado = e.data.producto;
            bsRegistro.hide();
        });
    }

    window.ContafyRegistroRapido = {
        disponible() {
            return !!(window.CONTAFY_URL_CREAR_PRODUCTO && window.CONTAFY_PUEDE_CREAR_PRODUCTOS);
        },
        abrir({ codigo } = {}) {
            if (!this.disponible()) {
                if (window.Swal) Swal.fire({ icon: 'info', title: 'Sin permiso para registrar productos',
                    text: 'Pida al administrador de la empresa que registre este producto.' });
                return Promise.resolve(null);
            }
            construirModalRegistro();
            productoGuardado = null;
            const url = new URL(window.CONTAFY_URL_CREAR_PRODUCTO, window.location.origin);
            url.searchParams.set('embebido', '1');
            if (codigo) url.searchParams.set('codigo_barras', codigo);
            modalRegistro.querySelector('.cfr-marco').src = url.toString();
            return new Promise((resolve) => {
                resolverRegistro = resolve;
                bsRegistro.show();
            });
        },
    };
})();
