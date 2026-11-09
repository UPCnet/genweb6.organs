# -*- coding: utf-8 -*-
"""Tests de la parte local de la firma documental (sin servicios externos).

- Callback de Portafirmes (updateInfoPortafirmes): cambio de estado del acta.
- estatFirmaActa / hasFirmaActa / UtilsFirmaDocumental.
- Permisos locales del acta firmada / no firmada.
- estatFirma de la sesión y warning al modificar contenido firmado.

Lo que decide Portafirmes (firmada/rechazada) se simula llamando al
callback con el payload que enviaría el servicio.
"""
import json
import unittest

from plone import api
from plone.app.testing import logout
from Products.statusmessages.interfaces import IStatusMessage

from genweb6.organs.browser.events.change import estatFirma
from genweb6.organs.firma_documental import hooks
from genweb6.organs.firma_documental import utils as fd_utils
from genweb6.organs.firma_documental.views import firmes
from genweb6.organs.tests.base import OrgansFunctionalTestCase


class FirmaLocalTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(FirmaLocalTestCase, self).setUp()
        self.session = self.create_session('realitzada', title='Sessio Firma')
        self.acta = self.create_acta(self.session)

    def create_acta(self, session, id='acta', id_firma='1001', estat='pendent'):
        acta = api.content.create(
            type='genweb.organs.acta', id=id, title='Acta Test', container=session)
        acta.info_firma = {'unitatDocumental': 'UD1', 'enviatASignar': True}
        acta.id_firma = id_firma
        acta.estat_firma = estat
        acta.reindexObject()
        return acta

    def callback(self, payload, anonymous=True):
        self.request['BODY'] = json.dumps(payload) if not isinstance(payload, str) else payload
        if anonymous:
            logout()
        view = self.portal.restrictedTraverse('@@updateInfoPortafirmes')
        return view()

    # ------------------------------------------------------------------
    # Callback de Portafirmes
    # ------------------------------------------------------------------
    def test_callback_signada_open_organ(self):
        self.callback({'idPeticio': 1001, 'estatPeticio': 'SIGNADA'})
        self.assertEqual(self.acta.estat_firma, 'SIGNADA')
        self.assertEqual(fd_utils.estatFirmaActa(self.acta)['class'], 'signada')

    def test_callback_rebutjada(self):
        self.callback({'idPeticio': 1001, 'estatPeticio': 'REBUTJADA'})
        self.assertEqual(fd_utils.estatFirmaActa(self.acta),
                         {'class': 'rebutjada', 'text': 'Signatura rebutjada'})

    def test_callback_cancelada_is_ignored(self):
        """La cancelación la gestiona la propia aplicación (cancelFirm)."""
        self.callback({'idPeticio': 1001, 'estatPeticio': 'CANCELADA'})
        self.assertEqual(self.acta.estat_firma, 'pendent')

    def test_callback_unknown_id(self):
        self.callback({'idPeticio': 999999, 'estatPeticio': 'SIGNADA'})
        self.assertEqual(self.acta.estat_firma, 'pendent')

    def test_callback_bad_body_does_not_raise(self):
        self.callback('no és json')
        self.callback({})
        self.callback({'idPeticio': 1001})
        self.assertEqual(self.acta.estat_firma, 'pendent')

    def test_callback_only_updates_matching_acta(self):
        session2 = self.create_session('realitzada', id='sessio2')
        acta2 = self.create_acta(session2, id='acta2', id_firma='2002')
        self.callback({'idPeticio': 2002, 'estatPeticio': 'SIGNADA'})
        self.assertEqual(acta2.estat_firma, 'SIGNADA')
        self.assertEqual(self.acta.estat_firma, 'pendent')

    def test_callback_signada_restricted_organ(self):
        """Portafirmes llama al callback sin autenticar; en órganos
        restringidos también debe encontrar el acta y actualizarla."""
        organ = self.create_organ('restricted_to_members_organ', id='restringit')
        session = self.create_session('realitzada', id='s_restr', organ=organ)
        acta = self.create_acta(session, id='acta_r', id_firma='3003')
        self.callback({'idPeticio': 3003, 'estatPeticio': 'SIGNADA'})
        self.assertEqual(acta.estat_firma, 'SIGNADA')

    def test_callback_is_public(self):
        """SEGURIDAD (comportamiento actual): cualquiera, sin autenticar,
        puede cambiar el estado de firma de un acta conociendo idPeticio.
        No hay secreto compartido ni validación del origen."""
        self.callback({'idPeticio': 1001, 'estatPeticio': 'SIGNADA'}, anonymous=True)
        self.assertEqual(self.acta.estat_firma, 'SIGNADA')

    # ------------------------------------------------------------------
    # Estados y flags
    # ------------------------------------------------------------------
    def test_estat_firma_acta_map(self):
        cases = {
            'pendent': 'Enviada i pendent de signatura',
            'PENDENT_SIGNANTS': 'Enviada i pendent de signatura',
            'Signada': 'Desada i signada',
            'cancelada': 'Signatura cancel·lada',
            'altre': 'altre',
        }
        for estat, text in cases.items():
            self.acta.estat_firma = estat
            self.assertEqual(fd_utils.estatFirmaActa(self.acta),
                             {'class': estat.lower(), 'text': text})

    @unittest.expectedFailure
    def test_estat_firma_acta_without_state(self):
        """BUG: sin estat_firma, estatFirmaActa hace `estats_map.get['pendent']`
        (corchetes en vez de paréntesis) -> TypeError."""
        self.acta.estat_firma = None
        self.assertEqual(fd_utils.estatFirmaActa(self.acta)['class'], 'pendent')

    def test_has_firma_acta(self):
        self.assertTrue(fd_utils.hasFirmaActa(self.acta))
        self.acta.info_firma = {'unitatDocumental': 'UD1', 'enviatASignar': False}
        self.assertFalse(fd_utils.hasFirmaActa(self.acta))
        self.acta.info_firma = None
        self.assertFalse(fd_utils.hasFirmaActa(self.acta))

    def test_has_firma_acta_legacy_formats(self):
        self.acta.info_firma = json.dumps({'unitatDocumental': 'UD1', 'enviatASignar': True})
        self.assertTrue(fd_utils.hasFirmaActa(self.acta))
        self.assertIsInstance(self.acta.info_firma, dict)
        self.acta.info_firma = "{'unitatDocumental': 'UD1', 'enviatASignar': True}"
        self.assertTrue(fd_utils.hasFirmaActa(self.acta))

    def test_utils_firma_documental_on_session(self):
        holder = fd_utils.UtilsFirmaDocumental()
        holder.context = self.session
        self.assertFalse(holder.hasFirma())
        self.assertEqual(holder.estatFirma(), 'pendent')
        self.session.info_firma = {'unitatDocumental': 'UD', 'enviatASignar': True}
        self.session.estat_firma = 'SIGNADA'
        self.assertTrue(holder.hasFirma())
        self.assertEqual(holder.estatFirma(), 'signada')

    def test_utils_firma_documental_on_acta(self):
        holder = fd_utils.UtilsFirmaDocumental()
        holder.context = self.acta
        self.assertTrue(holder.hasFirma())
        self.assertEqual(holder.estatFirma()['class'], 'pendent')

    def test_session_estat_firma(self):
        self.assertEqual(estatFirma(self.session)['class'], 'pendent')
        self.acta.estat_firma = 'SIGNADA'
        self.assertEqual(estatFirma(self.session)['class'], 'signada')
        session2 = self.create_session('realitzada', id='sense_firma')
        self.assertIsNone(estatFirma(session2))

    # ------------------------------------------------------------------
    # Permisos locales del acta
    # ------------------------------------------------------------------
    def test_apply_local_permissions_signed(self):
        changed = firmes.apply_acta_firma_local_permissions(self.acta, firmada=True)
        self.assertTrue(changed)
        for attr in firmes._ACTA_LOCAL_PERM_ATTRS:
            self.assertEqual(tuple(getattr(self.acta, attr)), firmes._PERMISOS_ACTA_FIRMADA)
        # Idempotente
        self.assertFalse(firmes.apply_acta_firma_local_permissions(self.acta, firmada=True))

    def test_signed_acta_not_editable_by_secretari(self):
        firmes.apply_acta_firma_local_permissions(self.acta, firmada=True)
        with self.as_user('secretari'):
            self.assertFalse(api.user.has_permission(
                'Modify portal content', obj=self.acta))
        firmes.restore_firma_local_permissions(self.acta)
        for attr in firmes._ACTA_LOCAL_PERM_ATTRS:
            self.assertEqual(tuple(getattr(self.acta, attr)), firmes._PERMISOS_ACTA_NO_FIRMADA)

    # ------------------------------------------------------------------
    # Warning al modificar contenido de una sesión firmada
    # ------------------------------------------------------------------
    def _warnings(self):
        return [m.message for m in IStatusMessage(self.request).show()
                if m.type == 'warning']

    def test_warning_when_session_pending(self):
        IStatusMessage(self.request).show()
        punt = self.create_punt(self.session)
        hooks.warningContentIsSigned(punt, None)
        warnings = self._warnings()
        self.assertTrue(any('enviada a signar' in w for w in warnings), warnings)

    def test_warning_when_session_signed(self):
        self.acta.estat_firma = 'SIGNADA'
        IStatusMessage(self.request).show()
        punt = self.create_punt(self.session)
        hooks.warningContentIsSigned(punt, None)
        self.assertTrue(any('ja signada' in w for w in self._warnings()))

    def test_no_warning_without_firma(self):
        session = self.create_session('realitzada', id='lliure')
        punt = self.create_punt(session)
        IStatusMessage(self.request).show()
        hooks.warningContentIsSigned(punt, None)
        self.assertEqual(self._warnings(), [])
