# -*- coding: utf-8 -*-
"""Tests de lógica sin servicios externos (fase 4 de PLAN_TESTS.md).

- Unitarios puros: checkhasRol, canViewSessionState, normalize_url,
  get_date_range.
- Funcionales: canViewAcord/Punt/Subpunt (coherencia con la matriz
  SESSION_VIEW_ROLES), checkHasOpenVote, get_organ/get_session/get_acord,
  getColor/estatsCanvi, renumeración al borrar y ExportCSV.
"""
from types import SimpleNamespace

import csv
import datetime
import io
import unittest

from plone import api
from plone.app.textfield.value import RichTextValue
from zope.annotation.interfaces import IAnnotations

from genweb6.organs import permissions
from genweb6.organs import utils
from genweb6.organs.browser.events import removeObject
from genweb6.organs.indicators import data_access
from genweb6.organs.tests.base import OrgansFunctionalTestCase


ORGAN_TYPES = ('open_organ', 'restricted_to_members_organ', 'restricted_to_affected_organ')
STATES = ('planificada', 'convocada', 'realitzada', 'tancada', 'en_correccio')
class _ViewHolder(object):
    """Sustituto de vista (hasheable: permissions.py usa plone.memoize)."""

    def __init__(self, context=None):
        self.context = context


ROLES = ('OG1-Secretari', 'OG2-Editor', 'OG3-Membre', 'OG4-Afectat', 'OG5-Convidat')


# ----------------------------------------------------------------------
# Unitarios puros
# ----------------------------------------------------------------------
class PureUtilsTestCase(unittest.TestCase):

    def test_checkhasrol(self):
        self.assertTrue(utils.checkhasRol(['A', 'B'], ['B']))
        self.assertFalse(utils.checkhasRol(['A'], ['B', 'C']))
        self.assertFalse(utils.checkhasRol([], ['A']))
        self.assertFalse(utils.checkhasRol(['A'], []))

    def test_can_view_session_state_manager(self):
        for organ_type in ORGAN_TYPES:
            for state in STATES:
                self.assertTrue(utils.canViewSessionState(organ_type, state, ['Manager']))

    def test_can_view_session_state_planificada_only_secretari_editor(self):
        for organ_type in ORGAN_TYPES:
            for role in ROLES:
                expected = role in ('OG1-Secretari', 'OG2-Editor')
                self.assertEqual(
                    utils.canViewSessionState(organ_type, 'planificada', [role]),
                    expected, (organ_type, role))

    def test_can_view_session_state_open_organ_public(self):
        for state in STATES[1:]:
            self.assertTrue(utils.canViewSessionState('open_organ', state, []))

    def test_can_view_session_state_restricted_members(self):
        for state in STATES[1:]:
            self.assertFalse(utils.canViewSessionState(
                'restricted_to_members_organ', state, ['OG4-Afectat']))
            self.assertFalse(utils.canViewSessionState(
                'restricted_to_members_organ', state, []))
            self.assertTrue(utils.canViewSessionState(
                'restricted_to_members_organ', state, ['OG5-Convidat']))

    def test_can_view_session_state_restricted_affected(self):
        self.assertFalse(utils.canViewSessionState(
            'restricted_to_affected_organ', 'convocada', ['OG4-Afectat']))
        for state in ('realitzada', 'tancada', 'en_correccio'):
            self.assertTrue(utils.canViewSessionState(
                'restricted_to_affected_organ', state, ['OG4-Afectat']))

    def test_can_view_session_state_unknown(self):
        self.assertFalse(utils.canViewSessionState('open_organ', 'inventat', ['OG1-Secretari']))
        self.assertFalse(utils.canViewSessionState('tipus_inventat', 'convocada', ['OG1-Secretari']))

    def test_normalize_url(self):
        cases = {
            'meet.upc.edu/sala': 'https://meet.upc.edu/sala',
            '  meet.upc.edu  ': 'https://meet.upc.edu',
            'http://a.b': 'http://a.b',
            'https://a.b/c': 'https://a.b/c',
            'mailto:x@upc.edu': 'mailto:x@upc.edu',
            'tel:934000000': 'tel:934000000',
            '/ca/organ': '/ca/organ',
            '': '',
            None: '',
        }
        for value, expected in cases.items():
            self.assertEqual(utils.normalize_url(value), expected, value)

    def test_get_date_range(self):
        source = datetime.datetime(2026, 3, 10, 12, 30, 0)
        start, end = data_access.get_date_range(30, source)
        self.assertEqual((start.year(), start.month(), start.day()), (2026, 3, 10))
        self.assertEqual((end.year(), end.month(), end.day()), (2026, 4, 9))

        start, end = data_access.get_date_range(-10, source)
        self.assertEqual((start.month(), start.day()), (2, 28))
        self.assertEqual((end.month(), end.day()), (3, 10))
        self.assertLess(start, end)


