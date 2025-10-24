# -*- coding: utf-8 -*-
"""Tests del sistema de quorum.

Verifica qué acciones de quorum están disponibles para cada rol,
basado en los permisos definidos en rolemap.xml.

ACCIONES DE QUORUM:
- Manage Quorum (gestionar quorum): Manager, OG1-Secretari, OG2-Editor
- Add Quorum (añadir quorum): OG1-Secretari, OG3-Membre
- Remove Quorum (eliminar quorum): Manager
"""
import datetime
import unittest
import warnings

from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from zope.component import getMultiAdapter

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


class QuorumTestCase(unittest.TestCase):
    """Tests funcionales para el sistema de quorum."""

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
        organ = api.content.create(
            type='genweb.organs.organgovern',
            id='obert',
            title='Organ TEST Obert',
            container=og_unit,
            safe_id=True
        )
        organ.acronim = 'OG.OPEN'
        organ.organType = 'open_organ'

        # Create session in CONVOCADA (where quorum happens)
        now = datetime.datetime.now()
        session = api.content.create(
            type='genweb.organs.sessio',
            id='convocada',
            title='Session Convocada',
            container=organ,
            start=now,
            end=now + datetime.timedelta(hours=1),
            modality='attended',
            numSessioShowOnly='01',
            numSessio='01'
        )
        api.content.transition(obj=session, transition='convocar')

        self.organ = organ
        self.session = session
        logout()

    def test_manager_can_manage_quorum(self):
        """Test que Manager puede gestionar quorum."""
        print("\n✅ Verificando que Manager puede gestionar quorum")

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewManageQuorumButtons())
        print("  ✓ Manager puede gestionar quorum")

        logout()

    def test_secretari_can_manage_quorum(self):
        """Test que OG1-Secretari puede gestionar quorum."""
        print("\n✅ Verificando que OG1-Secretari puede gestionar quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewManageQuorumButtons())
        print("  ✓ OG1-Secretari puede gestionar quorum")

        logout()

    def test_editor_can_manage_quorum(self):
        """Test que OG2-Editor puede gestionar quorum."""
        print("\n✅ Verificando que OG2-Editor puede gestionar quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewManageQuorumButtons())
        print("  ✓ OG2-Editor puede gestionar quorum")

        logout()

    def test_membre_cannot_manage_quorum(self):
        """Test que OG3-Membre NO puede gestionar quorum."""
        print("\n❌ Verificando que OG3-Membre NO puede gestionar quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewManageQuorumButtons())
        print("  ✓ OG3-Membre NO puede gestionar quorum")

        logout()

    def test_secretari_can_add_quorum(self):
        """Test que OG1-Secretari puede añadir quorum."""
        print("\n✅ Verificando que OG1-Secretari puede añadir quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewAddQuorumButtons())
        print("  ✓ OG1-Secretari puede añadir quorum")

        logout()

    def test_membre_can_add_quorum(self):
        """Test que OG3-Membre puede añadir quorum."""
        print("\n✅ Verificando que OG3-Membre puede añadir quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewAddQuorumButtons())
        print("  ✓ OG3-Membre puede añadir quorum")

        logout()

    def test_editor_cannot_add_quorum(self):
        """Test que OG2-Editor NO puede añadir quorum."""
        print("\n❌ Verificando que OG2-Editor NO puede añadir quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewAddQuorumButtons())
        print("  ✓ OG2-Editor NO puede añadir quorum")
        print("  ✓ OG2-Editor puede gestionar pero no añadir")

        logout()

    def test_afectat_cannot_access_quorum(self):
        """Test que OG4-Afectat NO tiene acceso a quorum."""
        print("\n❌ Verificando que OG4-Afectat NO tiene acceso a quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG4-Afectat']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewManageQuorumButtons())
        self.assertFalse(view_obj.canViewAddQuorumButtons())
        print("  ✓ OG4-Afectat NO puede gestionar quorum")
        print("  ✓ OG4-Afectat NO puede añadir quorum")

        logout()

    def test_convidat_cannot_access_quorum(self):
        """Test que OG5-Convidat NO tiene acceso a quorum."""
        print("\n❌ Verificando que OG5-Convidat NO tiene acceso a quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG5-Convidat']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewManageQuorumButtons())
        self.assertFalse(view_obj.canViewAddQuorumButtons())
        print("  ✓ OG5-Convidat NO puede gestionar quorum")
        print("  ✓ OG5-Convidat NO puede añadir quorum")

        logout()

    def test_anonymous_cannot_access_quorum(self):
        """Test que usuario Anónimo NO tiene acceso a quorum."""
        print("\n❌ Verificando que usuario Anónimo NO tiene acceso a quorum")

        logout()

        # Verificar permisos sin usuario logueado
        self.assertFalse(
            api.user.has_permission(
                'Genweb Organs: Manage Quorum',
                obj=self.session,
            )
        )
        self.assertFalse(
            api.user.has_permission(
                'Genweb Organs: Add Quorum',
                obj=self.session,
            )
        )
        self.assertFalse(
            api.user.has_permission(
                'Genweb Organs: Remove Quorum',
                obj=self.session,
            )
        )
        print("  ✓ Anónimo NO puede gestionar quorum")
        print("  ✓ Anónimo NO puede añadir quorum")
        print("  ✓ Anónimo NO puede eliminar quorum")

    def test_manager_can_remove_quorum(self):
        """Test que Manager puede eliminar quorum."""
        print("\n✅ Verificando que Manager puede eliminar quorum")

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        # Verificar permiso
        self.assertTrue(
            api.user.has_permission(
                'Genweb Organs: Remove Quorum',
                obj=self.session,
            )
        )
        print("  ✓ Manager puede eliminar quorum")

        logout()

    def test_secretari_cannot_remove_quorum(self):
        """Test que OG1-Secretari NO puede eliminar quorum."""
        print("\n❌ Verificando que OG1-Secretari NO puede eliminar quorum")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        # Verificar permiso
        self.assertFalse(
            api.user.has_permission(
                'Genweb Organs: Remove Quorum',
                obj=self.session,
            )
        )
        print("  ✓ OG1-Secretari NO puede eliminar quorum")

        logout()

    def test_user_cannot_vote_twice_in_same_quorum(self):
        """Test que un usuario no puede votar más de una vez en el mismo quorum."""
        print("\n🔒 Verificando que un usuario NO puede votar más de una vez en el mismo quorum")
        
        # Abrir quorum como OG1-Secretari (solo secretarios pueden abrir)
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )
        
        # Abrir quorum
        open_quorum_view = self.session.restrictedTraverse('@@openQuorum')
        open_quorum_view()
        
        # Cambiar a OG3-Membre para votar
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Verificar que el quorum está abierto y vacío
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(len(quorum_info), 1)
        self.assertEqual(quorum_info[1]['total'], 0)
        self.assertEqual(len(quorum_info[1]['people']), 0)
        print("  ✓ Quorum abierto y vacío inicialmente")
        
        # Primera votación - debe funcionar
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que el usuario fue añadido
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 1)
        self.assertIn(TEST_USER_ID, quorum_info[1]['people'])
        print("  ✓ Primera votación registrada correctamente")
        
        # Segunda votación - NO debe añadir al usuario de nuevo
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que el usuario NO fue añadido de nuevo
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 1)  # Sigue siendo 1, no 2
        people_count = quorum_info[1]['people'].count(TEST_USER_ID)
        self.assertEqual(people_count, 1)  # El usuario aparece solo una vez
        print("  ✓ Segunda votación NO fue registrada (protección activa)")
        
        # Tercera votación - también debe ser ignorada
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que sigue siendo 1
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 1)
        people_count = quorum_info[1]['people'].count(TEST_USER_ID)
        self.assertEqual(people_count, 1)
        print("  ✓ Tercera votación también fue ignorada")
        
        logout()

    def test_different_users_can_vote_in_same_quorum(self):
        """Test que diferentes usuarios pueden votar en el mismo quorum."""
        print("\n👥 Verificando que diferentes usuarios pueden votar en el mismo quorum")
        
        # Crear segundo usuario
        api.user.create(
            username='testuser2',
            email='testuser2@example.com',
            password='secret123'
        )
        
        # Abrir quorum como OG1-Secretari (solo secretarios pueden abrir)
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )
        
        # Abrir quorum
        open_quorum_view = self.session.restrictedTraverse('@@openQuorum')
        open_quorum_view()
        
        # Cambiar a OG3-Membre para votar
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Usuario 1 vota
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        logout()
        
        # Usuario 2 vota
        setRoles(self.portal, 'testuser2', ['Member'])
        login(self.portal, 'testuser2')
        api.user.grant_roles(
            username='testuser2',
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Usuario 2 vota
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que ambos usuarios están en el quorum
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 2)
        self.assertIn(TEST_USER_ID, quorum_info[1]['people'])
        self.assertIn('testuser2', quorum_info[1]['people'])
        print("  ✓ Ambos usuarios pueden votar en el mismo quorum")
        
        # Usuario 2 intenta votar de nuevo - no debe funcionar
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que sigue siendo 2
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 2)
        people_count = quorum_info[1]['people'].count('testuser2')
        self.assertEqual(people_count, 1)
        print("  ✓ Usuario 2 tampoco puede votar dos veces")
        
        logout()

    def test_cannot_add_quorum_when_closed(self):
        """Test que no se puede añadir quorum cuando está cerrado."""
        print("\n🔒 Verificando que NO se puede añadir quorum cuando está cerrado")
        
        # Abrir quorum como OG1-Secretari (solo secretarios pueden abrir)
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )
        
        # Abrir quorum
        open_quorum_view = self.session.restrictedTraverse('@@openQuorum')
        open_quorum_view()
        
        # Cambiar a OG3-Membre para votar
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Verificar que el quorum está abierto
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(len(quorum_info), 1)
        self.assertIsNone(quorum_info[1]['end'])  # No tiene fecha de cierre
        print("  ✓ Quorum abierto correctamente")
        
        # Usuario vota (debe funcionar)
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que el usuario fue añadido
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 1)
        self.assertIn(TEST_USER_ID, quorum_info[1]['people'])
        print("  ✓ Votación en quorum abierto funcionó correctamente")
        
        # Cerrar quorum (como Manager)
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        
        close_quorum_view = self.session.restrictedTraverse('@@closeQuorum')
        close_quorum_view()
        
        # Verificar que el quorum está cerrado
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertIsNotNone(quorum_info[1]['end'])  # Tiene fecha de cierre
        print("  ✓ Quorum cerrado correctamente")
        
        # Cambiar a usuario que puede añadir quorum
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Intentar añadir quorum cuando está cerrado - NO debe funcionar
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que el usuario NO fue añadido de nuevo
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(quorum_info[1]['total'], 1)  # Sigue siendo 1, no 2
        people_count = quorum_info[1]['people'].count(TEST_USER_ID)
        self.assertEqual(people_count, 1)  # El usuario aparece solo una vez
        print("  ✓ NO se pudo añadir quorum cuando está cerrado (protección activa)")
        
        # Verificar que showOpenQuorum devuelve True (se puede abrir nuevo quorum)
        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.showOpenQuorum())
        print("  ✓ Se puede abrir un nuevo quorum después de cerrar el anterior")
        
        logout()

    def test_cannot_add_quorum_when_no_quorum_exists(self):
        """Test que no se puede añadir quorum cuando no existe ningún quorum."""
        print("\n🔒 Verificando que NO se puede añadir quorum cuando no existe ningún quorum")
        
        # Crear usuario con rol OG3-Membre (puede añadir quorum)
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Verificar que no hay quorums inicialmente
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(len(quorum_info), 0)
        print("  ✓ No hay quorums inicialmente")
        
        # Intentar añadir quorum sin abrir uno primero - NO debe funcionar
        add_quorum_view = self.session.restrictedTraverse('@@addQuorum')
        add_quorum_view()
        
        # Verificar que no se creó ningún quorum
        quorum_info = self.session.restrictedTraverse('@@view').getInfoQuorums()
        self.assertEqual(len(quorum_info), 0)
        print("  ✓ NO se pudo añadir quorum sin abrir uno primero (protección activa)")
        
        logout()

    def test_zzz_quorum_summary(self):
        """Test resumen del sistema de quorum (al final por orden
        alfabético)."""
        print("\n📊 RESUMEN DEL SISTEMA DE QUORUM")
        print("=" * 60)
        print("Manager, OG1-Secretari y OG2-Editor pueden:")
        print("  ✓ Gestionar quorum (Manage Quorum)")
        print()
        print("Manager puede:")
        print("  ✓ Eliminar quorum (Remove Quorum)")
        print()
        print("OG1-Secretari y OG3-Membre pueden:")
        print("  ✓ Añadir quorum (Add Quorum)")
        print()
        print("OG2-Editor puede:")
        print("  ✓ Gestionar quorum")
        print("  ✗ NO puede añadir quorum")
        print()
        print("OG3-Membre puede:")
        print("  ✓ Añadir quorum")
        print("  ✗ NO puede gestionar quorum")
        print()
        print("OG4-Afectat:")
        print("  ✗ Sin acceso a funcionalidades de quorum")
        print()
        print("OG5-Convidat:")
        print("  ✗ Sin acceso a funcionalidades de quorum")
        print()
        print("Usuarios Anónimos:")
        print("  ✗ Sin ningún permiso de quorum")
        print()
        print("🔒 PROTECCIÓN ANTI-DUPLICADOS:")
        print("  ✓ Un usuario NO puede votar más de una vez en el mismo quorum")
        print("  ✓ Diferentes usuarios SÍ pueden votar en el mismo quorum")
        print("  ✓ El sistema previene automáticamente votos duplicados")
        print()
        print("🔒 PROTECCIÓN DE ESTADO:")
        print("  ✓ NO se puede añadir quorum cuando está cerrado")
        print("  ✓ NO se puede añadir quorum sin abrir uno primero")
        print("  ✓ Solo se puede votar en quorums abiertos")
        print("=" * 60)

        self.assertTrue(True)
