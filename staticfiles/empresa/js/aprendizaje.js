// JS for leccion_interactiva (moved from template)
(function(){
    // read data from DOM
    const el = document.getElementById('lessonData');
    const DATA = el ? {
        leccionId: el.getAttribute('data-leccion-id'),
        pasosJson: el.getAttribute('data-leccion-pasos'),
        contenidoJs: el.getAttribute('data-leccion-contenido'),
        xp: el.getAttribute('data-leccion-xp'),
        urlPaso: el.getAttribute('data-url-paso'),
        urlSimTipos: el.getAttribute('data-url-simulacion-tipos'),
        urlSimEscenarios: el.getAttribute('data-url-simulacion-escenarios'),
        urlSimStart: el.getAttribute('data-url-simulacion-start')
    } : {};

    let currentStep = 1;
    const totalSteps = 4;
    let lessonData = null;
    let currentQuiz = 0;
    let score = 0;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    function mostrarToast(message, variant='success'){
        // Bootstrap toast
        const container = document.getElementById('toastContainer');
        if (!container) { alert(message); return; }
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-'+variant+' border-0';
        toast.setAttribute('role','alert');
        toast.setAttribute('aria-live','assertive');
        toast.setAttribute('aria-atomic','true');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', ()=> toast.remove());
    }

    function initializeLesson() {
        // parse pasos
        let pasos = null;
        try { pasos = DATA.pasosJson ? JSON.parse(DATA.pasosJson) : null; } catch(e){ pasos = null; }
        let contenido = DATA.contenidoJs || '';
        lessonData = {
            teoria: (contenido && contenido.length>0) ? contenido : 'Lee la teoría proporcionada en la lección.',
            pasos: pasos || [],
            quiz: []
        };
        const theoryEl = document.getElementById('theoryText');
        if (theoryEl) theoryEl.textContent = lessonData.teoria;
        const xpEl = document.getElementById('xpEarned');
        if (xpEl) xpEl.textContent = DATA.xp || '0';
        updateProgress();
    }

    function updateProgress(){
        const progress = (currentStep / totalSteps) * 100;
        const bar = document.getElementById('progressBar'); if (bar) bar.style.width = progress + '%';
        const cur = document.getElementById('currentStep'); if (cur) cur.textContent = currentStep;
    }

    function getStepName(step){ const steps=['','theory','practice','quiz','completion']; return steps[step]; }

    function nextStep(){
        const current = document.getElementById(`step-${getStepName(currentStep)}`);
        if (current) current.classList.add('d-none');
        currentStep++;
        if (currentStep===2) showPracticeStep();
        else if (currentStep===3) showQuizStep();
        else if (currentStep===4) showCompletionStep();
        updateProgress();
    }

    function showPracticeStep(){
        const practiceDiv = document.getElementById('practiceContent'); if(!practiceDiv) return;
        let html='';
        (lessonData.pasos||[]).forEach((paso,index)=>{
            html += `\n            <div class="practice-step">\n                <h4><i class="fas fa-play-circle text-primary"></i> ${paso.titulo}</h4>\n                <p>${paso.descripcion}</p>\n                <div class="alert alert-info">\n                    <strong>En CONTAFY:</strong> ${getPracticeInstructions(paso)}\n                </div>\n                <div class="d-flex justify-content-end">\n                    <button id="marcar-paso-${index}" class="btn btn-outline-primary btn-sm">Marcar paso completado</button>\n                </div>\n            </div>\n            `;
        });
        practiceDiv.innerHTML = html;
        // attach handlers for mark buttons
        (lessonData.pasos||[]).forEach((paso,index)=>{
            const btn = document.getElementById(`marcar-paso-${index}`);
            if (btn) btn.addEventListener('click', ()=> marcarPaso(index));
        });
        const stepPractice = document.getElementById('step-practice'); if(stepPractice) stepPractice.classList.remove('d-none');
    }

    function getPracticeInstructions(paso){
        try{
            const datos = paso.datos || {};
            if (paso.accion === 'crear_producto'){
                const nombre = datos.nombre || 'Nuevo Producto';
                const codigo = datos.codigo || 'AUTO';
                const precio = datos.precio_venta ? `$${datos.precio_venta}` : 'establece un precio';
                return `Ve a "Inventario > + Nuevo Producto" y crea: ${nombre}, código ${codigo}, precio ${precio}`;
            } else if (paso.accion === 'crear_venta'){
                const cantidad = datos.cantidad || 1;
                const producto = datos.producto || 'el producto creado';
                return `Ve a "Transacciones > + Nueva Venta" y vende ${cantidad} unidades de ${producto}`;
            }
        }catch(e){ }
        return 'Sigue las instrucciones en CONTAFY';
    }

    function marcarPaso(pasoIndex){
        const url = DATA.urlPaso || '';
        const payload = { leccion_id: DATA.leccionId, paso_index: pasoIndex, micro_xp: 5 };
        fetch(url, {
            method:'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type':'application/json' },
            body: JSON.stringify(payload)
        }).then(r=>r.json()).then(data=>{
            if (data && data.ok){
                mostrarToast('Paso registrado. +'+(data.resultado?data.resultado.xp_otorgada:5)+' XP');
                const btn = document.getElementById(`marcar-paso-${pasoIndex}`);
                if (btn) { btn.disabled = true; btn.textContent = 'Completado'; btn.classList.remove('btn-outline-primary'); btn.classList.add('btn-success'); }
            } else {
                mostrarToast((data && (data.message||data.error)) || 'Paso ya registrado','warning');
            }
        }).catch(()=> mostrarToast('Error al registrar paso','danger'));
    }

    function showQuizStep(){
        const quizDiv = document.getElementById('quizContent'); if(!quizDiv) return;
        const question = (lessonData && lessonData.quiz) ? lessonData.quiz[currentQuiz] : null;
        if (!question){ nextStep(); return; }
        let html = `\n        <div class="quiz-question">\n            <h4 class="mb-4">${question.pregunta}</h4>\n            <div class="quiz-options">\n        `;
        (question.opciones||[]).forEach((opcion,index)=>{
            html += `\n            <div class="quiz-option" data-index="${index}">\n                <i class="fas fa-circle me-2"></i> ${opcion}\n            </div>\n        `;
        });
        html += `\n            </div>\n        </div>\n        `;
        quizDiv.innerHTML = html;
        // attach handlers
        document.querySelectorAll('.quiz-option').forEach(opt=> opt.addEventListener('click', ()=> selectAnswer(parseInt(opt.getAttribute('data-index')))));
        const stepQuiz = document.getElementById('step-quiz'); if(stepQuiz) stepQuiz.classList.remove('d-none');
    }

    function selectAnswer(selectedIndex){
        const question = (lessonData && lessonData.quiz) ? lessonData.quiz[currentQuiz] : null; if(!question) return;
        const options = document.querySelectorAll('.quiz-option');
        options.forEach((option, index)=>{
            const idx = parseInt(option.getAttribute('data-index'));
            if (idx === question.respuesta){ option.classList.add('correct'); option.innerHTML = '<i class="fas fa-check me-2"></i>'+question.opciones[idx]; }
            else if (idx === selectedIndex && idx !== question.respuesta){ option.classList.add('incorrect'); option.innerHTML = '<i class="fas fa-times me-2"></i>'+question.opciones[idx]; }
            option.style.pointerEvents = 'none';
        });
        if (selectedIndex === question.respuesta) score++;
        setTimeout(()=>{ currentQuiz++; if (currentQuiz < (lessonData.quiz||[]).length) showQuizStep(); else nextStep(); }, 1500);
    }

    function showCompletionStep(){ const el = document.getElementById('step-completion'); if (el) el.classList.remove('d-none'); }

    function startSimulacion(){
        const tipo = document.getElementById('selectSimulacion').value;
        const escenario = document.getElementById('selectEscenario').value || null;
        if (!tipo){ mostrarToast('Selecciona una simulación','warning'); return; }
        const url = DATA.urlSimStart || '';
        const payload = { tipo_id: tipo, escenario_id: escenario, leccion_id: DATA.leccionId };
        fetch(url, { method:'POST', headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type':'application/json' }, body: JSON.stringify(payload) })
            .then(r=>r.json()).then(data=>{
                if (data && data.ok){ mostrarToast('Simulación iniciada'); openSimModal(data.simulacion_id, data.datos_iniciales || {}); }
                else mostrarToast((data && (data.error||data.message))||'No se pudo iniciar la simulación','danger');
            }).catch(()=> mostrarToast('Error al iniciar simulación','danger'));
    }

    function populateSimulaciones(simList){
        const sel = document.getElementById('selectSimulacion'); if(!sel) return;
        sel.innerHTML = '<option value="">-- Seleccionar --</option>';
        simList.forEach(s=>{ const opt = document.createElement('option'); opt.value=s.id; opt.textContent = s.nombre+' ('+s.categoria+')'; sel.appendChild(opt); });
    }

    function openSimModal(id, datos){ try{ const modalIdEl = document.getElementById('simModalId'); const modalBodyEl = document.getElementById('simModalBody'); if(modalIdEl) modalIdEl.textContent = String(id); if(modalBodyEl) modalBodyEl.textContent = JSON.stringify(datos,null,2); if(window.bootstrap && document.getElementById('simModal')){ const bsModal = new bootstrap.Modal(document.getElementById('simModal')); bsModal.show(); } else alert('Simulación iniciada. ID: '+id+'\nDatos: '+JSON.stringify(datos)); }catch(e){ console.error(e); alert('Simulación iniciada. ID: '+id); } }

    // wire DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function(){
        initializeLesson();
        // fetch tipos
        if (DATA.urlSimTipos){ fetch(DATA.urlSimTipos).then(r=>r.json()).then(d=>{ if(d&&d.ok && Array.isArray(d.tipos)){ populateSimulaciones(d.tipos); }}).catch(()=>{}); }
        // attach change handler once
        const sel = document.getElementById('selectSimulacion');
        if (sel && !sel._simChangeAttached){ sel._simChangeAttached = true; sel.addEventListener('change', function(){ const val=sel.value; const esc = document.getElementById('selectEscenario'); if(!val){ esc.classList.add('d-none'); return;} if (DATA.urlSimEscenarios) { fetch(DATA.urlSimEscenarios+'?tipo_id='+val).then(r=>r.json()).then(d=>{ esc.innerHTML='<option value="">-- Escenario --</option>'; if(d && d.ok && Array.isArray(d.escenarios)){ d.escenarios.forEach(e=>{ const o = document.createElement('option'); o.value=e.id; o.textContent=e.nombre; esc.appendChild(o); }); esc.classList.remove('d-none'); } else esc.classList.add('d-none'); }).catch(()=>esc.classList.add('d-none')); } }); }
        // Attach start button
        const btn = document.getElementById('btnStartSim'); if (btn) btn.addEventListener('click', startSimulacion);
    });

    // expose some functions for inline onclicks that remain
    window.nextStep = nextStep;
    window.completeLesson = function(){ fetch('', { method:'POST', headers:{ 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type':'application/json' }, body: JSON.stringify({ completed:true, score: score }) }).then(()=>{ window.location.href = document.getElementById('lessonData').getAttribute('data-url-modulo') || '/'; }); };
    window.startSimulacion = startSimulacion;
    window.marcarPaso = marcarPaso;
})();
