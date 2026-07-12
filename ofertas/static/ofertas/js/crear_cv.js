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

var listaIA     = document.getElementById('lista-cvs-ia');
var listaOferta = document.getElementById('lista-cvs-oferta');

CVS_GUARDADOS.forEach(function(cv) {
    if (listaIA) listaIA.appendChild(crearBtnCV(cv, function(texto) {
        document.getElementById('cv-ia-texto').value = texto;
    }));
    if (listaOferta) listaOferta.appendChild(crearBtnCV(cv, function(texto) {
        document.getElementById('cv-oferta-texto').value = texto;
    }));
});

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
                // data.texto es el JSON crudo, data.html es el HTML para preview
                cvActual = data.texto;
                preview.classList.remove('vacio');
                preview.innerHTML = data.html;
                activarDescarga();
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

// ── Llamada IA ────────────────────────────────────────────────────────────────
function llamarIA(url, body, btn) {
    var preview = document.getElementById('cv-preview');
    var labelOrig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader-2" style="animation:spin 1s linear infinite"></i> ' + (IDIOMA === 'en' ? 'Processing...' : 'Procesando...');
    preview.classList.remove('vacio');
    preview.innerHTML = '<div style="padding:40px; text-align:center; color:#94a3b8;"><i class="ti ti-sparkles" style="font-size:32px; display:block; margin-bottom:12px;"></i>' + (IDIOMA === 'en' ? 'AI is working...' : 'La IA está trabajando...') + '</div>';

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
            preview.classList.remove('vacio');
            preview.innerHTML = data.html;
            activarDescarga();
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

// ── Activar botón descargar ───────────────────────────────────────────────────
function activarDescarga() {
    var btn = document.getElementById('btn-descargar');
    if (btn) btn.disabled = false;
}

// ── Botón mejorar IA ──────────────────────────────────────────────────────────
var btnMejorar = document.getElementById('btn-mejorar');
if (btnMejorar) {
    btnMejorar.addEventListener('click', function() {
        var texto = document.getElementById('cv-ia-texto').value.trim();
        if (!texto) { alert(IDIOMA === 'en' ? 'Paste your CV first.' : 'Pega tu CV primero.'); return; }
        llamarIA(URL_MEJORAR, { cv_texto: texto }, this);
    });
}

// ── Botón adaptar oferta externa ──────────────────────────────────────────────
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
        var val = this.checked ? 'perfil' : 'ninguna';
        document.getElementById('opcion-foto-form').value = val;
        var label = document.getElementById('foto-label');
        if (label) label.classList.toggle('activa', this.checked);
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

// ── Submit PDF ────────────────────────────────────────────────────────────────
document.getElementById('form-pdf').addEventListener('submit', function(e) {
    if (!cvActual) {
        e.preventDefault();
        alert(IDIOMA === 'en' ? 'Generate a CV first.' : 'Genera un CV primero.');
        return;
    }
    document.getElementById('cv-contenido-hidden').value = cvActual;
    document.getElementById('plantilla-form').value = document.getElementById('plantilla-value').value;
});

// ── Animación spinner ─────────────────────────────────────────────────────────
var style = document.createElement('style');
style.textContent = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
document.head.appendChild(style);

})();