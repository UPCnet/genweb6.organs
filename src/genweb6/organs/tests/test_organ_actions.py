# -*- coding: utf-8 -*-
"""Tests de acciones sobre el órgano.

Verifica qué acciones están disponibles sobre el órgano para cada rol,
basado en el documento resumen_permisos_organs.html.

ACCIONES:
- Crear sessió: OG1-Secretari, OG2-Editor
- Numera sessions: OG1-Secretari, OG2-Editor
- Exportar acords: OG1-Secretari
- Veure el tipus: OG1-Secretari, OG2-Editor
"""
import unittest
import warnings

from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from zope.component import getMultiAdapter

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


class OrganActionsTestCase(unittest.TestCase):
    """Tests funcionales para acciones sobre el órgano."""

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

        # Create Open Organ
        self.organ = api.content.create(
            type='genweb.organs.organgovern',
            id='obert',
            title='Organ TEST Obert',
            container=og_unit,
            safe_id=True
        )
        self.organ.acronim = 'OG.OPEN'
        self.organ.organType = 'open_organ'

        logout()

    def test_secretari_can_create_session(self):
        """Test que OG1-Secretari puede crear sesión."""
        print("\n✅ Verificando que OG1-Secretari puede crear sessió")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        # Verificar que puede crear sesión
        import datetime
        now = datetime.datetime.now()
        try:
            session = api.content.create(
                type='genweb.organs.sessio',
                id='session_secretari',
                title='Session Secretari',
                container=self.organ,
                start=now,
                end=now + datetime.timedelta(hours=1),
                modality='attended',
                numSessioShowOnly='01',
                numSessio='01'
            )
            self.assertIsNotNone(session)
            print("  ✓ OG1-Secretari puede crear sessió")
        except Exception as e:
            self.fail(f"OG1-Secretari debería poder crear sessió: {e}")

        logout()

    def test_editor_can_create_session(self):
        """Test que OG2-Editor puede crear sesión."""
        print("\n✅ Verificando que OG2-Editor puede crear sessió")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        # Verificar que puede crear sesión
        import datetime
        now = datetime.datetime.now()
        try:
            session = api.content.create(
                type='genweb.organs.sessio',
                id='session_editor',
                title='Session Editor',
                container=self.organ,
                start=now,
                end=now + datetime.timedelta(hours=1),
                modality='attended',
                numSessioShowOnly='02',
                numSessio='02'
            )
            self.assertIsNotNone(session)
            print("  ✓ OG2-Editor puede crear sessió")
        except Exception as e:
            self.fail(f"OG2-Editor debería poder crear sessió: {e}")

        logout()

    def test_membre_cannot_create_session(self):
        """Test que OG3-Membre NO puede crear sesión."""
        print("\n❌ Verificando que OG3-Membre NO puede crear sessió")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        # Verificar que NO puede crear sesión
        import datetime
        now = datetime.datetime.now()
        from AccessControl import Unauthorized
        with self.assertRaises(Unauthorized):
            api.content.create(
                type='genweb.organs.sessio',
                id='session_membre',
                title='Session Membre',
                container=self.organ,
                start=now,
                end=now + datetime.timedelta(hours=1),
                modality='attended',
                numSessioShowOnly='03',
                numSessio='03'
            )
        print("  ✓ OG3-Membre NO puede crear sessió")

        logout()

    def test_secretari_can_order_sessions(self):
        """Test que OG1-Secretari puede numerar sessions."""
        print("\n✅ Verificando que OG1-Secretari puede numerar sessions")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        # Verificar viewOrdena
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.viewOrdena())
        print("  ✓ OG1-Secretari puede ver botón 'Numera sessions'")

        # Verificar acceso a la vista orderSessions
        try:
            view = self.organ.restrictedTraverse('@@orderSessions')
            self.assertIsNotNone(view)
            print("  ✓ OG1-Secretari puede acceder a orderSessions")
        except Exception as e:
            self.fail(f"OG1-Secretari debería poder acceder a orderSessions: {e}")

        logout()

    def test_editor_can_order_sessions(self):
        """Test que OG2-Editor puede numerar sessions."""
        print("\n✅ Verificando que OG2-Editor puede numerar sessions")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        # Verificar viewOrdena
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.viewOrdena())
        print("  ✓ OG2-Editor puede ver botón 'Numera sessions'")

        # Verificar acceso a la vista orderSessions
        try:
            view = self.organ.restrictedTraverse('@@orderSessions')
            self.assertIsNotNone(view)
            print("  ✓ OG2-Editor puede acceder a orderSessions")
        except Exception as e:
            self.fail(f"OG2-Editor debería poder acceder a orderSessions: {e}")

        logout()

    def test_membre_cannot_order_sessions(self):
        """Test que OG3-Membre NO puede numerar sessions."""
        print("\n❌ Verificando que OG3-Membre NO puede numerar sessions")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        # Verificar viewOrdena
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertFalse(view_obj.viewOrdena())
        print("  ✓ OG3-Membre NO puede ver botón 'Numera sessions'")
        print("  ✓ Por tanto, no debería usar esta funcionalidad")

        logout()

    def test_secretari_can_export_acords(self):
        """Test que OG1-Secretari puede exportar acords."""
        print("\n✅ Verificando que OG1-Secretari puede exportar acords")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        # Verificar viewExportAcords
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.viewExportAcords())
        print("  ✓ OG1-Secretari puede ver botón 'Exportar acords'")

        # Verificar acceso a la vista getAcordsOrgangovern
        try:
            view = self.organ.restrictedTraverse('@@getAcordsOrgangovern')
            self.assertIsNotNone(view)
            print("  ✓ OG1-Secretari puede acceder a getAcordsOrgangovern")
        except Exception as e:
            self.fail(
                f"OG1-Secretari debería poder acceder a getAcordsOrgangovern: {e}")

        logout()

    def test_editor_cannot_export_acords(self):
        """Test que OG2-Editor NO puede exportar acords."""
        print("\n❌ Verificando que OG2-Editor NO puede exportar acords")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        # Verificar viewExportAcords
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertFalse(view_obj.viewExportAcords())
        print("  ✓ OG2-Editor NO puede ver botón 'Exportar acords'")

        logout()

    def test_secretari_can_view_organ_type(self):
        """Test que OG1-Secretari puede ver el tipo de órgano."""
        print("\n✅ Verificando que OG1-Secretari puede ver el tipo")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        # Verificar canModify
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canModify())
        print("  ✓ OG1-Secretari puede ver el tipo de órgano")

        logout()

    def test_editor_can_view_organ_type(self):
        """Test que OG2-Editor puede ver el tipo de órgano."""
        print("\n✅ Verificando que OG2-Editor puede ver el tipo")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        # Verificar canModify
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canModify())
        print("  ✓ OG2-Editor puede ver el tipo de órgano")

        logout()

    def test_membre_cannot_view_organ_type(self):
        """Test que OG3-Membre NO puede ver el tipo de órgano."""
        print("\n❌ Verificando que OG3-Membre NO puede ver el tipo")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        # Verificar canModify
        view_obj = self.organ.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canModify())
        print("  ✓ OG3-Membre NO puede ver el tipo de órgano")

        logout()

    def test_zzz_actions_summary(self):
        """Test resumen de acciones sobre el órgano (al final por orden
        alfabético)."""
        print("\n📊 RESUMEN DE ACCIONES SOBRE EL ÓRGANO")
        print("=" * 60)
        print("OG1-Secretari puede:")
        print("  ✓ Crear sessió")
        print("  ✓ Numera sessions")
        print("  ✓ Exportar acords")
        print("  ✓ Veure el tipus")
        print()
        print("OG2-Editor puede:")
        print("  ✓ Crear sessió")
        print("  ✓ Numera sessions")
        print("  ✓ Veure el tipus")
        print("  ✗ Exportar acords (solo Secretari)")
        print()
        print("Otros roles:")
        print("  ✗ Sin acceso a estas acciones")
        print("=" * 60)

        self.assertTrue(True)
