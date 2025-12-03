/**
 * OPTIMIZATION: Paginación server-side para acords y actes
 *
 * Features:
 * - Paginación server-side (50 items por página)
 * - Filtro por año (por defecto año actual)
 * - Carga solo los datos necesarios
 * - Estadísticas de resultados
 */

// Variables globales para paginación de acords
let currentAcordsPage = 1;
let currentAcordsYear = new Date().getFullYear();
let acordsMinYear = null;  // Se calculará dinámicamente
let acordsFilterInitialized = false;  // Para saber si ya se inicializó el filtro

/**
 * Inicializar filtro de año para acords
 * @param {number|null} minYear - Año mínimo disponible (calculado del backend)
 * @param {number|null} maxYear - Año máximo disponible (calculado del backend)
 */
function initYearFilter(minYear = null, maxYear = null) {
  const currentYear = new Date().getFullYear();
  const startYear = maxYear || currentYear;
  const endYear = minYear || 2010;  // Fallback por si no hay datos

  let filterHTML = '<option value="">Tots els anys</option>';

  // Años desde el más reciente hasta el más antiguo
  for (let year = startYear; year >= endYear; year--) {
    filterHTML += `<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}</option>`;
  }

  $("#year-filter").html(filterHTML);

  // Event listener para cambio de año (solo añadir una vez)
  $("#year-filter").off("change").on("change", function(){
    currentAcordsYear = $(this).val();
    currentAcordsPage = 1;  // Reset a primera página
    loadAcords(currentAcordsPage, currentAcordsYear);
  });

  // Si el año actual está en el rango, filtrar automáticamente por año actual
  if (currentYear >= endYear && currentYear <= startYear) {
    currentAcordsYear = currentYear;
    loadAcords(1, currentAcordsYear);
  }
}

/**
 * Cargar acords con paginación
 * @param {number} page - Número de página a cargar
 * @param {string|null} year - Año a filtrar (null = todos)
 */
function loadAcords(page, year = null) {
  $('.spinner-acords-tab').removeClass('d-none');
  $("#acordsTbody").empty();
  $("#acordsPagination").empty();

  const params = new URLSearchParams({
    page: page,
    page_size: 50
  });

  if (year) {
    params.append('year', year);
  }

  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getAcordsOrgangovern?' + params.toString(),
    success: function(result){
      const data = $.parseJSON(result);

      // Inicializar filtro de años en la primera carga (sin año)
      // Después de inicializar, se hace otra llamada con el año actual
      if (!acordsFilterInitialized && data.min_year && data.max_year) {
        initYearFilter(data.min_year, data.max_year);
        acordsFilterInitialized = true;
        // IMPORTANTE: Return aquí porque initYearFilter ya llamó a loadAcords con el año
        return;
      }

      // Actualizar estadísticas
      updateAcordsStats(data.total, data.page, data.page_size);

      // Renderizar items
      if (data.items && data.items.length > 0) {
        $.each(data.items, function(key, value){
          var acordHTML = '<tr>';
          acordHTML += '<td style="vertical-align: middle;">';
          acordHTML += '<i class="bi bi-check me-1" aria-hidden="True"></i>';
          acordHTML += '<a href="' + value['absolute_url'] + '">';
          acordHTML += value['title'];
          acordHTML += '</a>';
          acordHTML += '</td>';
          acordHTML += '<td class="text-center align-middle">';
          if (value['agreement']){
            acordHTML += '<span>';
            acordHTML += value['agreement'];
            acordHTML += '</span>';
          }
          acordHTML += '</td>';
          acordHTML += '<td style="min-width: 100px" class="text-center align-middle">';
          acordHTML += '<span class="estatpunt">';
          acordHTML += '<i class="bi bi-circle-fill boletaGran" aria-hidden="true" style="color: ' + value['color'] + ';"></i> ';
          acordHTML += '<span> ';
          acordHTML += value['estatsLlista'];
          acordHTML += '</span>';
          acordHTML += '</span>';
          acordHTML += '</td>';
          acordHTML += '</tr>';
          $("#acordsTbody").append(acordHTML);
        });

        // Renderizar paginación si hay más de una página
        if (data.total_pages > 1) {
          renderAcordsPagination(data.total_pages, data.page);
        }
      } else {
        // Mensaje de sin resultados
        $("#acordsTbody").append(
          '<tr><td colspan="3" class="text-center text-muted">' +
          'No hi ha acords' +
          '</td></tr>'
        );
      }

      $('.spinner-acords-tab').addClass('d-none');
    },
    error: function() {
      $("#acordsTbody").html(
        '<tr><td colspan="3" class="text-center text-danger">' +
        'Error al carregar els acords.' +
        '</td></tr>'
      );
      $('.spinner-acords-tab').addClass('d-none');
    }
  });
}

