# -*- coding: utf-8 -*-
"""Tests de las vistas AJAX del orden del día de una sesión.

- @@deleteElement / @@removeElement: borrar punt/acord/subpunt y renumerar.
- @@fcmoveTable: mover puntos y subpuntos y renumerar proposalPoint.
- @@changeActualState / @@changeSubpuntState: estado (color) de puntos/acuerdos.
"""
import json

from AccessControl import Unauthorized
from plone import api
from zope.annotation.interfaces import IAnnotations

from genweb6.organs.tests.base import OrgansFunctionalTestCase


class OrdreDiaViewsTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(OrdreDiaViewsTestCase, self).setUp()
        self.session = self.create_session('planificada', title='Sessio ODD')
        self.p1 = self.add('genweb.organs.punt', self.session, 'p1', '1')
        self.p2 = self.add('genweb.organs.punt', self.session, 'p2', '2')
        self.a3 = self.add('genweb.organs.acord', self.session, 'a3', '3')
        self.s21 = self.add('genweb.organs.subpunt', self.p2, 's1', '2.1')
        self.s22 = self.add('genweb.organs.subpunt', self.p2, 's2', '2.2')
        self.a23 = self.add('genweb.organs.acord', self.p2, 'a1', '2.3')

    def add(self, portal_type, container, id, point):
        obj = api.content.create(type=portal_type, id=id,
                                 title='T ' + id, container=container)
        obj.proposalPoint = point
        obj.estatsLlista = 'Esborrany'
        if portal_type == 'genweb.organs.acord':
            obj.infoVotacio = '{}'
        obj.reindexObject()
        return obj

    def points(self, container):
        return [(o.getId(), str(o.proposalPoint)) for o in container.objectValues()
                if o.portal_type in ('genweb.organs.punt', 'genweb.organs.acord',
                                     'genweb.organs.subpunt')]

    def log_messages(self):
        return [e['message'] for e in IAnnotations(self.session).get('genweb.organs.logMail', [])]

    # ------------------------------------------------------------------
    # deleteElement
    # ------------------------------------------------------------------
    def delete(self, itemid, portal_type, view='deleteElement'):
        return json.loads(self.call_view(
            self.session, view, action='delete', id=itemid, type=portal_type))

    def test_delete_punt_renumbers(self):
        result = self.delete('p1', 'genweb.organs.punt')
        self.assertEqual(result['status'], 'success')
        self.assertNotIn('p1', self.session.objectIds())
        self.assertEqual(self.points(self.session), [('p2', '1'), ('a3', '2')])
        self.assertEqual(self.points(self.p2),
                         [('s1', '1.1'), ('s2', '1.2'), ('a1', '1.3')])
        self.assertIn('Deleted via javascript', self.log_messages())

    def test_delete_subpunt_by_path(self):
        result = self.delete('p2/s1', 'genweb.organs.subpunt')
        self.assertEqual(result['status'], 'success')
        self.assertNotIn('s1', self.p2.objectIds())
        self.assertEqual(self.points(self.p2), [('s2', '2.1'), ('a1', '2.2')])

    def test_remove_element_alias(self):
        result = self.delete('a3', 'genweb.organs.acord', view='removeElement')
        self.assertEqual(result['status'], 'success')
        self.assertNotIn('a3', self.session.objectIds())

    def test_delete_not_found(self):
        result = self.delete('no_existeix', 'genweb.organs.punt')
        self.assertEqual(result, {'status': 'error', 'message': 'Element not found'})

    def test_delete_wrong_type_not_found(self):
        result = self.delete('p1', 'genweb.organs.acord')
        self.assertEqual(result['status'], 'error')
        self.assertIn('p1', self.session.objectIds())

    def test_delete_invalid_params(self):
        result = json.loads(self.call_view(self.session, 'deleteElement', id='p1'))
        self.assertEqual(result, {'status': 'error', 'message': 'Invalid parameters'})
        self.assertIn('p1', self.session.objectIds())

    def test_delete_requires_modify_permission(self):
        api.content.transition(obj=self.session, transition='convocar')
        for user_id in ('membre1', 'afectat', 'convidat'):
            with self.as_user(user_id):
                with self.assertRaises(Unauthorized, msg=user_id):
                    self.call_view(self.session, 'deleteElement', action='delete',
                                   id='p1', type='genweb.organs.punt')
        self.assertIn('p1', self.session.objectIds())

    # ------------------------------------------------------------------
    # fcmoveTable
    # ------------------------------------------------------------------
    def test_move_punt_down(self):
        self.call_view(self.session, 'fcmoveTable', action='movepunt',
                       itemid='p1', delta='1')
        self.assertEqual(self.points(self.session),
                         [('p2', '1'), ('p1', '2'), ('a3', '3')])
        self.assertEqual(self.points(self.p2),
                         [('s1', '1.1'), ('s2', '1.2'), ('a1', '1.3')])
        self.assertIn('Changed punt number with drag&drop', self.log_messages())

    def test_move_punt_up_to_top(self):
        self.call_view(self.session, 'fcmoveTable', action='movepunt',
                       itemid='a3', delta='-2')
        self.assertEqual(self.points(self.session),
                         [('a3', '1'), ('p1', '2'), ('p2', '3')])
        self.assertEqual(self.points(self.p2),
                         [('s1', '3.1'), ('s2', '3.2'), ('a1', '3.3')])

    def test_move_subpunt(self):
        self.call_view(self.session, 'fcmoveTable', action='movesubpunt',
                       itemid='p2/a1', delta='-2')
        self.assertEqual(self.points(self.p2),
                         [('a1', '2.1'), ('s1', '2.2'), ('s2', '2.3')])
        self.assertIn('Moved subpunt by drag&drop', self.log_messages())

    def test_move_ignored_when_migrated(self):
        self.session.migrated = True
        self.call_view(self.session, 'fcmoveTable', action='movepunt',
                       itemid='p1', delta='1')
        self.assertEqual(self.points(self.session)[0], ('p1', '1'))

    # ------------------------------------------------------------------
    # changeActualState / changeSubpuntState
    # ------------------------------------------------------------------
    def test_change_state_punt_is_recursive(self):
        self.call_view(self.session, 'changeActualState', id='p2', estat='Aprovat')
        self.assertEqual(self.p2.estatsLlista, 'Aprovat')
        for obj in (self.s21, self.s22, self.a23):
            self.assertEqual(obj.estatsLlista, 'Aprovat', obj.getId())
        self.assertEqual(self.p1.estatsLlista, 'Esborrany')
        self.assertIn('Changed punt color state', self.log_messages())

    def test_change_state_acord(self):
        self.call_view(self.session, 'changeActualState', id='a3', estat='No aprovat')
        self.assertEqual(self.a3.estatsLlista, 'No aprovat')
        self.assertIn('Changed acord color state', self.log_messages())

    def test_change_state_unknown_item_silent(self):
        self.call_view(self.session, 'changeActualState', id='no_existeix', estat='Aprovat')
        self.assertEqual(self.p1.estatsLlista, 'Esborrany')

    def test_change_subpunt_state_not_recursive(self):
        self.call_view(self.session, 'changeSubpuntState', id='p2/s1', estat='Aprovat')
        self.assertEqual(self.s21.estatsLlista, 'Aprovat')
        self.assertEqual(self.s22.estatsLlista, 'Esborrany')
        self.assertEqual(self.p2.estatsLlista, 'Esborrany')
        self.assertIn('Changed subpunt intern state color', self.log_messages())

    def test_change_state_requires_modify_permission(self):
        api.content.transition(obj=self.session, transition='convocar')
        with self.as_user('membre1'):
            with self.assertRaises(Unauthorized):
                self.call_view(self.session, 'changeActualState', id='p1', estat='Aprovat')
        self.assertEqual(self.p1.estatsLlista, 'Esborrany')
