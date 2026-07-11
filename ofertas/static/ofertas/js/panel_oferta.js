(function () {
  const panel     = document.getElementById('panel-detalle');
  const btnCerrar = document.getElementById('panel-cerrar');

  if (!panel) return;

  // ── Abrir panel al hacer click en tarjeta ────────────────────────────────
  document.querySelectorAll('.card[data-oferta-id]').forEach(el => {
    el.addEventListener('click', function (e) {
      if (e.target.closest('a') || e.target.closest('button') || e.target.closest('input')) return;
      if (e.target.closest('[data-accion]')) return;
      const id = this.dataset.ofertaId;
      abrirPanel(id);
    });
  });

  async function abrirPanel(id) {
    panel.classList.remove('panel--oculto');
    panel.classList.add('panel--cargando');
    document.querySelectorAll('.card').forEach(c => c.classList.remove('card--activa'));
    const tarjeta = document.querySelector(`.card[data-oferta-id="${id}"]`);
    if (tarjeta) tarjeta.classList.add('card--activa');

    try {
      const res = await fetch(`/ofertas/${id}/`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!res.ok) throw new Error('Error de red');
      const data = await res.json();
      renderPanel(data);
    } catch (err) {
      document.getElementById('panel-descripcion').innerHTML =
        '<p style="color:#dc2626;">No se pudo cargar la oferta.</p>';
    } finally {
      panel.classList.remove('panel--cargando');
    }
  }

  function renderPanel(data) {
    document.getElementById('panel-titulo').textContent    = data.titulo;
    document.getElementById('panel-empresa').textContent   = data.empresa;
    document.getElementById('panel-ubicacion').textContent = data.ubicacion;
    document.getElementById('panel-fecha').textContent     = data.fecha_publicacion;
    document.getElementById('panel-fuente').textContent    = data.fuente;
    document.getElementById('panel-descripcion').innerHTML = data.descripcion.replace(/\n/g, '<br>');
    document.getElementById('panel-url').href              = data.url_original;

    const linkCvmatch = document.getElementById('panel-link-cvmatch');
    if (linkCvmatch) linkCvmatch.href = `/ofertas/${data.id}/`;

    const linkAnalizar = document.getElementById('panel-link-analizar');
    if (linkAnalizar) linkAnalizar.href = `/ofertas/${data.id}/analizar/`;
  }

  // ── Cerrar panel ─────────────────────────────────────────────────────────
  if (btnCerrar) {
    btnCerrar.addEventListener('click', () => {
      panel.classList.add('panel--oculto');
      document.querySelectorAll('.card').forEach(c => c.classList.remove('card--activa'));
    });
  }
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      panel.classList.add('panel--oculto');
      document.querySelectorAll('.card').forEach(c => c.classList.remove('card--activa'));
    }
  });

  // ── Cambiar estado AJAX desde tarjeta ────────────────────────────────────
  document.querySelectorAll('[data-cambiar-estado]').forEach(btn => {
    btn.addEventListener('click', async function (e) {
      e.stopPropagation();
      const id     = this.dataset.ofertaId;
      const estado = this.dataset.cambiarEstado;
      if (!id) return;
      const csrf = document.querySelector('meta[name="csrf-token"]').content;

      try {
        await fetch(`/ofertas/${id}/estado/${estado}/`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf,
          }
        });
        const tarjeta = document.querySelector(`.card[data-oferta-id="${id}"]`);
        if (tarjeta) tarjeta.remove();
        panel.classList.add('panel--oculto');
      } catch (err) {
        console.error('Error cambiando estado:', err);
      }
    });
  });

})();