/**
 * Actualizar estadísticas de acords
 */
function updateAcordsStats(total, page, pageSize) {
  const start = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const end = Math.min(page * pageSize, total);

  let statsHTML = '<small>';
  if (total === 0) {
    statsHTML += 'No hi ha acords';
  } else {
    statsHTML += `Mostrant ${start} - ${end} de ${total} acords`;
  }
  statsHTML += '</small>';

  $("#acords-stats").html(statsHTML);
}

/**
 * Renderizar paginación de acords
 * @param {number} totalPages - Total de páginas
 * @param {number} currentPage - Página actual
 */
function renderAcordsPagination(totalPages, currentPage) {
  let paginationHTML = '<nav aria-label="Paginació acords"><ul class="pagination mb-0">';

  // Botón anterior
  paginationHTML += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">`;
  paginationHTML += `<a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Anterior">`;
  paginationHTML += '<span aria-hidden="true">&laquo;</span>';
  paginationHTML += '</a></li>';

  // Números de página
  const maxVisible = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  // Ajustar startPage si estamos cerca del final
  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  // Primera página
  if (startPage > 1) {
    paginationHTML += `<li class="page-item">`;
    paginationHTML += `<a class="page-link" href="#" data-page="1">1</a>`;
    paginationHTML += '</li>';
    if (startPage > 2) {
      paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
  }

  // Páginas visibles
  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}">`;
    paginationHTML += `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
    paginationHTML += '</li>';
  }

  // Última página
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
    paginationHTML += `<li class="page-item">`;
    paginationHTML += `<a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>`;
    paginationHTML += '</li>';
  }

  // Botón siguiente
  paginationHTML += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">`;
  paginationHTML += `<a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Siguiente">`;
  paginationHTML += '<span aria-hidden="true">&raquo;</span>';
  paginationHTML += '</a></li>';

  paginationHTML += '</ul></nav>';

  $("#acordsPagination").html(paginationHTML);

  // Event listeners para paginación
  $("#acordsPagination .page-link").on("click", function(e){
    e.preventDefault();
    const $this = $(this);

    // No hacer nada si está deshabilitado o es active
    if ($this.parent().hasClass('disabled') || $this.parent().hasClass('active')) {
      return;
    }

    const page = parseInt($this.data('page'));
    if (page > 0 && page <= totalPages) {
      currentAcordsPage = page;
      loadAcords(page, currentAcordsYear);

      // Scroll suave al inicio de la tabla
      $('html, body').animate({
        scrollTop: $("#acords-tab-panel").offset().top - 100
      }, 300);
    }
  });
}

// ==================== SESSIONS ====================

// Variables globales para paginación de sessions
let currentSessionsPage = 1;
let currentSessionsYear = new Date().getFullYear();
let sessionsFilterInitialized = false;

/**
 * Inicializar filtro de año para sessions
 */
