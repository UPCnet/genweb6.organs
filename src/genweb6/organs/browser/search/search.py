from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.PloneBatch import Batch
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.utils import safe_unicode
from Products.PythonScripts.standard import url_quote_plus
from Products.ZCTextIndex.ParseTree import ParseError
from ZTUtils import make_query

from plone import api
from plone.app.contentlisting.interfaces import IContentListing
from plone.memoize import instance
from operator import itemgetter
from zope.component import getMultiAdapter
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface
from zope.publisher.browser import BrowserView
from Products.Five.browser import BrowserView

from genweb6.core.utils import pref_lang
from genweb6.organs import permissions
from genweb6.organs.interfaces import IGenweb6OrgansLayer
from genweb6.organs import utils

import json
import pkg_resources
# import time
# start_time = time.time()
# print("--- %s seconds --- " % (time.time() - start_time))

PLMF = MessageFactory('plonelocales')
_ = MessageFactory('plone')

# Tamaño de página para la búsqueda (paginación)
SEARCH_PAGE_SIZE = 15

# We should accept both a simple space, unicode '\u0020' but also a
# multi-space, so called 'waji-kankaku', unicode '\u3000'
MULTISPACE = '\u3000'
EVER = DateTime('1970/01/03')


def quote_chars(s):
    # We need to quote parentheses when searching text indices
    if '(' in s:
        s = s.replace('(', '"("')
    if ')' in s:
        s = s.replace(')', '")"')
    if MULTISPACE in s:
        s = s.replace(MULTISPACE, ' ')
    return s


