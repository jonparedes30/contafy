(function(){
    console.log('vision_scanner.js loaded');
    // Helper to get CSRF token from cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    function createModal() {
        if (document.getElementById('visionScannerModal')) return document.getElementById('visionScannerModal');
        const html = `
        <div class="modal fade" id="visionScannerModal" tabindex="-1">
          <div class="modal-dialog modal-lg">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Capturar imagen para identificación</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body text-center">
                <video id="vision-video" width="100%" height="360" autoplay playsinline style="border:1px solid #ddd;border-radius:6px; background:#000"></video>
                <canvas id="vision-canvas" style="display:none;"></canvas>
                <div class="mt-3 d-flex justify-content-center gap-2">
                  <button id="vision-capture" class="btn btn-primary">📸 Capturar</button>
                  <button id="vision-send" class="btn btn-success" disabled>🔎 Enviar</button>
                  <button id="vision-close" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                </div>
                <div id="vision-result" class="mt-3" style="display:none"></div>
              </div>
            </div>
          </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
        return document.getElementById('visionScannerModal');
    }

    async function openCameraAndBind() {
        const modalEl = createModal();
        const modal = new bootstrap.Modal(modalEl);
        const video = document.getElementById('vision-video');
        const canvas = document.getElementById('vision-canvas');
        const btnCapture = document.getElementById('vision-capture');
        const btnSend = document.getElementById('vision-send');
        const result = document.getElementById('vision-result');

        let stream = null;
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            video.srcObject = stream;
        } catch (err) {
            alert('No se pudo acceder a la cámara: ' + err.message);
            return;
        }

        btnCapture.onclick = function() {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            btnSend.disabled = false;
            result.style.display = 'none';
        };

        btnSend.onclick = async function() {
            btnSend.disabled = true;
            result.style.display = 'block';
            result.innerHTML = 'Enviando imagen al servicio...';

            const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
            try {
                const endpoint = window.empresaVisionEndpoint || (window.location.pathname.indexOf('/app-beta-2024/') !== -1 ? '/app-beta-2024/vision/recognize/' : '/empresa/vision/recognize/');
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') || ''
                    },
                    body: JSON.stringify({ image: dataUrl })
                });
                const j = await res.json();
                if (!res.ok) throw new Error(j.error || 'Error en servidor');
                showResults(j.results);
            } catch (e) {
                result.innerHTML = '<div class="alert alert-danger">Error: ' + e.message + '</div>';
            } finally {
                btnSend.disabled = false;
            }
        };

        modalEl.addEventListener('hidden.bs.modal', function () {
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
            }
            // cleanup listeners
            btnCapture.onclick = null;
            btnSend.onclick = null;
        }, { once: true });

        modal.show();
    }

    function showResults(results) {
        const result = document.getElementById('vision-result');
        result.style.display = 'block';
        let html = '';
        if (results.logos && results.logos.length) {
            html += '<h6>Logos</h6><ul>' + results.logos.map(l => `<li>${escapeHtml(l.description)} (${(l.score||0).toFixed(2)})</li>`).join('') + '</ul>';
        }
        if (results.labels && results.labels.length) {
            html += '<h6>Etiquetas</h6><ul>' + results.labels.map(l => `<li>${escapeHtml(l.description)} (${(l.score||0).toFixed(2)})</li>`).join('') + '</ul>';
        }
        if (results.texts && results.texts.length) {
            html += '<h6>Texto detectado</h6><pre>' + escapeHtml(results.texts.join('\n')) + '</pre>';
        }

        html += '<div class="mt-2 d-flex gap-2"><button id="vision-fill" class="btn btn-primary">Autorrellenar formulario</button><button id="vision-close2" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button></div>';
        result.innerHTML = html;

        document.getElementById('vision-fill').onclick = function() {
            buscarProductoEnInventario(results);
        };
    }

    async function buscarProductoEnInventario(results){

        const probes = [];

        if (results.texts && results.texts.length){
            probes.push(results.texts.slice(0,5).join(" "));
        }

        if (results.logos && results.logos.length){
            probes.push(results.logos.map(l => l.description).join(" "));
        }

        if (results.labels && results.labels.length){
            probes.push(results.labels.map(l => l.description).join(" "));
        }

        const endpoint =
            window.location.pathname.indexOf('/app-beta-2024/') !== -1
            ? '/app-beta-2024/empresa/prefill_producto_from_scan/'
            : '/empresa/prefill_producto_from_scan/';

        try{

            const res = await fetch(endpoint,{
                method:'POST',
                headers:{
                    'Content-Type':'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({probes})
            });

            const data = await res.json();

            if(!data.matches || !data.matches.length){
                mostrarMensajeInventario('No se encontró el producto en inventario.');
                return;
            }

            manejarResultadoProducto(data.matches);

        }catch(err){
            console.error(err);
            mostrarMensajeInventario('Error al buscar producto en inventario.');
        }
    }

    function mostrarMensajeInventario(msg){
        const result = document.getElementById('vision-result');
        result.innerHTML = `<div class="alert alert-warning">${msg}</div>`;
    }

    function manejarResultadoProducto(matches){

        const result = document.getElementById('vision-result');

        // Alta confianza → uno solo
        if(matches.length === 1 && (matches[0].score || 0) >= 0.65){
            seleccionarProducto(matches[0]);
            return;
        }

        let html = '<h6>Productos encontrados</h6>';
        html += '<ul class="list-group">';

        matches.forEach(p=>{
            html += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>${p.nombre}</strong><br>
                    Stock: ${p.stock || 0} | Precio: ${p.precio || ''}
                </div>
                <button class="btn btn-sm btn-primary"
                        onclick="seleccionarProducto(${p.id})">
                    Usar
                </button>
            </li>
        `;
        });

        html += '</ul>';

        result.innerHTML = html;

        // guardar temporalmente
        window.__visionMatches = matches;
    }

    window.seleccionarProducto = function(id){

        const producto = (typeof id === 'object') ? id : (window.__visionMatches && window.__visionMatches.find(p=>p.id === id)) || id;

        console.log("Producto seleccionado:", producto);

        const productoInput =
            document.querySelector('input[name="producto_id"]');

        if(productoInput && producto && producto.id){
            productoInput.value = producto.id;
        }

        const modalEl = document.getElementById('visionScannerModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if(modal) modal.hide();
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>\"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]; });
    }

    function autofillFromResults(results) {
        // Heurística simple: usar primer label o logo como nombre
        const firstLabel = (results.labels && results.labels[0] && results.labels[0].description) || null;
        const firstLogo = (results.logos && results.logos[0] && results.logos[0].description) || null;
        const firstText = (results.texts && results.texts[0]) || null;

        // Productos
        const inputNombre = document.getElementById('id_nombre');
        const inputDescripcion = document.getElementById('id_descripcion');
        const inputPrecio = document.getElementById('id_precio_unitario');
        const inputCodigoBarras = document.getElementById('id_codigo_barras') || document.getElementById('codigo_barras');

        if (inputNombre && (firstLabel || firstLogo)) {
            inputNombre.value = firstLabel || firstLogo;
        }
        if (inputDescripcion && firstText) {
            inputDescripcion.value = firstText;
        }

        // Si se detecta un código de barras en texto, intentar ponerlo
        if (inputCodigoBarras && firstText) {
            // buscar secuencia de 8-13 dígitos
            const m = firstText.match(/\b\d{8,13}\b/);
            if (m) inputCodigoBarras.value = m[0];
        }

        // Ventas/Compras: si hay un campo de producto por nombre, intentar buscar
        const productoInput = document.querySelector('input[name="producto"]') || document.getElementById('producto') || document.querySelector('input[name="producto_id"]');
        if (productoInput && (firstLabel || firstLogo)) {
            // poner nombre en el campo libre o disparar búsqueda existente
            productoInput.value = firstLabel || firstLogo;
        }

        // Cerrar modal tras rellenar
        const modalEl = document.getElementById('visionScannerModal');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }

    // Registrar manejadores
    function init() {
        document.querySelectorAll('#btn-scanner').forEach(btn => {
            btn.addEventListener('click', function(e){
                e.preventDefault();
                openCameraAndBind();
            });
        });

        // Reemplazar la función global escanearCodigo si existe
        window.escanearCodigo = function() { openCameraAndBind(); };
    }

    // Exponer init para que pueda llamarse explícitamente
    window.initVisionScanner = init;

    // Auto-init cuando DOM listo
    document.addEventListener('DOMContentLoaded', init);
    console.log('vision_scanner initialization script attached');
})();