function initSessionsYearFilter(minYear = null, maxYear = null) {
  const currentYear = new Date().getFullYear();
  const startYear = maxYear || currentYear;
  const endYear = minYear || 2010;

  let filterHTML = '<option value="">Tots els anys</option>';

  for (let year = startYear; year >= endYear; year--) {
    filterHTML += `<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}</option>`;
  }

  $("#sessions-year-filter").html(filterHTML);

  $("#sessions-year-filter").off("change").on("change", function(){
    currentSessionsYear = $(this).val();
    currentSessionsPage = 1;
    loadSessions(currentSessionsPage, currentSessionsYear);
  });

  // Si el año actual está en el rango, filtrar automáticamente
  if (currentYear >= endYear && currentYear <= startYear) {
    currentSessionsYear = currentYear;
    loadSessions(1, currentSessionsYear);
  }
}

/**
 * Cargar sessions con paginación
 */
function loadSessions(page, year = null) {
  $('.spinner-sessions-tab').removeClass('d-none');
  $("#sessionsTbody").empty();
  $("#sessionsPagination").empty();

  const params = new URLSearchParams({
    page: page,
    page_size: 50
  });

  if (year) {
    params.append('year', year);
  }

  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getSessionsOrgangovern?' + params.toString(),
    success: function(result){
      const data = $.parseJSON(result);

      // Inicializar filtro de años en la primera carga (sin año)
      // Después de inicializar, se hace otra llamada con el año actual
      if (!sessionsFilterInitialized && data.min_year && data.max_year) {
        initSessionsYearFilter(data.min_year, data.max_year);
        sessionsFilterInitialized = true;
        // IMPORTANTE: Return aquí porque initSessionsYearFilter ya llamó a loadSessions con el año
        return;
      }

      // Actualizar estadísticas
      updateSessionsStats(data.total, data.page, data.page_size);

      // Renderizar items
      if (data.items && data.items.length > 0) {
        $.each(data.items, function(key, value){
          var sessionHTML = '<tr>';
          sessionHTML += '<td style="vertical-align: middle;">';
          sessionHTML += '<i class="bi bi-list" aria-hidden="True"></i>';
          sessionHTML += '<a href="' + value['absolute_url'] + '">';
          sessionHTML += value['title'];
          sessionHTML += '</a>';
          sessionHTML += ' [<span class="fs-s">' + value['sessionNumber'] + '</span>]';
          sessionHTML += '</td>';
          sessionHTML += '<td class="text-center align-middle">';
          sessionHTML += '<span>' + value['dataSessio'] + '</span>';
          sessionHTML += '<br/>';
          sessionHTML += '<span>' + value['horaInici'] + '</span>';
          sessionHTML += '</td>';
          sessionHTML += '<td class="text-center align-middle">';
          sessionHTML += '<span>' + value['llocConvocatoria'] + '</span>';
          sessionHTML += '</td>';
          sessionHTML += '<td class="text-center align-middle">';
          sessionHTML += '<span class="label-' + value['review_state'] + '">' + value['review_state'] + '</span>';
          sessionHTML += '</td>';
          sessionHTML += '</tr>';
          $("#sessionsTbody").append(sessionHTML);
        });

        // Renderizar paginación si hay más de una página
        if (data.total_pages > 1) {
          renderSessionsPagination(data.total_pages, data.page);
        }
      } else {
        $("#sessionsTbody").append(
          '<tr><td colspan="4" class="text-center text-muted">' +
          'No hi ha sessions' +
          '</td></tr>'
        );
      }

      $('.spinner-sessions-tab').addClass('d-none');
    },
    error: function() {
      $("#sessionsTbody").html(
        '<tr><td colspan="4" class="text-center text-danger">' +
        'Error al carregar les sessions.' +
        '</td></tr>'
      );
      $('.spinner-sessions-tab').addClass('d-none');
    }
  });
}

/**
 * Actualizar estadísticas de sessions
 */