class _SearchBatch(object):
    """Objeto tipo batch para la paginación del buscador (15 por página)."""

    max_visible_pages = 5  # como organgovern renderPagination

    def __init__(self, results, total, b_start, b_size):
        self.results = results
        self.total = total
        self.b_start = b_start
        self.b_size = b_size
        self.total_pages = max(1, (total + b_size - 1) // b_size) if total else 1
        self.current_page = (b_start // b_size) + 1 if b_size else 1
        self.first_item = b_start + 1 if results else 0
        self.last_item = min(b_start + len(results), total) if results else 0
        self.previous_start = b_start - b_size if b_start > 0 else None
        self.next_start = b_start + b_size if (b_start + b_size) < total else None
        self.has_previous = self.previous_start is not None
        self.has_next = self.next_start is not None

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)

    def get_page_numbers(self):
        """Lista de ítems para la barra de paginación (como organgovern).

        Cada ítem es {'type': 'page', 'page': n, 'b_start': start} o
        {'type': 'ellipsis'}.
        """
        total_pages = self.total_pages
        current = self.current_page
        if total_pages <= 0:
            return []
        max_visible = self.max_visible_pages
        start_page = max(1, current - max_visible // 2)
        end_page = min(total_pages, start_page + max_visible - 1)
        if end_page - start_page < max_visible - 1:
            start_page = max(1, end_page - max_visible + 1)
        items = []
        if start_page > 1:
            items.append({'type': 'page', 'page': 1, 'b_start': 0})
            if start_page > 2:
                items.append({'type': 'ellipsis'})
        for i in range(start_page, end_page + 1):
            items.append({
                'type': 'page',
                'page': i,
                'b_start': (i - 1) * self.b_size,
            })
        if end_page < total_pages:
            if end_page < total_pages - 1:
                items.append({'type': 'ellipsis'})
            items.append({
                'type': 'page',
                'page': total_pages,
                'b_start': (total_pages - 1) * self.b_size,
            })
        return items


class Search(BrowserView):
    """
    Vista de búsqueda para órganos, sesiones y acuerdos.
    Compatible con Plone 6 y el nuevo template search.pt (Bootstrap 5).
    """

    @instance.memoize
    def getOwnOrgans(self):
        """Get organs linked to current user.

        OPTIMIZATION: Usa metadata del catálogo y minimiza getObject() calls.
        Solo necesitamos getObject() para obtener eventsColor.
        """
        if api.user.is_anonymous():
            return []

        portal_catalog = api.portal.get_tool(name='portal_catalog')
        root_path = '/'.join(api.portal.get().getPhysicalPath())
        lang = api.portal.get_tool('portal_languages').getDefaultLanguage()
        username = api.user.get_current().id

        # Buscar todos los órganos
        values = portal_catalog.searchResults(
            portal_type=['genweb.organs.organgovern'],
            path=f'{root_path}/{lang}',
            sort_on='sortable_title'
        )

        results = []
        for obj in values:
            # NOTE: No se puede optimizar más - api.user.get_roles() necesita
            # el objeto real para leer roles locales (no están en metadata)
            organ = obj._unrestrictedGetObject()

            all_roles = api.user.get_roles(username=username, obj=organ)
            organ_roles = [r for r in all_roles if r in [
                'OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                'OG4-Afectat', 'OG5-Convidat']]

            if organ_roles:
                results.append(dict(
                    url=obj.getURL(),  # ← Metadata del brain
                    title=obj.Title,   # ← Metadata del brain
                    color=getattr(organ, 'eventsColor', '#007bc0') or '#007bc0',
                    role=organ_roles))

        return results

    def getLatestCDG(self):
        return self._getLatestSession(
            'consell-de-govern/consell-de-govern', 'Consell de Govern')

    def getLatestCS(self):
        return self._getLatestSession('cs/ple-del-consell-social', 'Consell Social')

    def getLatestCU(self):
        return self._getLatestSession(
            'claustre-universitari/claustre-universitari', 'Claustre Universitari')

    def _getLatestSession(self, rel_path, label):
        """OPTIMIZATION: Usa metadata del catálogo para evitar getObject().

        Filtra sesiones públicas (excluyendo 'planificada') y obtiene
        la más reciente usando solo metadata del catálogo.
        """
        root_path = '/'.join(api.portal.get().getPhysicalPath())
        lang = api.portal.get_tool('portal_languages').getDefaultLanguage()
        portal_catalog = api.portal.get_tool(name='portal_catalog')

        # Filtrar por review_state directamente en el catálogo
        # para evitar get_state()
        # Excluir 'planificada' usando una búsqueda más eficiente
        items = portal_catalog.searchResults(
            portal_type=['genweb.organs.sessio'],
            path=f'{root_path}/{lang}/{rel_path}',
            review_state=[
                'convocada', 'realitzada', 'en_correccio', 'tancada'],
            sort_on='start',  # OPTIMIZATION: Ordenar por fecha de inicio
            sort_order='reverse',
            sort_limit=1)  # OPTIMIZATION: Solo necesitamos 1

        # OPTIMIZATION: Sin getObject(), usar solo metadata del catálogo
        if items:
            item = items[0]
            return dict(
                title=item.Title,        # ← Metadata
                url=item.getURL())       # ← Metadata

        return None

    def results(self, query=None, batch=True, b_size=None, b_start=None, old=False):
        if query is None:
            query = {}
        # Si no hay parámetros de búsqueda no devolvemos nada
        if not self.request.form and not query:
            return []

        # Paginación: 15 por página, b_start desde la request
        if b_size is None:
            b_size = SEARCH_PAGE_SIZE
        if b_start is None:
            b_start = int(self.request.get('b_start', 0))
        if batch:
            query['b_start'] = b_start
            query['b_size'] = b_size

        # Construcción del query final
        query = self.filter_query(query)
        if not query or query.get('path') == '/empty_path/':
            return []

        # Orden descendente por defecto
        query.setdefault('sort_order', 'reverse')

        catalog = api.portal.get_tool(name='portal_catalog')
        return catalog(**query)

    def get_search_batch(self):
        """Devuelve un objeto tipo batch con la página actual y datos de paginación.

        Así la búsqueda solo carga 15 resultados por página y podemos mostrar
        controles anterior/siguiente y total.
        """
        b_start = int(self.request.get('b_start', 0))
        b_size = SEARCH_PAGE_SIZE

        base_query = self.filter_query({})
        if not base_query or base_query.get('path') == '/empty_path/':
            return _SearchBatch([], 0, 0, b_size)

        base_query.setdefault('sort_order', 'reverse')
        catalog = api.portal.get_tool(name='portal_catalog')

        # Total de resultados (solo cuenta, sin cargar todos los brains)
        count_query = dict(base_query)
        count_query.pop('b_start', None)
        count_query.pop('b_size', None)
        total = len(catalog(**count_query))

        # Solo la página actual
        page_query = dict(base_query)
        page_query['b_start'] = b_start
        page_query['b_size'] = b_size
        page_results = list(catalog(**page_query))

        return _SearchBatch(page_results, total, b_start, b_size)

    def base_search_url(self):
        absolute_url = api.portal.get().absolute_url()
        lang = api.portal.get_tool('portal_languages').getDefaultLanguage()
        return f'{absolute_url}/{lang}/@@search'

    def page_url(self, b_start):
        """URL para un número de página manteniendo el resto de parámetros del formulario."""
        form = dict(self.request.form)
        form['b_start'] = b_start
        base = self.base_search_url()
        return f'{base}?{make_query(form)}'

    def filter_query(self, query):
        # Solo filtra si hay texto o algún filtro
        request = self.request
        catalog = api.portal.get_tool(name='portal_catalog')
        valid_indexes = tuple(catalog.indexes())
        valid_keys = ('sort_on', 'sort_order', 'sort_limit',
                      'fq', 'fl', 'facet') + valid_indexes
        text = query.get('SearchableText', None)
        if text is None:
            text = request.form.get('SearchableText', '')
        if not text and not any(k in request.form
                                for k in ['portal_type', 'organ', 'period']):
            return {}
        # Construye el query
        for k, v in request.form.items():
            if v and ((k in valid_keys) or k.startswith('facet.')):
                query[k] = v
        if text:
            query['SearchableText'] = text + '*'
        # Tipos
        types = query.get('portal_type', [])
        if isinstance(types, str):
            types = [types]
        query['portal_type'] = types or ['genweb.organs.acord', 'genweb.organs.punt']
        # Path por defecto
        if 'path' not in query:
            root_path = '/'.join(api.portal.get().getPhysicalPath())
            lang = api.portal.get_tool('portal_languages').getDefaultLanguage()
            query['path'] = [
                f'{root_path}/{lang}/consell-de-govern/consell-de-govern/',
                f'{root_path}/{lang}/cs/ple-del-consell-social/',
                f'{root_path}/{lang}/claustre-universitari/claustre-universitari/'
            ]
        return query

    def filter_types(self, types):
        plone_utils = getToolByName(self.context, 'plone_utils')
        if not isinstance(types, list):
            types = [types]
        return plone_utils.getUserFriendlyTypes(types)

    def sort_options(self):
        """ Sorting options for search results view. """
        return (
            SortOption(
                self.request, _(u'date (newest first)'),
                'Date', reverse=True
            ),
            SortOption(self.request, _(u'alphabetically'), 'sortable_title'),
        )

    def breadcrumbs(self, item):
        obj = item.getObject()
        view = getMultiAdapter((obj, self.request), name='breadcrumbs_view')
        breadcrumbs = list(view.breadcrumbs())[:-1]  # quita el propio objeto
        # Si hay más de un elemento, elimina el primero (la raíz)
        if len(breadcrumbs) > 1:
            breadcrumbs = breadcrumbs[1:]
        # Si tras el corte queda vacío, devuelve al menos el padre inmediato o la raíz
        if not breadcrumbs:
            parent = getattr(obj, 'aq_parent', None)
            if parent and hasattr(parent, 'absolute_url') and hasattr(parent, 'Title'):
                return [{'absolute_url': parent.absolute_url(), 'Title': parent.Title()}]
            navroot = self.navroot_url()
            return [{'absolute_url': navroot, 'Title': 'Inici'}]
        # Si hay muchos, acorta como antes
        if len(breadcrumbs) > 3:
            empty = {'absolute_url': '', 'Title': '…'}
            breadcrumbs = [breadcrumbs[0], empty] + breadcrumbs[-2:]
        return breadcrumbs

    def navroot_url(self):
        if not hasattr(self, '_navroot_url'):
            state = self.context.unrestrictedTraverse('@@plone_portal_state')
            self._navroot_url = state.navigation_root_url()
        return self._navroot_url

    def root_path(self):
        path = '/'.join(api.portal.get().getPhysicalPath())
        return path

    @instance.memoize
    def getPeriodData(self):
        """OPTIMIZATION: Pre-calcular datos de periodo para evitar python: en template.

        Returns:
            dict: Contiene 'ever', 'lastyear', 'checked' para filtros de fecha
        """
        ever = '1970-01-02'
        today = DateTime().earliestTime()
        lastyear = (today - 365).Date()

        checked = self.request.get('created', [])
        if len(checked) == 1:
            checked = checked[0]
        else:
            checked = ever

        return {
            'ever': ever,
            'lastyear': lastyear,
            'checked': checked,
            'is_ever_checked': checked == ever,
            'is_lastyear_checked': checked == lastyear,
        }


class SortOption(object):

    def __init__(self, request, title, sortkey='', reverse=False):
        self.request = request
        self.title = title
        self.sortkey = sortkey
        self.reverse = reverse

    def selected(self):
        sort_on = self.request.get('sort_on', '')
        return sort_on == self.sortkey

    def url(self):
        q = {}
        q.update(self.request.form)
        if 'sort_on' in q.keys():
            del q['sort_on']
        if 'sort_order' in q.keys():
            del q['sort_order']
        q['sort_on'] = self.sortkey
        if self.reverse:
            q['sort_order'] = 'reverse'

        base_url = self.request.URL
        # After the AJAX call the request is changed and thus the URL part of
        # it as well. In this case we need to tweak the URL to point to have
        # correct URLs
        if '@@updated_search' in base_url:
            base_url = base_url.replace('@@updated_search', '@@search')
        return base_url + '?' + make_query(q)


# Hide show more
class TypeAheadSearch(BrowserView):
    def __call__(self):
        return self.render()

    def render(self):
        # We set the parameters sent in livesearch using the old way.
        q = self.request['q']

        limit = 10
        path = None
        ploneUtils = getToolByName(self.context, 'plone_utils')
        portal_url = getToolByName(self.context, 'portal_url')()
        pretty_title_or_id = ploneUtils.pretty_title_or_id
        portalProperties = getToolByName(self.context, 'portal_properties')
        siteProperties = getattr(portalProperties, 'site_properties', None)
        useViewAction = []
        if siteProperties is not None:
            useViewAction = siteProperties.getProperty(
                'typesUseViewActionInListings', [])

        # SIMPLE CONFIGURATION
        MAX_TITLE = 40
        MAX_DESCRIPTION = 80

        # generate a result set for the query
        catalog = self.context.portal_catalog

        friendly_types = ploneUtils.getUserFriendlyTypes()

        def quotestring(s):
            return '"%s"' % s

        def quote_bad_chars(s):
            bad_chars = ["(", ")"]
            for char in bad_chars:
                s = s.replace(char, quotestring(char))
            return s

        multispace = '\u3000'
        for char in ('?', '-', '+', '*', multispace):
            q = q.replace(char, ' ')
        r = q.split()
        r = " AND ".join(r)
        r = quote_bad_chars(r) + '*'
        searchterms = url_quote_plus(r)

        params = {'SearchableText': r,
                  'portal_type': friendly_types,
                  'sort_limit': limit + 1}

        if path is None:
            # useful for subsides
            params['path'] = getNavigationRoot(self.context)
        else:
            params['path'] = path

        params["Language"] = pref_lang()
        # search limit+1 results to know if limit is exceeded
        results = catalog(**params)

        REQUEST = self.context.REQUEST
        RESPONSE = REQUEST.RESPONSE
        RESPONSE.setHeader('Content-Type', 'application/json')

        label_show_all = _('label_show_all', default='Show all items')

        ts = getToolByName(self.context, 'translation_service')

        queryElements = []

        if results:
            # TODO: We have to build a JSON with the desired parameters.
            for result in results[:limit]:
                # Calculate icon replacing '.' per '-' as '.' in portal_types break CSS
                icon = result.portal_type.lower().replace(".", "-")
                itemUrl = result.getURL()
                if result.portal_type in useViewAction:
                    itemUrl += '/view'

                full_title = safe_unicode(pretty_title_or_id(result))
                if len(full_title) > MAX_TITLE:
                    display_title = ''.join((full_title[:MAX_TITLE], '...'))
                else:
                    display_title = full_title

                full_title = full_title.replace('"', '&quot;')

                display_description = safe_unicode(result.Description)
                if len(display_description) > MAX_DESCRIPTION:
                    display_description = ''.join(
                        (display_description[:MAX_DESCRIPTION], '...'))

                # We build the dictionary element with the desired parameters and we add it to the queryElements array.
                queryElement = {
                    'class': '',
                    'title': display_title,
                    'description': display_description,
                    'itemUrl': itemUrl,
                    'icon': icon}
                queryElements.append(queryElement)

        return json.dumps(queryElements)
