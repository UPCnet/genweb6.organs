# -*- coding: utf-8 -*-
"""Tests unitarios del cliente de firma documental (sin red).

Se simula `requests.request` para comprobar URLs, métodos, cabeceras,
payloads y la traducción de errores a ClientFirmaException.
Las pruebas contra los servicios reales de PRE van en tests/manual/ (opt-in).
"""
from types import SimpleNamespace
from unittest import mock

import json
import unittest

from requests.exceptions import ConnectionError
from requests.exceptions import ConnectTimeout
from requests.exceptions import HTTPError
from requests.exceptions import ReadTimeout

from genweb6.organs.firma_documental import webservices
from genweb6.organs.firma_documental.webservices import ClientFirma
from genweb6.organs.firma_documental.webservices import ClientFirmaException


SETTINGS = SimpleNamespace(
    gdoc_url='https://gdoc.test',
    gdoc_user='usr',
    gdoc_hash='HASH',
    gdoc_fons_id='FONS',
    codiexpedient_url='https://codi.test',
    codiexpedient_apikey='KEY-CODI',
    portafirmes_url='https://pf.test/peticions',
    portafirmes_apikey='KEY-PF',
    copiesautentiques_url='https://ca.test',
    copiesautentiques_apikey='KEY-CA',
    signaturacsv_url='https://csv.test',
    signaturacsv_apikey='KEY-CSV',
)


def fake_response(payload=None, status=200, content=None):
    res = mock.Mock()
    res.status_code = status
    res.content = content if content is not None else json.dumps(payload or {}).encode()
    if status >= 400:
        res.raise_for_status.side_effect = HTTPError('{0} Error'.format(status))
    else:
        res.raise_for_status.return_value = None
    return res


