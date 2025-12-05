/**
 * OPTIMIZATION: Paginación server-side para sessions, acords y actes
 *
 * Features:
 * - Paginación server-side (50 items por página)
 * - Filtro por año (2016 - año actual, hardcodeado para performance)
 * - Primera carga directa con año actual
 * - Solo procesa items de la página actual
 */

// Constantes
const START_YEAR = 2016;  // Año inicial hardcodeado para performance
const CURRENT_YEAR = new Date().getFullYear();
const PAGE_SIZE = 50;

/**
 * Generar HTML del selector de años (2016 - año actual)
 */
function generateYearFilterHTML() {
  let html = '<option value="">Tots els anys</option>';
  for (let year = CURRENT_YEAR; year >= START_YEAR; year--) {
    html += `<option value="${year}" ${year === CURRENT_YEAR ? 'selected' : ''}>${year}</option>`;
  }
  return html;
}

// ==================== ACORDS ====================

let currentAcordsPage = 1;
let currentAcordsYear = CURRENT_YEAR;

function loadAcords(page, year = null) {
  $('.spinner-acords-tab').removeClass('d-none');
  $("#acordsTbody").empty();
  $("#acordsPagination").empty();

  const params = new URLSearchParams({ page: page, page_size: PAGE_SIZE });
  if (year) params.append('year', year);

  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getAcordsOrgangovern?' + params.toString(),
    success: function(result){
      const data = $.parseJSON(result);

      updateAcordsStats(data.total, data.page, data.page_size);

      if (data.items && data.items.length > 0) {
        $.each(data.items, function(key, value){
          var html = '<tr>';
          html += '<td style="vertical-align: middle;">';
          html += '<i class="bi bi-check me-1" aria-hidden="True"></i>';
          html += '<a href="' + value.absolute_url + '">' + value.title + '</a>';
          html += '</td>';
          html += '<td class="text-center align-middle">';
          if (value.agreement) html += '<span>' + value.agreement + '</span>';
          html += '</td>';
          html += '<td style="min-width: 100px" class="text-center align-middle">';
          html += '<span class="estatpunt"><i class="bi bi-circle-fill boletaGran" aria-hidden="true" style="color: ' + value.color + ';"></i> ';
          html += '<span> ' + value.estatsLlista + '</span></span>';
          html += '</td></tr>';
          $("#acordsTbody").append(html);
        });

        if (data.total_pages > 1) {
          renderPagination("#acordsPagination", data.total_pages, data.page, function(p) {
            currentAcordsPage = p;
            loadAcords(p, currentAcordsYear);
          }, "#acords-tab-panel");
        }
      } else {
        $("#acordsTbody").append('<tr><td colspan="3" class="text-center text-muted">No hi ha acords</td></tr>');
      }

      $('.spinner-acords-tab').addClass('d-none');
    },
    error: function() {
      $("#acordsTbody").html('<tr><td colspan="3" class="text-center text-danger">Error al carregar els acords.</td></tr>');
      $('.spinner-acords-tab').addClass('d-none');
    }
  });
}

function updateAcordsStats(total, page, pageSize) {
  const start = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const end = Math.min(page * pageSize, total);
  const text = total === 0 ? 'No hi ha acords' : `Mostrant ${start} - ${end} de ${total} acords`;
  $("#acords-stats").html('<small>' + text + '</small>');
}

// ==================== SESSIONS ====================

let currentSessionsPage = 1;
let currentSessionsYear = CURRENT_YEAR;

function loadSessions(page, year = null) {
  $('.spinner-sessions-tab').removeClass('d-none');
  $("#sessionsTbody").empty();
  $("#sessionsPagination").empty();

  const params = new URLSearchParams({ page: page, page_size: PAGE_SIZE });
  if (year) params.append('year', year);

  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getSessionsOrgangovern?' + params.toString(),
    success: function(result){
      const data = $.parseJSON(result);

      updateSessionsStats(data.total, data.page, data.page_size);

      if (data.items && data.items.length > 0) {
        $.each(data.items, function(key, value){
          var html = '<tr>';
          html += '<td style="vertical-align: middle;">';
          html += '<i class="bi bi-list" aria-hidden="True"></i>';
          html += '<a href="' + value.absolute_url + '">' + value.title + '</a>';
          html += ' [<span class="fs-s">' + value.sessionNumber + '</span>]';
          html += '</td>';
          html += '<td class="text-center align-middle">';
          html += '<span>' + value.dataSessio + '</span><br/>';
          html += '<span>' + value.horaInici + '</span>';
          html += '</td>';
          html += '<td class="text-center align-middle">';
          html += '<span>' + value.llocConvocatoria + '</span>';
          html += '</td>';
          html += '<td class="text-center align-middle">';
          html += '<span class="label-' + value.review_state + '">' + value.review_state_title + '</span>';
          html += '</td></tr>';
          $("#sessionsTbody").append(html);
        });

        if (data.total_pages > 1) {
          renderPagination("#sessionsPagination", data.total_pages, data.page, function(p) {
            currentSessionsPage = p;
            loadSessions(p, currentSessionsYear);
          }, "#sessions-tab-panel");
        }
      } else {
        $("#sessionsTbody").append('<tr><td colspan="4" class="text-center text-muted">No hi ha sessions</td></tr>');
      }

      $('.spinner-sessions-tab').addClass('d-none');
    },
    error: function() {
      $("#sessionsTbody").html('<tr><td colspan="4" class="text-center text-danger">Error al carregar les sessions.</td></tr>');
      $('.spinner-sessions-tab').addClass('d-none');
    }
  });
}

