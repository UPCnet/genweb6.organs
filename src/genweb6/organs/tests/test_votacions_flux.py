# -*- coding: utf-8 -*-
"""Tests funcionales del flujo de votaciones (acuerdos y esmenas).

Complementa test_votaciones.py (permisos de UI) probando:
- Ciclo de vida: abrir, cerrar, reabrir, anular.
- Registro de votos de varios usuarios, en acuerdo y en esmena.
- Correo de confirmación de voto y de anulación (MockMailHost).
- Recuentos de reloadVoteStats.
- Permisos reales de las vistas.
- Persistencia de los votos en la ZODB.

Decisiones de negocio (docs/PLAN_TESTS.md §7):
- Se pueden tener varias votaciones abiertas a la vez.
- No se puede votar en una votación cerrada.
- Quórum y votación son independientes.
"""
import json
import re
import unittest

import transaction
from AccessControl import Unauthorized

from genweb6.organs.tests.base import as_dict
from genweb6.organs.tests.base import ORGAN_FROM_MAIL
from genweb6.organs.tests.base import OrgansFunctionalTestCase


DATE_RE = re.compile(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$')


def _json(result):
    if isinstance(result, (bytes, str)):
        return json.loads(result)
    return result


class VotacionsFluxTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(VotacionsFluxTestCase, self).setUp()
        self.session = self.create_session('realitzada', title='Sessio Votacions')
        self.acord = self.create_acord(self.session, title='Acord Pressupost')
        self.reset_mails()

    def open_vote(self, context=None):
        self.call_view(context or self.acord, 'openPublicVote')

    def vote(self, user_id, vote_view, context=None):
        with self.as_user(user_id):
            return _json(self.call_view(context or self.acord, vote_view))

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def test_open_public_vote(self):
        self.open_vote()
        self.assertEqual(self.acord.estatVotacio, 'open')
        self.assertEqual(self.acord.tipusVotacio, 'public')
        self.assertRegex(self.acord.horaIniciVotacio, DATE_RE)

    def test_close_vote(self):
        self.open_vote()
        self.call_view(self.acord, 'closeVote')
        self.assertEqual(self.acord.estatVotacio, 'close')
        self.assertRegex(self.acord.horaFiVotacio, DATE_RE)

    def test_reopen_closed_vote(self):
        self.open_vote()
        self.call_view(self.acord, 'closeVote')
        result = _json(self.call_view(self.acord, 'reopenVote'))
        self.assertEqual(result['status'], 'success')
        self.assertEqual(self.acord.estatVotacio, 'open')

    def test_reopen_blocked_when_esmena_open(self):
        """Comportamiento ACTUAL: reopenVote rechaza reabrir si hay otra
        votación abierta en el mismo acuerdo. Pendiente de confirmar si es
        intencionado (ver PLAN_TESTS.md §7)."""
        self.open_vote()
        self.call_view(self.acord, 'closeVote')
        self.create_esmena(self.acord, estat='open')
        result = _json(self.call_view(self.acord, 'reopenVote'))
        self.assertEqual(result['status'], 'error')
        self.assertEqual(self.acord.estatVotacio, 'close')

    def test_open_other_public_vote_creates_esmena(self):
        self.open_vote()
        self.call_view(self.acord, 'openOtherPublicVote', title='Esmena 1')
        esmenes = [o for o in self.acord.objectValues()
                   if o.portal_type == 'genweb.organs.votacioacord']
        self.assertEqual(len(esmenes), 1)
        self.assertEqual(esmenes[0].title, 'Esmena 1')
        self.assertEqual(esmenes[0].estatVotacio, 'open')
        self.assertEqual(esmenes[0].tipusVotacio, 'public')

    def test_open_other_public_vote_without_title_does_nothing(self):
        self.call_view(self.acord, 'openOtherPublicVote', title='')
        esmenes = [o for o in self.acord.objectValues()
                   if o.portal_type == 'genweb.organs.votacioacord']
        self.assertEqual(esmenes, [])

    def test_multiple_votes_open_at_same_time(self):
        """Decisión de negocio: varias votaciones abiertas a la vez."""
        acord2 = self.create_acord(self.session, id='acord2', title='Acord 2')
        self.open_vote()
        self.open_vote(acord2)
        self.call_view(self.acord, 'openOtherPublicVote', title='Esmena A')
        esmena = [o for o in self.acord.objectValues()
                  if o.portal_type == 'genweb.organs.votacioacord'][0]

        self.vote('membre1', 'favorVote')
        self.vote('membre1', 'againstVote', acord2)
        self.vote('membre1', 'whiteVote', esmena)

        self.assertEqual(as_dict(self.acord.infoVotacio), {'membre1': 'favor'})
        self.assertEqual(as_dict(acord2.infoVotacio), {'membre1': 'against'})
        self.assertEqual(as_dict(esmena.infoVotacio), {'membre1': 'white'})

    def test_remove_vote_resets_fields(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.call_view(self.acord, 'removeVote')
        self.assertIsNone(self.acord.estatVotacio)
        self.assertIsNone(self.acord.tipusVotacio)
        self.assertIsNone(self.acord.horaIniciVotacio)
        self.assertIsNone(self.acord.horaFiVotacio)
        self.assertEqual(as_dict(self.acord.infoVotacio), {})

    def test_remove_esmena_vote_deletes_esmena(self):
        esmena = self.create_esmena(self.acord)
        self.call_view(esmena, 'removeVote')
        self.assertNotIn('esmena', self.acord.objectIds())

    # ------------------------------------------------------------------
    # Registro de votos
    # ------------------------------------------------------------------
    def test_several_users_vote(self):
        self.open_vote()
        self.assertEqual(self.vote('membre1', 'favorVote')['status'], 'success')
        self.assertEqual(self.vote('membre2', 'againstVote')['status'], 'success')
        self.assertEqual(self.vote('secretari', 'whiteVote')['status'], 'success')
        self.assertEqual(
            as_dict(self.acord.infoVotacio),
            {'membre1': 'favor', 'membre2': 'against', 'secretari': 'white'})

    def test_vote_in_esmena(self):
        esmena = self.create_esmena(self.acord)
        self.vote('membre1', 'favorVote', esmena)
        self.vote('membre2', 'againstVote', esmena)
        self.assertEqual(as_dict(esmena.infoVotacio),
                         {'membre1': 'favor', 'membre2': 'against'})
        # El voto en la esmena no afecta al acuerdo
        self.assertEqual(as_dict(self.acord.infoVotacio), {})

    def test_vote_acord_inside_punt(self):
        punt = self.create_punt(self.session)
        acord = self.create_acord(punt, id='acord_punt', title='Acord en Punt')
        self.open_vote(acord)
        self.vote('membre1', 'favorVote', acord)
        self.assertEqual(as_dict(acord.infoVotacio), {'membre1': 'favor'})

    def test_vote_with_legacy_string_info(self):
        self.open_vote()
        self.acord.infoVotacio = "{'membre2': 'white'}"
        self.vote('membre1', 'favorVote')
        self.assertEqual(as_dict(self.acord.infoVotacio),
                         {'membre1': 'favor', 'membre2': 'white'})

    def test_cannot_vote_closed_vote(self):
        self.open_vote()
        self.call_view(self.acord, 'closeVote')
        result = self.vote('membre1', 'favorVote')
        self.assertEqual(result['status'], 'error')
        self.assertEqual(as_dict(self.acord.infoVotacio), {})

    def test_cannot_vote_closed_esmena(self):
        esmena = self.create_esmena(self.acord, estat='close')
        result = self.vote('membre1', 'favorVote', esmena)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(as_dict(esmena.infoVotacio), {})

    def test_votes_persist_in_zodb(self):
        """Los votos deben verse desde otra conexión a la ZODB
        (otro cliente ZEO / tras reiniciar)."""
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.vote('membre2', 'againstVote')
        self.vote('membre3', 'whiteVote')
        transaction.commit()

        conn = self.layer['zodbDB'].open()
        try:
            app = conn.root()['Application']
            acord = app.unrestrictedTraverse(self.acord.getPhysicalPath())
            self.assertEqual(
                as_dict(acord.infoVotacio),
                {'membre1': 'favor', 'membre2': 'against', 'membre3': 'white'})
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Correo de voto
    # ------------------------------------------------------------------
    def assert_vote_mail(self, mail, to, vot, acord, sessio, esmena=None):
        self.assertEqual(mail.mfrom, ORGAN_FROM_MAIL)
        self.assertEqual(mail.mto, to)
        self.assertEqual(mail.subject, 'Votació Govern UPC')
        body = mail.body
        self.assertIn('has votat {0}'.format(vot), body)
        if esmena:
            self.assertIn("l'esmena {0}".format(esmena), body)
        self.assertIn("l'acord {0}".format(acord), body)
        self.assertIn('la sessió {0}'.format(sessio), body)
        self.assertIn("l'òrgan {0}".format(self.organ.title), body)

    def test_vote_sends_confirmation_mail(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        self.assert_vote_mail(mails[0], 'membre1@example.com', 'a favor',
                              'Acord Pressupost', 'Sessio Votacions')
        self.assertEqual(mails[0].recipients, ['membre1@example.com'])

    def test_vote_mail_labels(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.vote('membre2', 'againstVote')
        self.vote('membre3', 'whiteVote')
        bodies = [m.body for m in self.sent_mails()]
        self.assertEqual(len(bodies), 3)
        self.assertIn('has votat a favor', bodies[0])
        self.assertIn('has votat en contra', bodies[1])
        self.assertIn('has votat en blanc', bodies[2])

    def test_vote_mail_acord_inside_punt(self):
        punt = self.create_punt(self.session)
        acord = self.create_acord(punt, id='acord_punt', title='Acord en Punt')
        self.open_vote(acord)
        self.vote('membre1', 'againstVote', acord)
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        self.assert_vote_mail(mails[0], 'membre1@example.com', 'en contra',
                              'Acord en Punt', 'Sessio Votacions')

    def test_vote_mail_esmena(self):
        esmena = self.create_esmena(self.acord, title='Esmena Text')
        self.vote('membre1', 'whiteVote', esmena)
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        self.assert_vote_mail(mails[0], 'membre1@example.com', 'en blanc',
                              'Acord Pressupost', 'Sessio Votacions',
                              esmena='Esmena Text')

    def test_vote_mail_esmena_inside_punt(self):
        punt = self.create_punt(self.session)
        acord = self.create_acord(punt, id='acord_punt', title='Acord en Punt')
        esmena = self.create_esmena(acord, title='Esmena Punt')
        self.vote('membre1', 'favorVote', esmena)
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        self.assert_vote_mail(mails[0], 'membre1@example.com', 'a favor',
                              'Acord en Punt', 'Sessio Votacions',
                              esmena='Esmena Punt')

    def test_change_vote_sends_new_mail(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.vote('membre1', 'againstVote')
        mails = self.sent_mails()
        self.assertEqual(len(mails), 2)
        self.assertIn('has votat en contra', mails[1].body)
        self.assertEqual(as_dict(self.acord.infoVotacio), {'membre1': 'against'})

    def test_user_without_email_votes_but_no_mail(self):
        self.open_vote()
        result = self.vote('membre_sense_email', 'favorVote')
        self.assertEqual(result['status'], 'success')
        self.assertEqual(as_dict(self.acord.infoVotacio),
                         {'membre_sense_email': 'favor'})
        self.assertEqual(self.sent_mails(), [])

    def test_closed_vote_sends_no_mail(self):
        self.open_vote()
        self.call_view(self.acord, 'closeVote')
        self.vote('membre1', 'favorVote')
        self.assertEqual(self.sent_mails(), [])

    def test_vote_mail_uses_crlf(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        raw = self.mailhost.messages[0]
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        self.assertNotRegex(raw, r'(?<!\r)\n')

    def test_organ_from_mail_is_required(self):
        """El remitente de los correos de voto es organ.fromMail: el campo es
        obligatorio y debe ser un email válido, así que nunca falta."""
        from genweb6.organs.content.organgovern.organgovern import IOrgangovern
        field = IOrgangovern['fromMail']
        self.assertTrue(field.required)
        field.validate('organ@example.com')
        with self.assertRaises(Exception):
            field.validate('no-es-un-email')

    # ------------------------------------------------------------------
    # Correo de anulación
    # ------------------------------------------------------------------
    def _prepare_votes(self, session_state):
        session = self.create_session(session_state, id='s_' + session_state,
                                      title='Sessio ' + session_state)
        acord = self.create_acord(session, id='a_' + session_state,
                                  title='Acord ' + session_state)
        acord.estatVotacio = 'close'
        acord.infoVotacio = {'membre1': 'favor', 'membre2': 'against',
                             'membre_sense_email': 'white',
                             'usuari_inexistent': 'favor'}
        self.reset_mails()
        return acord

    def test_remove_vote_mail_in_convocada(self):
        acord = self._prepare_votes('convocada')
        self.call_view(acord, 'removeVote')
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        mail = mails[0]
        self.assertEqual(mail.mfrom, ORGAN_FROM_MAIL)
        self.assertEqual(mail.subject, 'Votació anul·lada Govern UPC')
        # MailHost convierte el Bcc en destinatarios del sobre y lo elimina
        self.assertIsNone(mail.mto)
        self.assertEqual(set(mail.recipients),
                         {'membre1@example.com', 'membre2@example.com'})
        self.assertIn("l'acord Acord convocada", mail.body)
        self.assertIn('ha estat anul·lada', mail.body)

    def test_remove_vote_no_mail_in_closed_states(self):
        for state in ('realitzada', 'tancada', 'en_correccio'):
            acord = self._prepare_votes(state)
            self.call_view(acord, 'removeVote')
            self.assertEqual(self.sent_mails(), [], state)
            self.assertEqual(as_dict(acord.infoVotacio), {}, state)

    def test_remove_vote_without_voters_sends_no_mail(self):
        session = self.create_session('convocada', id='s_buida')
        acord = self.create_acord(session, id='a_buit')
        self.reset_mails()
        self.call_view(acord, 'removeVote')
        self.assertEqual(self.sent_mails(), [])

    # ------------------------------------------------------------------
    # Resultados (reloadVoteStats)
    # ------------------------------------------------------------------
    def _stats(self, user_id, votacio):
        with self.as_user(user_id):
            self.request.UID = votacio.UID()
            return _json(self.session.restrictedTraverse('@@reloadVoteStats')())

    def test_reload_stats_open_vote(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.vote('membre2', 'againstVote')

        stats = self._stats('secretari', self.acord)
        self.assertTrue(stats['open'])
        self.assertEqual(stats['totalVote'], 2)
        self.assertIn('membre1', stats['totalVoteListHTML'])
        # Con la votación abierta no se exponen los sentidos del voto
        self.assertNotIn('favorVote', stats)

    def test_reload_stats_open_vote_membre_does_not_see_names(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        stats = self._stats('membre2', self.acord)
        self.assertEqual(stats['totalVote'], 1)
        self.assertEqual(stats['totalVoteListHTML'], '')

    def test_reload_stats_closed_vote(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.vote('membre2', 'favorVote')
        self.vote('membre3', 'againstVote')
        self.vote('secretari', 'whiteVote')
        self.call_view(self.acord, 'closeVote')

        stats = self._stats('secretari', self.acord)
        self.assertFalse(stats['open'])
        self.assertEqual(stats['favorVote'], 2)
        self.assertEqual(stats['againstVote'], 1)
        self.assertEqual(stats['whiteVote'], 1)
        self.assertEqual(stats['totalVote'], 4)
        self.assertIn('membre3', stats['againstVoteListHTML'])
        self.assertRegex(stats['hourClose'], DATE_RE)

    def test_reload_stats_closed_vote_membre_counts_without_names(self):
        self.open_vote()
        self.vote('membre1', 'favorVote')
        self.call_view(self.acord, 'closeVote')
        stats = self._stats('membre2', self.acord)
        self.assertEqual(stats['favorVote'], 1)
        self.assertEqual(stats['favorVoteListHTML'], '')

    @unittest.expectedFailure
    def test_reload_stats_unknown_uid(self):
        """BUG: con un UID inexistente la vista devuelve False y el decorador
        json_response de genweb6.core hace False.get(...) -> AttributeError
        (error 500). Debería responder JSON vacío/False sin petar."""
        with self.as_user('secretari'):
            self.request.UID = 'no-existeix'
            result = _json(self.session.restrictedTraverse('@@reloadVoteStats')())
        self.assertFalse(result)

    # ------------------------------------------------------------------
    # Permisos de las vistas
    # ------------------------------------------------------------------
    def test_vote_permission_by_role(self):
        self.open_vote()
        for user_id in ('membre1', 'secretari'):
            result = self.vote(user_id, 'favorVote')
            self.assertEqual(result['status'], 'success', user_id)

        for user_id in ('editor', 'afectat', 'convidat'):
            with self.as_user(user_id):
                with self.assertRaises(Unauthorized, msg=user_id):
                    self.call_view(self.acord, 'favorVote')

    def test_manage_vote_permission_by_role(self):
        for user_id in ('membre1', 'afectat', 'convidat'):
            for view in ('openPublicVote', 'closeVote', 'removeVote',
                         'reopenVote', 'openOtherPublicVote'):
                with self.as_user(user_id):
                    with self.assertRaises(Unauthorized, msg=(user_id, view)):
                        self.call_view(self.acord, view)

        for user_id in ('secretari', 'editor'):
            with self.as_user(user_id):
                self.call_view(self.acord, 'openPublicVote')
                self.call_view(self.acord, 'closeVote')
            self.assertEqual(self.acord.estatVotacio, 'close', user_id)

    def test_anonymous_cannot_vote(self):
        from plone.app.testing import logout
        self.open_vote()
        logout()
        with self.assertRaises(Unauthorized):
            self.call_view(self.acord, 'favorVote')