function updateSessionsStats(total, page, pageSize) {
  const start = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const end = Math.min(page * pageSize, total);

  let statsHTML = '<small>';
  if (total === 0) {
    statsHTML += 'No hi ha sessions';
  } else {
    statsHTML += `Mostrant ${start} - ${end} de ${total} sessions`;
  }
  statsHTML += '</small>';

  $("#sessions-stats").html(statsHTML);
}

/**
 * Renderizar paginación de sessions
 */
function renderSessionsPagination(totalPages, currentPage) {
  let paginationHTML = '<nav aria-label="Paginació sessions"><ul class="pagination mb-0">';

  // Botón anterior
  paginationHTML += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">`;
  paginationHTML += `<a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Anterior">`;
  paginationHTML += '<span aria-hidden="true">&laquo;</span>';
  paginationHTML += '</a></li>';

  // Números de página
  const maxVisible = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  if (startPage > 1) {
    paginationHTML += '<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>';
    if (startPage > 2) {
      paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}">`;
    paginationHTML += `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
    paginationHTML += '</li>';
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
    paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
  }

  // Botón siguiente
  paginationHTML += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">`;
  paginationHTML += `<a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Siguiente">`;
  paginationHTML += '<span aria-hidden="true">&raquo;</span>';
  paginationHTML += '</a></li>';

  paginationHTML += '</ul></nav>';

  $("#sessionsPagination").html(paginationHTML);

  // Event listeners para paginación
  $("#sessionsPagination .page-link").on("click", function(e){
    e.preventDefault();
    const $this = $(this);

    if ($this.parent().hasClass('disabled') || $this.parent().hasClass('active')) {
      return;
    }

    const page = parseInt($this.data('page'));
    if (page > 0 && page <= totalPages) {
      currentSessionsPage = page;
      loadSessions(page, currentSessionsYear);

      $('html, body').animate({
        scrollTop: $("#sessions-tab-panel").offset().top - 100
      }, 300);
    }
  });
}

// ==================== SESSIONS TAB (carga inicial) ====================

// Cargar sessions automáticamente cuando la página se carga (es el tab activo)
$(document).ready(function(){
  loadSessions(1, null);
});

// ==================== ACORDS TAB ====================

$("#acords-tab").on("click", function(){
  // Primera carga SIN filtrar por año
  loadAcords(1, null);

  // Unbind para que no se ejecute múltiples veces
  $("#acords-tab").unbind("click");
});

// ==================== ACTES ====================

// Variables globales para paginación de actes
let currentActesPage = 1;
let currentActesYear = new Date().getFullYear();
let actesFilterInitialized = false;

/**
 * Inicializar filtro de año para actes
 */
function initActesYearFilter(minYear = null, maxYear = null) {
  const currentYear = new Date().getFullYear();
  const startYear = maxYear || currentYear;
  const endYear = minYear || 2010;

  let filterHTML = '<option value="">Tots els anys</option>';

  for (let year = startYear; year >= endYear; year--) {
    filterHTML += `<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}</option>`;
  }

  $("#actes-year-filter").html(filterHTML);

  $("#actes-year-filter").off("change").on("change", function(){
    currentActesYear = $(this).val();
    currentActesPage = 1;
    loadActes(currentActesPage, currentActesYear);
  });

  // Si el año actual está en el rango, filtrar automáticamente
  if (currentYear >= endYear && currentYear <= startYear) {
    currentActesYear = currentYear;
    loadActes(1, currentActesYear);
  }
}

/**
 * Cargar actes con paginación
 */
function loadActes(page, year = null) {
  $('.spinner-actas-tab').removeClass('d-none');
  $("#actesTbody").empty();
  $("#actesPagination").empty();

  const params = new URLSearchParams({
    page: page,
    page_size: 50
  });

  if (year) {
    params.append('year', year);
  }

  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getActesOrgangovern?' + params.toString(),
    success: function(result){
      const data = $.parseJSON(result);

      // Inicializar filtro de años en la primera carga (sin año)
      if (!actesFilterInitialized && data.min_year && data.max_year) {
        initActesYearFilter(data.min_year, data.max_year);
        actesFilterInitialized = true;
        // Return porque initActesYearFilter ya llamó a loadActes con el año
        return;
      }

      // Actualizar estadísticas
      updateActesStats(data.total, data.page, data.page_size);

      // Renderizar items
      if (data.items && data.items.length > 0) {
        $.each(data.items, function(key, value){
          var actaHTML = '<tr>';
          actaHTML += '<td>';
          actaHTML += '<i class="bi bi-file-text me-1" aria-hidden="true"></i>';
          actaHTML += '<a href="' + value['absolute_url'] + '">';
          actaHTML += value['title'];
          actaHTML += '</a>';
          actaHTML += '</td>';
          actaHTML += '<td class="text-center">';
          if (value['data']){
            actaHTML += '<span>';
            actaHTML += value['data'];
            actaHTML += '</span>';
          }
          actaHTML += '</td>';
          actaHTML += '</tr>';

          $("#actesTbody").append(actaHTML);
        });

        // Renderizar paginación si hay más de una página
        if (data.total_pages > 1) {
          renderActesPagination(data.total_pages, data.page);
        }
      } else {
        $("#actesTbody").append(
          '<tr><td colspan="2" class="text-center text-muted">' +
          'No hi ha actes' +
          '</td></tr>'
        );
      }

      $('.spinner-actas-tab').addClass('d-none');
    },
    error: function() {
      $("#actesTbody").html(
        '<tr><td colspan="2" class="text-center text-danger">' +
        'Error al carregar les actes.' +
        '</td></tr>'
      );
      $('.spinner-actas-tab').addClass('d-none');
    }
  });
}

