# -*- coding: utf-8 -*-
"""
Tests de visibilitat de utils.FilesandDocumentsInside (llistat de fitxers i
documents de punts / subpunts / acords).

Regla:
  Òrgans públics:
    Sec, Ed, Mem, Conv veuen les dues parts diferenciades.
    Afectats i anònims (i autenticats sense rol) només la pública.
  Òrgans restringits a membres:
    Sec, Ed, Mem, Conv veuen les dues parts diferenciades.
    Afectats i anònims no en veuen cap.
  Òrgans restringits a afectats:
    Sec, Ed, Mem, Conv veuen les dues parts diferenciades.
    Afectats veuen la pública.
    Anònims no en veuen cap.
"""

import unittest
import warnings

from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout
from plone.app.testing import setRoles
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from zope.component import getMultiAdapter

from genweb6.organs.browser import tools
from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING

ALL_ITEMS = {'public', 'restringit', 'public-restringit',
             'docpublic', 'docrestringit', 'docboth'}
PUBLIC_ITEMS = {'public', 'public-restringit', 'docpublic', 'docboth'}
DOUBLE_ITEMS = {'public-restringit', 'docboth'}


class TestFilesandDocumentsInsideVisibility(unittest.TestCase):

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING

    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning,
                                message=".*unclosed file.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setupview = getMultiAdapter((self.portal, self.request), name='setup-view')
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()

        behavior = ISelectableConstrainTypes(self.portal['ca'])
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(['genweb.organs.organsfolder'])
        behavior.setImmediatelyAddableTypes(['genweb.organs.organsfolder'])

        try:
            api.content.delete(
                obj=self.portal['ca']['testingfolder'],
                check_linkintegrity=False)
        except Exception:
            pass

        og_unit = api.content.create(
            type='genweb.organs.organsfolder',
            id='testingfolder',
            title='Organ Tests',
            container=self.portal['ca'])

        tools.create_organ_content(
            og_unit, 'open_organ', 'OG.OPEN', 'Organ TEST Obert', 'obert')
        tools.create_organ_content(
            og_unit, 'restricted_to_members_organ', 'OG.MEMBERS',
            'Organ TEST restringit a MEMBRES', 'membres')
        tools.create_organ_content(
            og_unit, 'restricted_to_affected_organ', 'OG.AFFECTED',
            'Organ TEST restringit a AFECTATS', 'afectats')

        logout()

    def tearDown(self):
        logout()

    def _login_as(self, roles):
        setRoles(self.portal, TEST_USER_ID, roles)
        login(self.portal, TEST_USER_NAME)

    def _listing(self, organ_id):
        punt = self.portal.ca.testingfolder[organ_id].realitzada.punt
        view = getMultiAdapter((punt, self.request), name='view')
        return view.FilesandDocumentsInside()

    @staticmethod
    def _item_id(item):
        return item['absolute_url'].split('/punt/')[1].split('/')[0]

    def _ids(self, items):
        return {self._item_id(item) for item in items}

    def _assert_both_differentiated(self, items, label):
        self.assertEqual(self._ids(items), ALL_ITEMS, label)
        for item in items:
            item_id = self._item_id(item)
            if item_id in DOUBLE_ITEMS:
                self.assertIn('double-icon', item['classCSS'], label)
                # Doble contingut → vista de l'objecte amb les dues parts
                self.assertTrue(item['absolute_url'].endswith('/punt/' + item_id), label)
                self.assertIsNone(item['target'], label)
            elif item_id in ('restringit', 'docrestringit'):
                self.assertIn('text-danger', item['classCSS'], label)
            else:
                self.assertIn('text-success', item['classCSS'], label)

    def _assert_only_public(self, items, label):
        self.assertEqual(self._ids(items), PUBLIC_ITEMS, label)
        for item in items:
            self.assertNotIn('double-icon', item['classCSS'], label)
            self.assertNotIn('text-danger', item['classCSS'], label)
            self.assertNotIn('hiddenfile', item['absolute_url'], label)
            self.assertNotIn('visibility=private', item['absolute_url'], label)

    # Òrgans públics -----------------------------------------------------

    def test_open_roles_see_both(self):
        for role in ['OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                     'OG5-Convidat']:
            self._login_as([role])
            self._assert_both_differentiated(self._listing('obert'), 'obert/' + role)
            logout()

    def test_open_afectat_only_public(self):
        self._login_as(['OG4-Afectat'])
        self._assert_only_public(self._listing('obert'), 'obert/OG4-Afectat')

    def test_open_anonymous_only_public(self):
        logout()
        self._assert_only_public(self._listing('obert'), 'obert/Anonymous')

    def test_open_authenticated_without_role_only_public(self):
        self._login_as(['Member'])
        self._assert_only_public(self._listing('obert'), 'obert/Member')

    # Òrgans restringits a membres ---------------------------------------

    def test_members_roles_see_both(self):
        for role in ['OG1-Secretari', 'OG2-Editor', 'OG3-Membre', 'OG5-Convidat']:
            self._login_as([role])
            self._assert_both_differentiated(self._listing('membres'), 'membres/' + role)
            logout()

    def test_members_afectat_and_anonymous_see_nothing(self):
        self._login_as(['OG4-Afectat'])
        self.assertEqual(self._listing('membres'), [], 'membres/OG4-Afectat')
        self._login_as(['Member'])
        self.assertEqual(self._listing('membres'), [], 'membres/Member')

    # Òrgans restringits a afectats --------------------------------------

    def test_affected_roles_see_both(self):
        for role in ['OG1-Secretari', 'OG2-Editor', 'OG3-Membre', 'OG5-Convidat']:
            self._login_as([role])
            self._assert_both_differentiated(self._listing('afectats'), 'afectats/' + role)
            logout()

    def test_affected_afectat_only_public(self):
        self._login_as(['OG4-Afectat'])
        self._assert_only_public(self._listing('afectats'), 'afectats/OG4-Afectat')

    def test_affected_authenticated_without_role_sees_nothing(self):
        self._login_as(['Member'])
        self.assertEqual(self._listing('afectats'), [], 'afectats/Member')