# ----------------------------------------------------------------------
# Funcionales
# ----------------------------------------------------------------------
class LogicFunctionalTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(LogicFunctionalTestCase, self).setUp()
        self.organ.estatsLlista = RichTextValue(
            '<p>Esborrany #777777</p><p>Aprovat #00ff00</p><p>No aprovat #ff0000</p>',
            'text/html', 'text/x-html-safe')

    # -- coherencia de permisos --------------------------------------
    def test_can_view_items_matches_session_matrix(self):
        """canViewAcord/Punt/Subpunt deben coincidir con SESSION_VIEW_ROLES
        (comentario en utils.py: 'Ha de coincidir amb SessioView.canView')."""
        mismatches = []
        for organ_type in ORGAN_TYPES:
            organ = self.create_organ(organ_type, id='o_' + organ_type)
            for state in STATES:
                session = self.create_session(state, id='s_' + state, organ=organ)
                punt = self.create_punt(session)
                subpunt = api.content.create(
                    type='genweb.organs.subpunt', id='subpunt', title='Sub', container=punt)
                acord = self.create_acord(session)
                for role in ROLES:
                    user_id = 'u_{0}_{1}'.format(organ_type.split('_')[-2], role)
                    if user_id not in self.users:
                        self.create_user(user_id, email=user_id + '@example.com',
                                         role=role, obj=organ)
                    expected = utils.canViewSessionState(organ_type, state, [role])
                    with self.as_user(user_id):
                        for func, item in ((permissions.canViewAcord, acord),
                                           (permissions.canViewPunt, punt),
                                           (permissions.canViewSubpunt, subpunt)):
                            got = bool(func(_ViewHolder(), item))
                            if got != expected:
                                mismatches.append((func.__name__, organ_type, state,
                                                   role, got, expected))
        if mismatches:
            self.fail('\n'.join('MISMATCH ' + repr(m) for m in mismatches))

    # -- navegación por la jerarquía ---------------------------------
    def test_get_organ_session_acord(self):
        session = self.create_session('convocada')
        punt = self.create_punt(session)
        acord = self.create_acord(punt)
        esmena = self.create_esmena(acord)
        for obj in (session, punt, acord, esmena):
            self.assertEqual(utils.get_organ(obj), self.organ)
            self.assertEqual(utils.get_session(obj), session)
        self.assertEqual(utils.get_organ(self.organ), self.organ)
        self.assertEqual(utils.get_acord(esmena), acord)
        self.assertEqual(utils.get_acord(acord), acord)
        self.assertIsNone(utils.get_organ(self.organs_folder))

    def test_session_wf_state_from_children(self):
        session = self.create_session('tancada')
        punt = self.create_punt(session)
        acord = self.create_acord(punt)
        for obj in (session, punt, acord):
            self.assertEqual(utils.session_wf_state(SimpleNamespace(context=obj)), 'tancada')

    # -- checkHasOpenVote --------------------------------------------
    def test_check_has_open_vote(self):
        session = self.create_session('realitzada')
        acord = self.create_acord(session)
        self.assertFalse(utils.checkHasOpenVote(acord))
        acord.estatVotacio = 'open'
        self.assertTrue(utils.checkHasOpenVote(acord))
        acord.estatVotacio = 'close'
        esmena = self.create_esmena(acord, estat='close')
        self.assertFalse(utils.checkHasOpenVote(acord))
        esmena.estatVotacio = 'open'
        self.assertTrue(utils.checkHasOpenVote(acord))
        # Desde la propia esmena también se detecta
        self.assertTrue(utils.checkHasOpenVote(esmena))

    # -- colores y estados -------------------------------------------
    def test_estats_canvi(self):
        session = self.create_session('convocada')
        acord = self.create_acord(session)
        items = utils.estatsCanvi(SimpleNamespace(_unrestrictedGetObject=lambda: acord))
        self.assertEqual(items, [
            {'title': 'Esborrany', 'color': '#777777'},
            {'title': 'Aprovat', 'color': '#00ff00'},
            {'title': 'No aprovat', 'color': '#ff0000'},
        ])

    def test_get_color(self):
        session = self.create_session('convocada')
        acord = self.create_acord(session)
        brain = SimpleNamespace(_unrestrictedGetObject=lambda: acord)
        acord.estatsLlista = 'No aprovat'
        self.assertEqual(utils.getColor(brain), '#ff0000')
        acord.estatsLlista = 'Aprovat'
        self.assertEqual(utils.getColor(brain), '#00ff00')
        acord.estatsLlista = 'Estat inexistent'
        self.assertEqual(utils.getColor(brain), '#777777')

    # -- log ---------------------------------------------------------
    def test_add_entry_log_and_excuse(self):
        session = self.create_session('convocada')
        utils.addEntryLog(session, 'Algú', 'Missatge X', 'a@example.com')
        log = IAnnotations(session)['genweb.organs.logMail']
        self.assertEqual(log[-1]['fromMail'], 'Algú')
        self.assertEqual(log[-1]['message'], 'Missatge X')
        self.assertEqual(log[-1]['index'], len(log))

        utils.addExcuse(session, 'Nom', 'n@example.com', 'Motiu')
        utils.addExcuse(session, 'Nom2', 'n2@example.com', 'Motiu2')
        excuses = IAnnotations(session)['genweb.organs.excuse']
        self.assertEqual([e['index'] for e in excuses], [1, 2])
        self.assertEqual(excuses[1]['name'], 'Nom2')

    def test_add_entry_log_sender_from_current_user(self):
        session = self.create_session('convocada')
        with self.as_user('secretari'):
            utils.addEntryLog(session, None, 'M', 'r')
        sender = IAnnotations(session)['genweb.organs.logMail'][-1]['fromMail']
        self.assertIn('secretari', sender)

    # -- renumeración al borrar --------------------------------------
    def confirm_deletion_request(self):
        self.request['URL'] = self.portal.absolute_url() + '/delete_confirmation'
        self.request['REQUEST_METHOD'] = 'POST'
        self.request.form['action'] = 'delete'

    def test_deletion_confirmed(self):
        self.request['URL'] = self.portal.absolute_url() + '/view'
        self.request['REQUEST_METHOD'] = 'GET'
        self.request.form.clear()
        self.assertFalse(removeObject.deletion_confirmed())
        self.confirm_deletion_request()
        self.assertTrue(removeObject.deletion_confirmed())
        self.request.form['form.button.Cancel'] = '1'
        self.assertFalse(removeObject.deletion_confirmed())

    def test_delete_punt_renumbers(self):
        session = self.create_session('planificada')
        punts = []
        for i in range(1, 4):
            punt = self.create_punt(session, id='p{0}'.format(i), title='Punt {0}'.format(i))
            punt.proposalPoint = str(i)
            punt.reindexObject()
            punts.append(punt)
        sub = api.content.create(type='genweb.organs.subpunt', id='s1',
                                 title='Sub', container=punts[2])
        sub.proposalPoint = '3.1'
        sub.reindexObject()

        self.confirm_deletion_request()
        api.content.delete(obj=punts[0], check_linkintegrity=False)

        self.assertEqual(str(session['p2'].proposalPoint), '1')
        self.assertEqual(str(session['p3'].proposalPoint), '2')
        self.assertEqual(session['p3']['s1'].proposalPoint, '2.1')
        log = IAnnotations(session)['genweb.organs.logMail']
        self.assertEqual(log[-1]['message'], 'Deleted punt')

    def test_delete_subpunt_renumbers(self):
        session = self.create_session('planificada')
        punt = self.create_punt(session)
        punt.proposalPoint = '4'
        subs = []
        for i in range(1, 4):
            sub = api.content.create(type='genweb.organs.subpunt', id='s{0}'.format(i),
                                     title='Sub {0}'.format(i), container=punt)
            sub.proposalPoint = '4.{0}'.format(i)
            sub.reindexObject()
            subs.append(sub)

        self.confirm_deletion_request()
        api.content.delete(obj=subs[1], check_linkintegrity=False)
        self.assertEqual(punt['s1'].proposalPoint, '4.1')
        self.assertEqual(punt['s3'].proposalPoint, '4.2')

    def test_delete_without_confirmation_does_not_renumber(self):
        session = self.create_session('planificada')
        for i in range(1, 3):
            punt = self.create_punt(session, id='p{0}'.format(i))
            punt.proposalPoint = str(i)
            punt.reindexObject()
        self.request['REQUEST_METHOD'] = 'GET'
        self.request.form.clear()
        api.content.delete(obj=session['p1'], check_linkintegrity=False)
        self.assertEqual(str(session['p2'].proposalPoint), '2')

    # -- ExportCSV ---------------------------------------------------
    def test_export_csv(self):
        session = self.create_session('convocada', title='Sessio CSV')
        punt = self.create_punt(session, title='Punt CSV')
        punt.proposalPoint = '1'
        punt.estatsLlista = 'Esborrany'
        punt.reindexObject()
        acord = self.create_acord(punt, title='Acord CSV')
        acord.proposalPoint = '1.1'
        acord.agreement = 'ACU-1'
        acord.estatsLlista = 'Aprovat'
        acord.reindexObject()

        view = session.restrictedTraverse('@@exportCSV')
        output = view()
        self.assertIn('text/csv', self.request.response.getHeader('Content-Type'))
        self.assertIn('ordre_del_dia_' + session.id + '.csv',
                      self.request.response.getHeader('Content-Disposition'))

        rows = list(csv.reader(io.StringIO(output.lstrip('﻿'))))
        self.assertEqual(rows[1][1], 'Sessio CSV')
        punt_row = [r for r in rows if len(r) > 1 and r[1] == 'Punt CSV'][0]
        self.assertEqual(punt_row[0], '1')
        self.assertEqual(punt_row[2], 'Punt')
        acord_row = [r for r in rows if len(r) > 1 and r[1] == '-- Acord CSV'][0]
        self.assertEqual(acord_row[:4], ['1.1', '-- Acord CSV', 'Acord', 'ACU-1'])