class ClientFirmaTestCase(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch.object(webservices.requests, 'request')
        self.request = patcher.start()
        self.addCleanup(patcher.stop)
        self.request.return_value = fake_response({'ok': True})
        self.client = ClientFirma(settings=SETTINGS, timeout=15)

    def last_call(self):
        args, kwargs = self.request.call_args
        return args[0], args[1], kwargs

    # ------------------------------------------------------------------
    # URLs y payloads
    # ------------------------------------------------------------------
    def test_get_codi_expedient(self):
        self.request.return_value = fake_response({'codi': 'EXP-1'})
        self.assertEqual(self.client.getCodiExpedient('SERIE1'), {'codi': 'EXP-1'})
        method, url, kw = self.last_call()
        self.assertEqual(method, 'GET')
        self.assertEqual(url, 'https://codi.test/api/codi?serie=SERIE1')
        self.assertEqual(kw['headers'], {'X-Api-Key': 'KEY-CODI'})
        self.assertEqual(kw['timeout'], 15)

    def test_create_serie_documental(self):
        self.client.createSerieDocumental('S1', 'EXP-1', 'Titol')
        method, url, kw = self.last_call()
        self.assertEqual(method, 'POST')
        self.assertEqual(
            url, 'https://gdoc.test/api/serie/S1/udch?uid=usr&fonsId=FONS&hash=HASH')
        self.assertEqual(kw['json'], {'expedient': 'EXP-1', 'titolPropi': 'Titol'})

    def test_delete_serie_documental(self):
        self.client.deleteSerieDocumental('UD1')
        method, url, kw = self.last_call()
        self.assertEqual(method, 'DELETE')
        self.assertEqual(
            url, 'https://gdoc.test/api/udch/UD1/esborrar?fonsId=FONS&hash=HASH')

    def test_get_info_element(self):
        self.client.getInfoElement(123)
        method, url, kw = self.last_call()
        self.assertEqual(method, 'GET')
        self.assertEqual(
            url, 'https://gdoc.test/api/doce/123/consulta?fonsId=FONS&hash=HASH')

    def test_upload_fitxer_gdoc_document(self):
        fitxer = {'fitxer': ['Acta àèí "final".pdf', b'%PDF', 'application/pdf']}
        self.client.uploadFitxerGDoc('autor1', 'EXP-9', fitxer)
        method, url, kw = self.last_call()
        self.assertEqual(method, 'POST')
        self.assertEqual(
            url, 'https://gdoc.test/api/pare/EXP-9/doce?uid=usr&fonsId=FONS&hash=HASH')
        self.assertEqual(kw['timeout'], 60)
        self.assertEqual(kw['data']['tipusDocumental'], '906340')
        self.assertEqual(kw['data']['autors'], "[{'id': autor1}]")
        # Nombre sin acentos ni comillas dobles
        self.assertEqual(kw['files']['fitxer'][0], "Acta aei 'final'.pdf")

    def test_upload_fitxer_gdoc_acta_type(self):
        self.client.uploadFitxerGDoc('a', 'E', {'fitxer': ['a.pdf', b'', 'application/pdf']},
                                     is_acta=True)
        self.assertEqual(self.last_call()[2]['data']['tipusDocumental'], '452')

    def test_upload_fitxer_gdoc_truncates_long_name(self):
        name = 'x' * 300 + '.pdf'
        self.client.uploadFitxerGDoc('a', 'E', {'fitxer': [name, b'', 'application/pdf']})
        sent = self.last_call()[2]['files']['fitxer'][0]
        self.assertEqual(len(sent), 199)
        self.assertTrue(sent.endswith('...'))

    def test_upload_fitxer_gdoc_from_namedfile(self):
        blob = mock.Mock(filename='doc.pdf', contentType='application/pdf')
        blob.open.return_value.read.return_value = b'%PDF-1.4'
        self.client.uploadFitxerGDoc('a', 'E', blob)
        self.assertEqual(self.last_call()[2]['files']['fitxer'],
                         ['doc.pdf', b'%PDF-1.4', 'application/pdf'])

    def test_upload_acta_portafirmes(self):
        portal = mock.Mock()
        portal.absolute_url.return_value = 'https://govern.test'
        with mock.patch.object(webservices.api.portal, 'get', return_value=portal):
            self.client.uploadActaPortafirmes(
                'Acta 1', 'UUID-1', [{'codi': 'ANX'}], ['signant1', 'signant2'])
        method, url, kw = self.last_call()
        self.assertEqual(method, 'POST')
        self.assertEqual(url, 'https://pf.test/peticions')
        self.assertEqual(kw['headers'], {'X-Api-Key': 'KEY-PF'})
        body = kw['json']
        self.assertEqual(body['documents'][0]['codi'], 'UUID-1')
        self.assertEqual(body['documentsAnnexos'], [{'codi': 'ANX'}])
        self.assertEqual(
            [p['signants'][0]['commonName'] for p in body['passosPeticio']],
            ['signant1', 'signant2'])
        self.assertEqual(body['callbackUrl'], 'https://govern.test/updateInfoPortafirmes')
        self.assertIn('Acta 1', body['descripcioPeticio'])

    def test_timbrar_document(self):
        self.client.timbrarDocumentGdoc('DOC1')
        method, url, kw = self.last_call()
        self.assertEqual(url, 'https://csv.test/api/timbrarDocumentGdc')
        self.assertEqual(kw['headers'], {'X-Api-Key': 'KEY-CSV'})
        self.assertEqual(kw['json'],
                         {'idDocument': 'DOC1', 'afegirTimbrat': False, 'idioma': 'CATALA'})

    def test_cancel_peticio_portafirmes(self):
        res = self.client.cancelPeticioPortafirmes(77)
        method, url, kw = self.last_call()
        self.assertEqual(method, 'DELETE')
        self.assertEqual(url, 'https://pf.test/peticions/77')
        self.assertEqual(kw['headers'], {'X-Api-Key': 'KEY-PF'})
        # Devuelve la respuesta cruda, no JSON
        self.assertIs(res, self.request.return_value)

    def test_invalida_copia_autentica(self):
        self.client.invalidaCopiaAutentica('UUID-9')
        method, url, kw = self.last_call()
        self.assertEqual(method, 'POST')
        self.assertEqual(url, 'https://ca.test/api/invalida?idDocument=UUID-9')
        self.assertEqual(kw['headers']['X-Api-Key'], 'KEY-CA')

    def test_invalida_copia_autentica_without_id(self):
        self.client.invalidaCopiaAutentica()
        self.assertEqual(self.last_call()[1], 'https://ca.test/api/invalida')

    # ------------------------------------------------------------------
    # Errores
    # ------------------------------------------------------------------
    def test_timeout_raises_client_exception(self):
        for exc in (ConnectTimeout, ReadTimeout):
            self.request.side_effect = exc('t')
            with self.assertRaises(ClientFirmaException) as cm:
                self.client.getInfoElement(1)
            self.assertTrue(cm.exception.timeout)
            self.assertIn('Request timeout', str(cm.exception))

    def test_connection_error_raises_client_exception(self):
        self.request.side_effect = ConnectionError('refused')
        with self.assertRaises(ClientFirmaException) as cm:
            self.client.getInfoElement(1)
        self.assertFalse(cm.exception.timeout)
        self.assertIn('refused', cm.exception.message)

    def test_http_error_json_body(self):
        self.request.return_value = fake_response({'error': 'no existeix'}, status=404)
        with self.assertRaises(ClientFirmaException) as cm:
            self.client.getInfoElement(1)
        self.assertEqual(cm.exception.status, 404)
        self.assertEqual(cm.exception.response, {'error': 'no existeix'})
        self.assertIn('[404]', str(cm.exception))

    def test_http_error_non_json_body(self):
        """Un error con cuerpo no JSON (p. ej. página HTML de un proxy 502)
        debe llegar como ClientFirmaException, no como JSONDecodeError."""
        self.request.return_value = fake_response(status=502, content=b'<html>Bad Gateway</html>')
        with self.assertRaises(ClientFirmaException) as cm:
            self.client.getInfoElement(1)
        self.assertEqual(cm.exception.status, 502)
        self.assertIsNone(cm.exception.response)
        self.assertIn('Bad Gateway', str(cm.exception))

    def test_http_error_empty_body(self):
        self.request.return_value = fake_response(status=504, content=b'')
        with self.assertRaises(ClientFirmaException) as cm:
            self.client.timbrarDocumentGdoc('ID')
        self.assertEqual(cm.exception.status, 504)

    def test_success_non_json_body(self):
        """Un 200 con cuerpo vacío o HTML no debe dar 'Expecting value'."""
        for content in (b'', b'<html>ok</html>'):
            self.request.return_value = fake_response(status=200, content=content)
            with self.assertRaises(ClientFirmaException):
                self.client.timbrarDocumentGdoc('ID')

    # ------------------------------------------------------------------
    # uploadFileGdoc (helper de alto nivel)
    # ------------------------------------------------------------------
    def test_upload_file_gdoc_returns_ids(self):
        self.request.side_effect = [
            fake_response({'idElementCreat': 555}),
            fake_response({'documentElectronic': {'uuid': 'U-555'}}),
        ]
        with mock.patch.object(webservices, 'get_settings_firma_documental',
                               return_value=SETTINGS):
            result = webservices.uploadFileGdoc(
                'autor', 'EXP', {'fitxer': ['a.pdf', b'', 'application/pdf']})
        self.assertEqual(result, {'id': '555', 'uuid': 'U-555',
                                  'filename': 'a.pdf', 'contentType': 'application/pdf'})
        self.assertEqual(self.request.call_count, 2)
        self.assertIn('/api/doce/555/consulta', self.request.call_args_list[1][0][1])

    def test_upload_file_gdoc_propagates_errors(self):
        self.request.side_effect = ConnectionError('down')
        with mock.patch.object(webservices, 'get_settings_firma_documental',
                               return_value=SETTINGS):
            with self.assertRaises(ClientFirmaException):
                webservices.uploadFileGdoc(
                    'autor', 'EXP', {'fitxer': ['a.pdf', b'', 'application/pdf']})
