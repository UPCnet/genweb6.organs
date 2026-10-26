# -*- coding: utf-8 -*-
"""
Tests de visibilitat del contingut restringit en òrgans oberts (open_organ).

Un usuari anònim o autenticat sense cap rol a l'òrgan NO pot veure els
fitxers (hiddenfile) ni els documents (alternateContent) restringits:
  - ni al llistat de la sessió (filesinsidePunt)
  - ni a la vista del fitxer (viewReserved)
  - ni a la vista del document (viewDocumentReserved / message)

Els rols OG1-OG5 sí que veuen el contingut restringit.
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
from genweb6.organs.content.document.document import View as DocumentView
from genweb6.organs.content.file.file import View as FileView
from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING

STATES = ['convocada', 'realitzada', 'tancada', 'correccio']
ROLES_WITH_ACCESS = ['OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                     'OG4-Afectat', 'OG5-Convidat']


class TestOpenOrganRestrictedVisibility(unittest.TestCase):

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
            og_unit,
            'open_organ',
            'OG.OPEN',
            'Organ TEST Obert',
            'obert')

        logout()

    def tearDown(self):
        logout()

    def _login_as(self, roles):
        setRoles(self.portal, TEST_USER_ID, roles)
        login(self.portal, TEST_USER_NAME)

    def _sessio(self, state):
        return self.portal.ca.testingfolder.obert[state]

    def _listed_ids(self, state):
        sessio = self._sessio(state)
        view = getMultiAdapter((sessio, self.request), name='view')
        return [f['id'].split('/')[-1] for f in view.filesinsidePunt({'id': 'punt'})]

    def _assert_only_public(self, label):
        for state in STATES:
            ids = self._listed_ids(state)
            # Només la part pública
            self.assertIn('public', ids, '%s/%s' % (label, state))
            self.assertIn('public-restringit', ids, '%s/%s' % (label, state))
            self.assertIn('docpublic', ids, '%s/%s' % (label, state))
            self.assertIn('docboth', ids, '%s/%s' % (label, state))
            # Mai el que només té part restringida
            self.assertNotIn('restringit', ids, '%s/%s' % (label, state))
            self.assertNotIn('docrestringit', ids, '%s/%s' % (label, state))

            sessio = self._sessio(state)
            view = getMultiAdapter((sessio, self.request), name='view')
            for item in view.filesinsidePunt({'id': 'punt'}):
                self.assertNotIn('double-icon', item['classCSS'])
                self.assertNotIn('text-danger', item['classCSS'])
                self.assertNotIn('hiddenfile', item['absolute_url'])
                self.assertNotIn('visibility=private', item['absolute_url'])

            punt = sessio.punt
            self.assertFalse(
                FileView(punt['public-restringit'], self.request).viewReserved())
            self.assertTrue(
                FileView(punt['public-restringit'], self.request).viewPublic())

            docboth = DocumentView(punt.docboth, self.request)
            self.assertFalse(docboth.viewDocumentReserved())
            self.assertTrue(docboth.viewDocumentPublic())
            self.assertIsNone(
                DocumentView(punt.docrestringit, self.request).message())

    def test_anonymous_cannot_see_restricted(self):
        logout()
        self._assert_only_public('Anonymous')

    def test_authenticated_without_role_cannot_see_restricted(self):
        self._login_as(['Member'])
        self._assert_only_public('Member')

    def test_roles_with_access_see_restricted(self):
        for role in ROLES_WITH_ACCESS:
            self._login_as([role])
            for state in STATES:
                ids = self._listed_ids(state)
                self.assertIn('restringit', ids, '%s/%s' % (role, state))
                self.assertIn('docrestringit', ids, '%s/%s' % (role, state))

                punt = self._sessio(state).punt
                self.assertTrue(
                    FileView(punt['public-restringit'], self.request).viewReserved(),
                    '%s/%s' % (role, state))
                self.assertTrue(
                    DocumentView(punt.docboth, self.request).viewDocumentReserved(),
                    '%s/%s' % (role, state))
            logout()
