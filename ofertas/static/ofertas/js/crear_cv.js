(function() {

var CVS_GUARDADOS = JSON.parse(document.getElementById('cvs-data').textContent);
var cvActual = '';
var URL_STATUS = '/tarea/TASK_ID/status-cv/';

// ── Tabs modo ────────────────────────────────────────────────────────────────
document.querySelectorAll('.modo-tab').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var modo = this.dataset.modo;
        document.querySelectorAll('.modo-tab').forEach(function(t) { t.classList.remove('activo'); });
        document.querySelectorAll('.modo-contenido').forEach(function(c) { c.classList.remove('activo'); });
        this.classList.add('activo');
        document.getElementById('modo-' + modo).classList.add('activo');
    });
});

// ── CVs guardados ────────────────────────────────────────────────────────────
function crearBtnCV(cv, onClick) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-outline';
    btn.style.fontSize = '12px';
    btn.style.justifyContent = 'flex-start';
    btn.innerHTML = '<i class="ti ti-file-text"></i> ' + cv.nombre;
    btn.addEventListener('click', function() { onClick(cv.texto); });
    return btn;
}

var listaManual = document.getElementById('lista-cvs-manual');
var listaIA     = document.getElementById('lista-cvs-ia');
var listaOferta = document.getElementById('lista-cvs-oferta');

CVS_GUARDADOS.forEach(function(cv) {
    if (listaManual) listaManual.appendChild(crearBtnCV(cv, function(texto) {
        document.getElementById('cv-manual-texto').value = texto;
        actualizarPreviewManual();
    }));
    if (listaIA) listaIA.appendChild(crearBtnCV(cv, function(texto) {
        document.getElementById('cv-ia-texto').value = texto;
    }));
    if (listaOferta) listaOferta.appendChild(crearBtnCV(cv, function(texto) {
        document.getElementById('cv-oferta-texto').value = texto;
    }));
});

// ── Preview manual ───────────────────────────────────────────────────────────
var textareaManual = document.getElementById('cv-manual-texto');
if (textareaManual) {
    textareaManual.addEventListener('input', actualizarPreviewManual);
}

function actualizarPreviewManual() {
    var texto = document.getElementById('cv-manual-texto').value;
    var preview = document.getElementById('cv-preview');
    if (texto.trim()) {
        cvActual = texto;
        preview.classList.remove('vacio');
        preview.innerHTML = texto.replace(/\n/g, '<br>');
    } else {
        cvActual = '';
        preview.classList.add('vacio');
        preview.innerHTML = IDIOMA === 'en' ? 'Your CV will appear here...' : 'Tu CV aparecerá aquí...';
    }
}

// ── Polling Celery ───────────────────────────────────────────────────────────
function pollTask(taskId, btn, labelOrig) {
    var preview = document.getElementById('cv-preview');
    var intentos = 0;
    var intervalo = setInterval(function() {
        intentos++;
        if (intentos > 60) {
            clearInterval(intervalo);
            preview.innerHTML = '<p style="color:#dc2626;">' + (IDIOMA === 'en' ? 'Timeout. Try again.' : 'Tiempo agotado. Inténtalo de nuevo.') + '</p>';
            btn.disabled = false;
            btn.innerHTML = labelOrig;
            return;
        }
        fetch(URL_STATUS.replace('TASK_ID', taskId))
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status === 'ok') {
                clearInterval(intervalo);
                cvActual = data.texto;
                preview.innerHTML = data.html;
                btn.disabled = false;
                btn.innerHTML = labelOrig;
            } else if (data.status === 'error') {
                clearInterval(intervalo);
                preview.innerHTML = '<p style="color:#dc2626;">' + (data.mensaje || 'Error') + '</p>';
                btn.disabled = false;
                btn.innerHTML = labelOrig;
            }
        })
        .catch(function() {});
    }, 2000);
}

