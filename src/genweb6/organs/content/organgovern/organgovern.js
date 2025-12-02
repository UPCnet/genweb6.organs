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

      // Inicializar filtro de años en la primera carga
      if (!acordsFilterInitialized && data.min_year && data.max_year) {
        initYearFilter(data.min_year, data.max_year);
        acordsFilterInitialized = true;
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

// ==================== ACORDS TAB ====================

$("#acords-tab").on("click", function(){
  // Primera carga SIN filtrar por año
  // Esto permite que el backend calcule todos los años disponibles
  // El selector se inicializará con el año actual seleccionado
  loadAcords(1, null);

  // Unbind para que no se ejecute múltiples veces
  $("#acords-tab").unbind("click");
});

// ==================== ACTES TAB ====================

$("#actes-tab").on("click", function(){
  $('.spinner-actas-tab').removeClass('d-none');
  $.ajax({
    type: 'GET',
    url: $(location).attr('href') + '/getActesOrgangovern',
    success: function(result){
      data = $.parseJSON(result);
      $.each(data, function(key, value){
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

        $("#actesTbody").append(actaHTML)
      });
      $('.spinner-actas-tab').addClass('d-none');
    },
  })
  $("#actes-tab").unbind("click");
});
