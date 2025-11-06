from genweb6.core.subscribers import clean_pdf_on_upload
from genweb6.organs.utils import get_settings_property
from genweb6.organs.firma_documental.utils import is_file_uploaded_to_gdoc
from genweb6.organs.indicators.updating import (
    update_indicators,
    update_indicators_if_state)
from genweb6.core.purge import purge_varnish_paths
from genweb6.organs.content.organsfolder.organsfolder import IOrgansfolder
from zope.ramcache import ram

def update_indicators_on_organ_deletion(obj, event):
    update_indicators_if_state(
        obj, ('intranet', 'published'),
        service=get_settings_property('service_id'), indicator='organ-n')


def update_indicators_on_organ_review_state_change(obj, event):
    update_indicators(
        obj, service=get_settings_property('service_id'), indicator='organ-n')


def update_indicators_on_sessio_deletion(obj, event):
    update_indicators_if_state(
        obj, ('convocada',),
        service=get_settings_property('service_id'), indicator='sessio-n')


def update_indicators_on_sessio_review_state_change(obj, event):
    update_indicators(
        obj, service=get_settings_property('service_id'), indicator='sessio-n')


def update_indicators_on_acord_deletion(obj, event):
    update_indicators_if_state(
        obj, ('intranet', 'published'),
        service=get_settings_property('service_id'), indicator='acord-n')


def update_indicators_on_acord_review_state_change(obj, event):
    update_indicators(
        obj, service=get_settings_property('service_id'), indicator='acord-n')


def is_file_in_open_organ(obj):
    return obj.organType == 'open_organ'


def clean_pdf_on_upload_file(obj, event):
    """Limpia PDFs de los campos visiblefile y hiddenfile si no están subidos al gDOC."""
    if is_file_in_open_organ(obj) and not is_file_uploaded_to_gdoc(obj):
        clean_pdf_on_upload(obj, 'visiblefile')
        clean_pdf_on_upload(obj, 'hiddenfile')


def clean_pdf_on_upload_acta(obj, event):
    """Limpia PDF del campo acta si no está subido al gDOC."""
    if is_file_in_open_organ(obj) and not is_file_uploaded_to_gdoc(obj):
        clean_pdf_on_upload(obj, 'acta')


def clean_pdf_on_upload_annex(obj, event):
    """Limpia PDF del campo file si no está subido al gDOC."""
    if is_file_in_open_organ(obj) and not is_file_uploaded_to_gdoc(obj):
        clean_pdf_on_upload(obj, 'file')


def purge_cache_varnish_organs(obj, event):
    """Limpia la caché de varnish recorriendo todos los paths hasta IOrgansfolder."""
    ram.caches.clear()
    
    paths = []
    paths.append('_purge_all')
    # current = obj
    
    # # Recorrer hacia arriba añadiendo paths hasta llegar a IOrgansfolder
    # while current is not None:
    #     # Añadir el path del objeto actual
    #     try:
    #         paths.append(current.absolute_url_path())
    #     except AttributeError:
    #         break
        
    #     # Si hemos llegado a IOrgansfolder, parar
    #     if IOrgansfolder.providedBy(current):
    #         break
        
    #     # Subir al padre
    #     try:
    #         current = current.aq_parent
    #     except AttributeError:
    #         break
    
    purge_varnish_paths(obj, paths)