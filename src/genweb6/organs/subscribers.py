from genweb6.core.subscribers import clean_pdf_on_upload
from genweb6.organs.utils import get_settings_property
from genweb6.organs.content.organgovern.organgovern import IOrgangovern
from genweb6.organs.content.sessio.sessio import ISessio
from genweb6.organs.content.acord.acord import IAcord
from genweb6.organs.indicators.updating import (
    update_indicators,
    update_indicators_if_state)


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


def clean_pdf_on_upload_file(obj, event):
    clean_pdf_on_upload(obj, 'visiblefile')
    clean_pdf_on_upload(obj, 'hiddenfile')


def clean_pdf_on_upload_acta(obj, event):
    clean_pdf_on_upload(obj, 'acta')


def clean_pdf_on_upload_annex(obj, event):
    clean_pdf_on_upload(obj, 'file')