/**
 * Actualizar estadísticas de actes
 */
function updateActesStats(total, page, pageSize) {
  const start = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const end = Math.min(page * pageSize, total);

  let statsHTML = '<small>';
  if (total === 0) {
    statsHTML += 'No hi ha actes';
  } else {
    statsHTML += `Mostrant ${start} - ${end} de ${total} actes`;
  }
  statsHTML += '</small>';

  $("#actes-stats").html(statsHTML);
}

/**
 * Renderizar paginación de actes
 */
function renderActesPagination(totalPages, currentPage) {
  let paginationHTML = '<nav aria-label="Paginació actes"><ul class="pagination mb-0">';

  // Botón anterior
  paginationHTML += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">`;
  paginationHTML += `<a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Anterior">`;
  paginationHTML += '<span aria-hidden="true">&laquo;</span>';
  paginationHTML += '</a></li>';

  // Números de página
  const maxVisible = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  if (startPage > 1) {
    paginationHTML += '<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>';
    if (startPage > 2) {
      paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}">`;
    paginationHTML += `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
    paginationHTML += '</li>';
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
    paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
  }

  // Botón siguiente
  paginationHTML += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">`;
  paginationHTML += `<a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Siguiente">`;
  paginationHTML += '<span aria-hidden="true">&raquo;</span>';
  paginationHTML += '</a></li>';

  paginationHTML += '</ul></nav>';

  $("#actesPagination").html(paginationHTML);

  // Event listeners para paginación
  $("#actesPagination .page-link").on("click", function(e){
    e.preventDefault();
    const $this = $(this);

    if ($this.parent().hasClass('disabled') || $this.parent().hasClass('active')) {
      return;
    }

    const page = parseInt($this.data('page'));
    if (page > 0 && page <= totalPages) {
      currentActesPage = page;
      loadActes(page, currentActesYear);

      $('html, body').animate({
        scrollTop: $("#actas-tab-panel").offset().top - 100
      }, 300);
    }
  });
}

// ==================== ACTES TAB ====================

$("#actes-tab").on("click", function(){
  // Primera carga SIN filtrar por año
  loadActes(1, null);

  // Unbind para que no se ejecute múltiples veces
  $("#actes-tab").unbind("click");
});