// ── Llamada IA genérica ───────────────────────────────────────────────────────
function llamarIA(url, body, btn) {
    var preview = document.getElementById('cv-preview');
    var labelOrig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="crear-spinner"></span>' + (IDIOMA === 'en' ? 'Processing...' : 'Procesando...');
    preview.classList.remove('vacio');
    preview.innerHTML = '<div class="preview-spinner"></div>';

    var csrf = document.querySelector('meta[name="csrf-token"]').content;
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrf },
        body: new URLSearchParams(body).toString()
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'pending') {
            pollTask(data.task_id, btn, labelOrig);
        } else if (data.status === 'ok') {
            cvActual = data.texto;
            preview.innerHTML = data.html;
            btn.disabled = false;
            btn.innerHTML = labelOrig;
        } else {
            preview.innerHTML = '<p style="color:#dc2626;">' + (data.mensaje || 'Error') + '</p>';
            btn.disabled = false;
            btn.innerHTML = labelOrig;
        }
    })
    .catch(function(err) {
        preview.innerHTML = '<p style="color:#dc2626;">' + err.message + '</p>';
        btn.disabled = false;
        btn.innerHTML = labelOrig;
    });
}

// ── Botones IA ────────────────────────────────────────────────────────────────
var btnMejorar = document.getElementById('btn-mejorar');
if (btnMejorar) {
    btnMejorar.addEventListener('click', function() {
        var texto = document.getElementById('cv-ia-texto').value.trim();
        if (!texto) { alert(IDIOMA === 'en' ? 'Paste your CV first.' : 'Pega tu CV primero.'); return; }
        llamarIA(URL_MEJORAR, { cv_texto: texto }, this);
    });
}

var btnAdaptar = document.getElementById('btn-adaptar');
if (btnAdaptar) {
    btnAdaptar.addEventListener('click', function() {
        var oferta = document.getElementById('oferta-externa-texto').value.trim();
        var cv     = document.getElementById('cv-oferta-texto').value.trim();
        if (!oferta) { alert(IDIOMA === 'en' ? 'Paste the job offer first.' : 'Pega la oferta primero.'); return; }
        if (!cv)     { alert(IDIOMA === 'en' ? 'Paste your CV first.' : 'Pega tu CV primero.'); return; }
        llamarIA(URL_ADAPTAR, { oferta_texto: oferta, cv_texto: cv }, this);
    });
}

// ── Copiar ────────────────────────────────────────────────────────────────────
var btnCopiar = document.getElementById('btn-copiar');
if (btnCopiar) {
    btnCopiar.addEventListener('click', function() {
        if (!cvActual) return;
        var btn = this;
        navigator.clipboard.writeText(cvActual).then(function() {
            var orig = btn.innerHTML;
            btn.innerHTML = '<i class="ti ti-check"></i> ' + (IDIOMA === 'en' ? 'Copied!' : '¡Copiado!');
            setTimeout(function() { btn.innerHTML = orig; }, 2000);
        });
    });
}

// ── Foto ──────────────────────────────────────────────────────────────────────
var checkFoto = document.getElementById('check-foto');
if (checkFoto) {
    checkFoto.addEventListener('change', function() {
        document.getElementById('opcion-foto-value').value = this.checked ? 'perfil' : 'ninguna';
    });
}

// ── Plantillas ────────────────────────────────────────────────────────────────
document.querySelectorAll('.plantilla-item').forEach(function(el) {
    el.addEventListener('click', function() {
        document.querySelectorAll('.plantilla-item').forEach(function(p) { p.classList.remove('activa'); });
        this.classList.add('activa');
        document.getElementById('plantilla-value').value = this.dataset.plantilla;
    });
});

// ── PDF ───────────────────────────────────────────────────────────────────────
document.getElementById('form-pdf').addEventListener('submit', function(e) {
    if (!cvActual) {
        e.preventDefault();
        alert(IDIOMA === 'en' ? 'Write or generate a CV first.' : 'Escribe o genera un CV primero.');
        return;
    }
    document.getElementById('cv-contenido-hidden').value = cvActual;
});

})();