function updateSessionsStats(total, page, pageSize) {
  const start = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const end = Math.min(page * pageSize, total);
  const text = total === 0 ? 'No hi ha sessions' : `Mostrant ${start} - ${end} de ${total} sessions`;
  $("#sessions-stats").html('<small>' + text + '</small>');
}

// ==================== ACTES ====================

let currentActesPage = 1;
let currentActesYear = CURRENT_YEAR;

function loadActes(page, year = null) {
  $('.spinner-actas-tab').removeClass('d-none');
  $("#actesTbody").empty();
  $("#actesPagination").empty();

  const params = new URLSearchParams({ page: page, page_size: PAGE_SIZE });
  if (year) params.append('year', year);

  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getActesOrgangovern?' + params.toString(),
    success: function(result){
      const data = $.parseJSON(result);

      updateActesStats(data.total, data.page, data.page_size);

      if (data.items && data.items.length > 0) {
        $.each(data.items, function(key, value){
          var html = '<tr>';
          html += '<td>';
          html += '<i class="bi bi-file-text me-1" aria-hidden="true"></i>';
          html += '<a href="' + value.absolute_url + '">' + value.title + '</a>';
          html += '</td>';
          html += '<td class="text-center">';
          if (value.data) html += '<span>' + value.data + '</span>';
          html += '</td></tr>';
          $("#actesTbody").append(html);
        });

        if (data.total_pages > 1) {
          renderPagination("#actesPagination", data.total_pages, data.page, function(p) {
            currentActesPage = p;
            loadActes(p, currentActesYear);
          }, "#actas-tab-panel");
        }
      } else {
        $("#actesTbody").append('<tr><td colspan="2" class="text-center text-muted">No hi ha actes</td></tr>');
      }

      $('.spinner-actas-tab').addClass('d-none');
    },
    error: function() {
      $("#actesTbody").html('<tr><td colspan="2" class="text-center text-danger">Error al carregar les actes.</td></tr>');
      $('.spinner-actas-tab').addClass('d-none');
    }
  });
}

function updateActesStats(total, page, pageSize) {
  const start = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const end = Math.min(page * pageSize, total);
  const text = total === 0 ? 'No hi ha actes' : `Mostrant ${start} - ${end} de ${total} actes`;
  $("#actes-stats").html('<small>' + text + '</small>');
}

// ==================== PAGINACIÓN COMÚN ====================

function renderPagination(container, totalPages, currentPage, loadFunction, scrollTarget) {
  let html = '<nav aria-label="Paginació"><ul class="pagination mb-0">';

  // Botón anterior
  html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">`;
  html += `<a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Anterior">`;
  html += '<span aria-hidden="true">&laquo;</span></a></li>';

  // Números de página
  const maxVisible = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);
  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  if (startPage > 1) {
    html += '<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>';
    if (startPage > 2) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
  }

  for (let i = startPage; i <= endPage; i++) {
    html += `<li class="page-item ${i === currentPage ? 'active' : ''}">`;
    html += `<a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    html += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
  }

  // Botón siguiente
  html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">`;
  html += `<a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Siguiente">`;
  html += '<span aria-hidden="true">&raquo;</span></a></li>';

  html += '</ul></nav>';
  $(container).html(html);

  // Event listeners
  $(container + " .page-link").on("click", function(e) {
    e.preventDefault();
    const $this = $(this);
    if ($this.parent().hasClass('disabled') || $this.parent().hasClass('active')) return;

    const page = parseInt($this.data('page'));
    if (page > 0 && page <= totalPages) {
      loadFunction(page);
      $('html, body').animate({ scrollTop: $(scrollTarget).offset().top - 100 }, 300);
    }
  });
}

// ==================== INICIALIZACIÓN ====================

$(document).ready(function() {
  // Inicializar filtros de año con valores hardcodeados
  const yearFilterHTML = generateYearFilterHTML();

  // Sessions (tab activo por defecto)
  $("#sessions-year-filter").html(yearFilterHTML);
  $("#sessions-year-filter").val(CURRENT_YEAR);  // Forzar selección
  $("#sessions-year-filter").on("change", function() {
    currentSessionsYear = $(this).val() || null;
    currentSessionsPage = 1;
    loadSessions(1, currentSessionsYear);
  });
  // Cargar sessions del año actual directamente
  loadSessions(1, CURRENT_YEAR);

  // Acords
  $("#year-filter").html(yearFilterHTML);
  $("#year-filter").val(CURRENT_YEAR);  // Forzar selección
  $("#year-filter").on("change", function() {
    currentAcordsYear = $(this).val() || null;
    currentAcordsPage = 1;
    loadAcords(1, currentAcordsYear);
  });

  // Actes
  $("#actes-year-filter").html(yearFilterHTML);
  $("#actes-year-filter").val(CURRENT_YEAR);  // Forzar selección
  $("#actes-year-filter").on("change", function() {
    currentActesYear = $(this).val() || null;
    currentActesPage = 1;
    loadActes(1, currentActesYear);
  });
});

// ==================== TAB CLICK HANDLERS ====================

$("#acords-tab").on("click", function() {
  // Cargar acords del año actual
  loadAcords(1, currentAcordsYear);
  // Unbind para que no se ejecute múltiples veces
  $("#acords-tab").unbind("click");
});

$("#actes-tab").on("click", function() {
  // Cargar actes del año actual
  loadActes(1, currentActesYear);
  // Unbind para que no se ejecute múltiples veces
  $("#actes-tab").unbind("click");
});
