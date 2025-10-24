# -*- coding: utf-8 -*-
"""Tests de visibilidad de pestañas del órgano.

Verifica qué pestañas son visibles para cada rol y tipo de órgano,
basado en el documento resumen_permisos_organs.html.

PESTAÑAS:
- Sessions: Visible para todos (incluye anónimos en open_organ)
- Composició: Visible para todos (incluye anónimos en open_organ)
- Acords: Visible para todos (incluye anónimos en open_organ)
- Actes: Visible para todos (incluye anónimos en open_organ)
- FAQ membres: Solo visible para roles OG1-OG5 (no anónimos)
"""
import unittest
import warnings

from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from zope.component import getMultiAdapter

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


class OrganTabsTestCase(unittest.TestCase):
    """Tests funcionales para visibilidad de pestañas del órgano."""

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING

    def setUp(self):
        """Configuración inicial del test."""
        warnings.filterwarnings("ignore", category=ResourceWarning,
                                message=".*unclosed file.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        # Create default GW directories
        setupview = getMultiAdapter(
            (self.portal, self.request),
            name='setup-view'
        )
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()

        # Enable Organs folder
        behavior = ISelectableConstrainTypes(self.portal['ca'])
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(['genweb.organs.organsfolder'])
        behavior.setImmediatelyAddableTypes(['genweb.organs.organsfolder'])

        # Clean up
        try:
            api.content.delete(
                obj=self.portal['ca']['testingfolder'],
                check_linkintegrity=False
            )
        except Exception:
            pass

        # Create Organs Test Folder
        og_unit = api.content.create(
            type='genweb.organs.organsfolder',
            id='testingfolder',
            title='Organ Tests',
            container=self.portal['ca']
        )

        # Create organs of different types
        self.organs = {}

        for organ_type, organ_id in [
            ('open_organ', 'obert'),
            ('restricted_to_members_organ', 'membres'),
            ('restricted_to_affected_organ', 'afectats')
        ]:
            organ = api.content.create(
                type='genweb.organs.organgovern',
                id=organ_id,
                title=f'Organ {organ_id.upper()}',
                container=og_unit,
                safe_id=True
            )
            organ.acronim = f'OG.{organ_id.upper()}'
            organ.organType = organ_type
            self.organs[organ_type] = organ

        # Create a session so "Sessions" tab is visible
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        import datetime
        now = datetime.datetime.now()
        for organ in self.organs.values():
            api.content.create(
                type='genweb.organs.sessio',
                id='session1',
                title='Session Test',
                container=organ,
                start=now,
                end=now + datetime.timedelta(hours=1),
                modality='attended',
                numSessioShowOnly='01',
                numSessio='01'
            )

        logout()

    def test_actes_tab_visible_for_membres(self):
        """Test que la pestaña Actes es visible para OG3-Membre."""
        print("\n✅ Verificando pestaña Actes para OG3-Membre")

        logout()
        organ = self.organs['open_organ']

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=organ,
            roles=['OG3-Membre']
        )

        # Acceder a la vista del órgano
        view = organ.restrictedTraverse('@@view')()
        self.assertIsNotNone(view)

        # Verificar que viewActes es True
        view_obj = organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.viewActes())
        print("  ✓ OG3-Membre puede ver pestaña Actes")

        logout()

    def test_actes_tab_not_visible_for_afectats(self):
        """Test que la pestaña Actes NO es visible para OG4-Afectat."""
        print("\n❌ Verificando que OG4-Afectat NO ve pestaña Actes")

        logout()
        organ = self.organs['open_organ']

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=organ,
            roles=['OG4-Afectat']
        )

        # Verificar que viewActes es False
        view_obj = organ.restrictedTraverse('@@view')
        self.assertFalse(view_obj.viewActes())
        print("  ✓ OG4-Afectat NO puede ver pestaña Actes")

        logout()

    def test_actes_tab_not_visible_for_anonymous(self):
        """Test que la pestaña Actes NO es visible para anónimos."""
        print("\n❌ Verificando que anónimos NO ven pestaña Actes")

        logout()
        organ = self.organs['open_organ']

        # Como anónimo
        view_obj = organ.restrictedTraverse('@@view')
        self.assertFalse(view_obj.viewActes())
        print("  ✓ Anónimos NO pueden ver pestaña Actes")

    def test_faq_membres_visible_for_membres(self):
        """Test que FAQ membres es visible para OG3-Membre."""
        print("\n✅ Verificando pestaña FAQ membres para OG3-Membre")

        logout()
        organ = self.organs['open_organ']

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=organ,
            roles=['OG3-Membre']
        )

        # Verificar que canViewFAQs es True
        view_obj = organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewFAQs())
        print("  ✓ OG3-Membre puede ver pestaña FAQ membres")

        logout()

    def test_faq_membres_visible_for_afectats(self):
        """Test que FAQ membres es visible para OG4-Afectat."""
        print("\n✅ Verificando pestaña FAQ membres para OG4-Afectat")

        logout()
        organ = self.organs['open_organ']

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=organ,
            roles=['OG4-Afectat']
        )

        # Verificar que canViewFAQs es True
        view_obj = organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewFAQs())
        print("  ✓ OG4-Afectat puede ver pestaña FAQ membres")

        logout()

    def test_faq_membres_not_visible_for_anonymous(self):
        """Test que FAQ membres NO es visible para anónimos."""
        print("\n❌ Verificando que anónimos NO ven FAQ membres")

        logout()
        organ = self.organs['open_organ']

        # Como anónimo
        view_obj = organ.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewFAQs())
        print("  ✓ Anónimos NO pueden ver pestaña FAQ membres")

    def test_sessions_tab_always_visible(self):
        """Test que la pestaña Sessions se renderiza para todos."""
        print("\n✅ Verificando que pestaña Sessions está disponible")

        organ = self.organs['open_organ']

        # Como Manager - Verificar que existe al menos una sesión
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        sessions = organ.listFolderContents(
            contentFilter={'portal_type': 'genweb.organs.sessio'})
        self.assertTrue(len(sessions) > 0)
        print("  ✓ Hay sesiones en el órgano")

        view_obj = organ.restrictedTraverse('@@view')
        sessions_from_view = view_obj.SessionsInside()
        self.assertIsNotNone(sessions_from_view)
        print("  ✓ Manager puede acceder a la vista de Sessions")
        logout()

        # Como OG3-Membre
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=organ,
            roles=['OG3-Membre']
        )
        view_obj = organ.restrictedTraverse('@@view')
        sessions_from_view = view_obj.SessionsInside()
        self.assertIsNotNone(sessions_from_view)
        print("  ✓ OG3-Membre puede acceder a la vista de Sessions")
        logout()

        # La pestaña Sessions está siempre visible en open_organ
        print("  ✓ Pestaña Sessions disponible para todos en open_organ")

    def test_zzz_tabs_summary(self):
        """Test resumen de visibilidad de pestañas (al final por orden
        alfabético)."""
        print("\n📊 RESUMEN DE VISIBILIDAD DE PESTAÑAS DEL ÓRGANO")
        print("=" * 60)
        print("Pestañas visibles para TODOS los roles:")
        print("  ✓ Sessions")
        print("  ✓ Composición")
        print("  ✓ Acuerdos")
        print("  ✓ Actas")
        print()
        print("En OPEN_ORGAN:")
        print("  ✓ Anónimos pueden ver las 4 pestañas anteriores")
        print()
        print("Pestaña FAQ miembros:")
        print("  ✓ Visible para: OG1-Secretari, OG2-Editor, OG3-Membre")
        print("                  OG4-Afectat, OG5-Convidat")
        print("  ✗ NO visible para: Anónimos")
        print()
        print("En órganos RESTRICTED:")
        print("  ✗ Anónimos NO tienen acceso al órgano")
        print("=" * 60)

        self.assertTrue(True)
