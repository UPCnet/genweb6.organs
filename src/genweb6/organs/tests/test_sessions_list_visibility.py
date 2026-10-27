# -*- coding: utf-8 -*-
"""Tests de visibilidad del listado de sesiones del órgano.

El listado (@@getSessionsOrgangovern) debe mostrar las mismas sesiones que
el usuario puede abrir con la vista de la sesión (SessioView.canView).

Caso reportado: en un órgano restringido a afectados, OG4-Afectat veía en el
listado las sesiones convocadas (el workflow da View) pero al abrirlas
obtenía Unauthorized.
"""
import datetime
import json
import unittest
import warnings

from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from zope.component import getMultiAdapter

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


SESSION_TRANSITIONS = {
    'planificada': [],
    'convocada': ['convocar'],
    'realitzada': ['convocar', 'realitzar'],
    'tancada': ['convocar', 'realitzar', 'tancar'],
    'en_correccio': ['convocar', 'realitzar', 'tancar', 'corregir'],
}


class SessionsListVisibilityTestCase(unittest.TestCase):
    """Tests funcionales del listado de sesiones por rol y tipo de órgano."""

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING

    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning,
                                message=".*unclosed file.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setupview = getMultiAdapter(
            (self.portal, self.request),
            name='setup-view'
        )
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()

        behavior = ISelectableConstrainTypes(self.portal['ca'])
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(['genweb.organs.organsfolder'])
        behavior.setImmediatelyAddableTypes(['genweb.organs.organsfolder'])

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        og_unit = api.content.create(
            type='genweb.organs.organsfolder',
            id='testingfolder',
            title='Organ Tests',
            container=self.portal['ca']
        )
        self.organs = {}
        for organ_type in ['open_organ', 'restricted_to_affected_organ']:
            organ = api.content.create(
                type='genweb.organs.organgovern',
                id=organ_type,
                title=organ_type,
                container=og_unit,
                safe_id=True
            )
            organ.acronim = 'OG.TEST'
            organ.organType = organ_type
            self._create_sessions(organ)
            self.organs[organ_type] = organ

        logout()

    def _create_sessions(self, organ):
        now = datetime.datetime.now()
        for state, transitions in SESSION_TRANSITIONS.items():
            session = api.content.create(
                type='genweb.organs.sessio',
                id=state,
                title=state,
                container=organ,
                start=now,
                end=now + datetime.timedelta(hours=1),
                modality='attended',
                numSessioShowOnly='01',
                numSessio='01'
            )
            for transition in transitions:
                api.content.transition(obj=session, transition=transition)

    def _listed_states(self, organ, role):
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(username=TEST_USER_ID, obj=organ, roles=[role])
        organ.reindexObjectSecurity()
        try:
            view = organ.restrictedTraverse('@@getSessionsOrgangovern')
            data = json.loads(view())
            return sorted(item['review_state'] for item in data['items'])
        finally:
            api.user.revoke_roles(
                username=TEST_USER_ID, obj=organ, roles=[role])
            organ.reindexObjectSecurity()
            logout()

    def test_afectat_no_veu_convocades_en_organ_afectats(self):
        organ = self.organs['restricted_to_affected_organ']
        self.assertEqual(
            self._listed_states(organ, 'OG4-Afectat'),
            ['en_correccio', 'realitzada', 'tancada'])

    def test_membre_veu_convocades_en_organ_afectats(self):
        organ = self.organs['restricted_to_affected_organ']
        self.assertEqual(
            self._listed_states(organ, 'OG3-Membre'),
            ['convocada', 'en_correccio', 'realitzada', 'tancada'])

    def test_secretari_veu_totes_en_organ_afectats(self):
        organ = self.organs['restricted_to_affected_organ']
        self.assertEqual(
            self._listed_states(organ, 'OG1-Secretari'),
            sorted(SESSION_TRANSITIONS))

    def test_afectat_veu_convocades_en_organ_obert(self):
        organ = self.organs['open_organ']
        self.assertEqual(
            self._listed_states(organ, 'OG4-Afectat'),
            ['convocada', 'en_correccio', 'realitzada', 'tancada'])
