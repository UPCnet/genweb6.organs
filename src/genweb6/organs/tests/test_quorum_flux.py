# -*- coding: utf-8 -*-
"""Tests funcionales del flujo de quórum (asistencia) de una sesión.

Complementa test_quorum.py (permisos de UI) probando la lógica de
openQuorum / closeQuorum / addQuorum / removeQuorums, los helpers de la
vista de sesión y la persistencia.

Decisión de negocio (docs/PLAN_TESTS.md §7): quórum y votaciones son
independientes; el quórum solo registra asistencia.
"""
import re

import transaction
from AccessControl import Unauthorized

from genweb6.organs.tests.base import as_dict
from genweb6.organs.tests.base import OrgansFunctionalTestCase


DATE_RE = re.compile(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$')


class QuorumFluxTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(QuorumFluxTestCase, self).setUp()
        self.session = self.create_session('realitzada', title='Sessio Quorum')

    def quorums(self):
        return as_dict(self.session.infoQuorums)

    def open_quorum(self):
        self.call_view(self.session, 'openQuorum')

    def close_quorum(self):
        self.call_view(self.session, 'closeQuorum')

    def add_quorum(self, user_id):
        with self.as_user(user_id):
            self.call_view(self.session, 'addQuorum')

    def session_view(self, user_id=None):
        return self.session.restrictedTraverse('@@view')

    # ------------------------------------------------------------------
    # Abrir / cerrar
    # ------------------------------------------------------------------
    def test_initial_state_empty(self):
        self.assertEqual(self.quorums(), {})

    def test_open_first_quorum(self):
        self.open_quorum()
        quorums = self.quorums()
        self.assertEqual(list(quorums.keys()), [1])
        self.assertRegex(quorums[1]['start'], DATE_RE)
        self.assertIsNone(quorums[1]['end'])
        self.assertEqual(quorums[1]['people'], [])
        self.assertEqual(quorums[1]['total'], 0)

    def test_open_twice_does_not_create_second(self):
        self.open_quorum()
        self.open_quorum()
        self.assertEqual(list(self.quorums().keys()), [1])

    def test_close_quorum(self):
        self.open_quorum()
        self.close_quorum()
        self.assertRegex(self.quorums()[1]['end'], DATE_RE)

    def test_close_without_quorum_does_not_fail(self):
        self.close_quorum()
        self.assertEqual(self.quorums(), {})

    def test_close_already_closed_keeps_end(self):
        self.open_quorum()
        self.close_quorum()
        end = self.quorums()[1]['end']
        self.close_quorum()
        self.assertEqual(self.quorums()[1]['end'], end)

    def test_reopen_creates_new_numbered_quorum(self):
        self.open_quorum()
        self.add_quorum('membre1')
        self.close_quorum()
        self.open_quorum()
        quorums = self.quorums()
        self.assertEqual(sorted(quorums.keys()), [1, 2])
        self.assertIsNone(quorums[2]['end'])
        self.assertEqual(quorums[2]['people'], [])
        # El quórum anterior se conserva intacto
        self.assertEqual(quorums[1]['people'], ['membre1'])

    def test_remove_quorums(self):
        self.open_quorum()
        self.add_quorum('membre1')
        self.close_quorum()
        self.open_quorum()
        self.call_view(self.session, 'removeQuorums')
        self.assertEqual(self.quorums(), {})

    # ------------------------------------------------------------------
    # Registro de asistencia
    # ------------------------------------------------------------------
    def test_add_attendees(self):
        self.open_quorum()
        for user_id in ('membre1', 'membre2', 'secretari'):
            self.add_quorum(user_id)
        quorum = self.quorums()[1]
        self.assertEqual(quorum['people'], ['membre1', 'membre2', 'secretari'])
        self.assertEqual(quorum['total'], 3)

    def test_add_twice_does_not_duplicate(self):
        self.open_quorum()
        self.add_quorum('membre1')
        self.add_quorum('membre1')
        quorum = self.quorums()[1]
        self.assertEqual(quorum['people'], ['membre1'])
        self.assertEqual(quorum['total'], 1)

    def test_add_to_closed_quorum_ignored(self):
        self.open_quorum()
        self.close_quorum()
        self.add_quorum('membre1')
        self.assertEqual(self.quorums()[1]['people'], [])

    def test_add_without_quorum_ignored(self):
        self.add_quorum('membre1')
        self.assertEqual(self.quorums(), {})

    def test_add_only_affects_last_quorum(self):
        self.open_quorum()
        self.add_quorum('membre1')
        self.close_quorum()
        self.open_quorum()
        self.add_quorum('membre2')
        quorums = self.quorums()
        self.assertEqual(quorums[1]['people'], ['membre1'])
        self.assertEqual(quorums[2]['people'], ['membre2'])

    def test_legacy_string_info(self):
        self.session.infoQuorums = (
            "{1: {'start': '01/01/2025 10:00', 'end': None, "
            "'people': ['membre2'], 'total': 1}}")
        self.add_quorum('membre1')
        quorum = self.quorums()[1]
        self.assertEqual(quorum['people'], ['membre2', 'membre1'])
        self.assertEqual(quorum['total'], 2)

    def test_quorum_persists_in_zodb(self):
        self.open_quorum()
        self.add_quorum('membre1')
        self.add_quorum('membre2')
        self.close_quorum()
        transaction.commit()

        conn = self.layer['zodbDB'].open()
        try:
            app = conn.root()['Application']
            session = app.unrestrictedTraverse(self.session.getPhysicalPath())
            quorum = as_dict(session.infoQuorums)[1]
            self.assertEqual(quorum['people'], ['membre1', 'membre2'])
            self.assertEqual(quorum['total'], 2)
            self.assertIsNotNone(quorum['end'])
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Helpers de la vista de sesión
    # ------------------------------------------------------------------
    def test_show_open_quorum(self):
        view = self.session_view()
        self.assertTrue(view.showOpenQuorum())
        self.open_quorum()
        self.assertFalse(view.showOpenQuorum())
        self.close_quorum()
        self.assertTrue(view.showOpenQuorum())

    def test_check_has_quorum(self):
        self.open_quorum()
        with self.as_user('membre1'):
            self.assertFalse(self.session_view().checkHasQuorum())
            self.call_view(self.session, 'addQuorum')
            self.assertTrue(self.session_view().checkHasQuorum())
        with self.as_user('membre2'):
            self.assertFalse(self.session_view().checkHasQuorum())
        self.close_quorum()
        with self.as_user('membre1'):
            self.assertFalse(self.session_view().checkHasQuorum())

    def test_get_info_quorums(self):
        self.open_quorum()
        self.add_quorum('membre1')
        info = self.session_view().getInfoQuorums()
        self.assertEqual(info[1]['people'], ['membre1'])

    # ------------------------------------------------------------------
    # Independencia quórum / votación
    # ------------------------------------------------------------------
    def test_can_vote_without_being_in_quorum(self):
        acord = self.create_acord(self.session)
        self.call_view(acord, 'openPublicVote')
        self.open_quorum()
        self.add_quorum('membre1')
        with self.as_user('membre2'):
            self.call_view(acord, 'favorVote')
        self.assertEqual(as_dict(acord.infoVotacio), {'membre2': 'favor'})

    def test_quorum_does_not_change_open_votes(self):
        acord = self.create_acord(self.session)
        self.call_view(acord, 'openPublicVote')
        with self.as_user('membre1'):
            self.call_view(acord, 'favorVote')
        self.open_quorum()
        self.add_quorum('membre1')
        self.close_quorum()
        self.call_view(self.session, 'removeQuorums')
        self.assertEqual(acord.estatVotacio, 'open')
        self.assertEqual(as_dict(acord.infoVotacio), {'membre1': 'favor'})

    # ------------------------------------------------------------------
    # Permisos de las vistas
    # ------------------------------------------------------------------
    def test_manage_quorum_permission(self):
        for user_id in ('secretari', 'editor'):
            with self.as_user(user_id):
                self.call_view(self.session, 'openQuorum')
                self.call_view(self.session, 'closeQuorum')
        self.assertEqual(sorted(self.quorums().keys()), [1, 2])

        for user_id in ('membre1', 'afectat', 'convidat'):
            for view in ('openQuorum', 'closeQuorum'):
                with self.as_user(user_id):
                    with self.assertRaises(Unauthorized, msg=(user_id, view)):
                        self.call_view(self.session, view)

    def test_add_quorum_permission(self):
        self.open_quorum()
        for user_id in ('editor', 'afectat', 'convidat'):
            with self.as_user(user_id):
                with self.assertRaises(Unauthorized, msg=user_id):
                    self.call_view(self.session, 'addQuorum')
        self.assertEqual(self.quorums()[1]['people'], [])

    def test_remove_quorums_only_manager(self):
        self.open_quorum()
        for user_id in ('secretari', 'editor', 'membre1'):
            with self.as_user(user_id):
                with self.assertRaises(Unauthorized, msg=user_id):
                    self.call_view(self.session, 'removeQuorums')
        self.assertIn(1, self.quorums())
