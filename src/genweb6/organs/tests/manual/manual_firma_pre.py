# -*- coding: utf-8 -*-
"""Bateria de firma documental contra els serveis REALS de PRE.

Bateria APART: el `bin/test` normal no la descobreix (viu a tests/manual/ i el
fitxer no comença per "test"). Només es llança manualment:

    bin/test -s genweb6.organs --tests-pattern='^manual$' --test-file-pattern='^manual_'

Cal tests/manual/manual_settings.env (no versionat). Veure manual_settings.env.example.

ClientFirma contra gDOC, codi expedient, Signatura CSV, Portafirmes i
Còpies Autèntiques de PRE. No es toca cap lloc Plone de PRE.

No es comprova el resultat final de la firma (signada/rebutjada): ho
resol Portafirmes de forma asíncrona. Només que la petició s'envia i es
pot cancel·lar. Tot el que es crea es neteja amb addCleanup.
"""
from unittest import mock

import datetime
import logging
import os
import unittest

from genweb6.organs.firma_documental import webservices
from genweb6.organs.firma_documental.webservices import ClientFirma
from genweb6.organs.tests.manual.config import CONFIG
from genweb6.organs.tests.manual.config import firma_settings
from genweb6.organs.tests.manual.config import require
from genweb6.organs.tests.manual.config import SKIP_REASON


logger = logging.getLogger('genweb6.organs.tests.manual')

TEST_PDF = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'testfile.pdf')
SERVICE_KEYS = ('GDOC_URL', 'GDOC_USER', 'GDOC_HASH', 'GDOC_FONS_ID',
                'CODIEXPEDIENT_URL', 'CODIEXPEDIENT_APIKEY', 'GDOC_SERIE_TEST',
                'GDOC_AUTHOR_TEST')
PORTAFIRMES_KEYS = ('PORTAFIRMES_URL', 'PORTAFIRMES_APIKEY', 'PRE_SIGNANT')


def _pdf():
    with open(TEST_PDF, 'rb') as f:
        return f.read()


def _safe_cleanup(func, *args):
    """Les neteges no han de tapar l'error original del test."""
    def _run():
        try:
            func(*args)
        except Exception as exc:  # noqa
            logger.warning('Neteja PRE fallida %s%r: %s', func.__name__, args, exc)
    return _run


@unittest.skipUnless(require(*SERVICE_KEYS), SKIP_REASON)
class FirmaServeisPreTestCase(unittest.TestCase):
    """Nivell B: flux gDOC complet amb neteja."""

    def setUp(self):
        self.client = ClientFirma(settings=firma_settings(), timeout=30)
        self.serie = CONFIG['GDOC_SERIE_TEST']

    def create_expedient(self):
        codi = self.client.getCodiExpedient(self.serie)
        self.assertIn('codi', codi)
        expedient = datetime.datetime.now().strftime('%Y') + '-' + codi['codi']
        titol = 'TEST AUTOMATIC genweb6.organs {0}'.format(
            datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        exp = self.client.createSerieDocumental(self.serie, expedient, titol)
        self.assertIn('idElementCreat', exp)
        unitat = str(exp['idElementCreat'])
        self.addCleanup(_safe_cleanup(self.client.deleteSerieDocumental, unitat))
        return unitat

    def upload_pdf(self, unitat, name='test_organs.pdf', is_acta=False):
        fitxer = {'fitxer': [name, _pdf(), 'application/pdf']}
        # A producció l'autor és organ.author (camp de l'òrgan)
        content = self.client.uploadFitxerGDoc(
            CONFIG['GDOC_AUTHOR_TEST'], unitat, fitxer, is_acta=is_acta)
        self.assertIn('idElementCreat', content)
        info = self.client.getInfoElement(content['idElementCreat'])
        uuid = info['documentElectronic']['uuid']
        self.assertTrue(uuid)
        return content['idElementCreat'], uuid

    def test_codi_expedient(self):
        codi = self.client.getCodiExpedient(self.serie)
        self.assertTrue(codi.get('codi'))

    def test_gdoc_upload_and_info(self):
        unitat = self.create_expedient()
        self.upload_pdf(unitat)

    def test_gdoc_upload_acta_type(self):
        unitat = self.create_expedient()
        self.upload_pdf(unitat, name='acta_test.pdf', is_acta=True)

    @unittest.skipUnless(require('SIGNATURACSV_URL', 'SIGNATURACSV_APIKEY'),
                         'Falta configuració de Signatura CSV')
    def test_timbrar_document(self):
        unitat = self.create_expedient()
        id_element, uuid = self.upload_pdf(unitat)
        res = self.client.timbrarDocumentGdoc(id_element)
        self.assertIn('idDocument', res)

    @unittest.skipUnless(require(*PORTAFIRMES_KEYS), 'Falta configuració de Portafirmes')
    def test_portafirmes_send_and_cancel(self):
        """Envia una petició de firma de l'acta i la cancel·la.
        El signant (PRE_SIGNANT) pot rebre una notificació de PRE."""
        unitat = self.create_expedient()
        _, acta_uuid = self.upload_pdf(unitat, name='acta_test.pdf', is_acta=True)

        # callbackUrl apunta a una URL no vàlida: no volem que Portafirmes
        # cridi cap lloc real (la petició es cancel·la tot seguit).
        portal = mock.Mock()
        portal.absolute_url.return_value = 'https://invalid.example.com'
        with mock.patch.object(webservices.api.portal, 'get', return_value=portal):
            content = self.client.uploadActaPortafirmes(
                'TEST AUTOMATIC', acta_uuid, [], [CONFIG['PRE_SIGNANT']])
        self.assertIn('idPeticio', content)
        id_peticio = content['idPeticio']

        res = self.client.cancelPeticioPortafirmes(id_peticio)
        self.assertLess(res.status_code, 400)

    @unittest.skipUnless(require('COPIESAUTENTIQUES_URL', 'COPIESAUTENTIQUES_APIKEY'),
                         'Falta configuració de Còpies Autèntiques')
    def test_invalida_copia_autentica(self):
        unitat = self.create_expedient()
        _, uuid = self.upload_pdf(unitat)
        result = self.client.invalidaCopiaAutentica(id_document=uuid)
        self.assertIsNotNone(result)
