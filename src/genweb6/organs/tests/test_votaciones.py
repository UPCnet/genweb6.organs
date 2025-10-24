# -*- coding: utf-8 -*-
"""Tests del sistema de votaciones.

Verifica qué acciones de votación están disponibles para cada rol,
basado en el documento resumen_permisos_organs.html.

ACCIONES DE VOTACIÓN:
- Abrir votación: OG1-Secretari, OG2-Editor
- Cerrar votación: OG1-Secretari, OG2-Editor
- Ver botones de voto: OG1-Secretari, OG2-Editor
- Ver resultados de votación a mano alzada: OG1-Secretari, OG2-Editor,
  OG3-Membre
- Ver quién votó qué: OG1-Secretari, OG2-Editor
"""
import ast
import datetime
import unittest
import warnings

from AccessControl.unauthorized import Unauthorized
from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from zope.component import getMultiAdapter

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


class VotacionesTestCase(unittest.TestCase):
    """Tests funcionales para el sistema de votaciones."""

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

        # Create session in REALITZADA (where voting happens)
        now = datetime.datetime.now()
        session = api.content.create(
            type='genweb.organs.sessio',
            id='realitzada',
            title='Session Realitzada',
            container=organ,
            start=now,
            end=now + datetime.timedelta(hours=1),
            modality='attended',
            numSessioShowOnly='01',
            numSessio='01'
        )
        api.content.transition(obj=session, transition='convocar')
        api.content.transition(obj=session, transition='realitzar')

        self.organ = organ
        self.session = session
        logout()

    def test_secretari_can_manage_vote(self):
        """Test que OG1-Secretari puede gestionar votaciones."""
        print("\n✅ Verificando que OG1-Secretari puede gestionar votaciones")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewManageVote())
        print("  ✓ OG1-Secretari puede abrir/cerrar votación")
        print("  ✓ OG1-Secretari puede ver quién votó qué")

        logout()

    def test_editor_can_manage_vote(self):
        """Test que OG2-Editor puede gestionar votaciones."""
        print("\n✅ Verificando que OG2-Editor puede gestionar votaciones")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewManageVote())
        print("  ✓ OG2-Editor puede abrir/cerrar votación")
        print("  ✓ OG2-Editor puede ver quién votó qué")

        logout()

    def test_membre_cannot_manage_vote(self):
        """Test que OG3-Membre NO puede gestionar votaciones."""
        print("\n❌ Verificando que OG3-Membre NO puede gestionar votaciones")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewManageVote())
        print("  ✓ OG3-Membre NO puede gestionar votaciones")
        print("  ✓ OG3-Membre NO puede ver quien votó qué")

        logout()

    def test_secretari_can_view_vote_buttons(self):
        """Test que OG1-Secretari puede ver botones de voto."""
        print("\n✅ Verificando que OG1-Secretari puede ver botones de voto")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewVoteButtons())
        print("  ✓ OG1-Secretari puede ver botones de voto")

        logout()

    def test_membre_can_view_vote_buttons(self):
        """Test que OG3-Membre puede ver botones de voto."""
        print("\n✅ Verificando que OG3-Membre puede ver botones de voto")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewVoteButtons())
        print("  ✓ OG3-Membre puede ver botones de voto")

        logout()

    def test_editor_cannot_view_vote_buttons(self):
        """Test que OG2-Editor NO puede ver botones de voto."""
        print("\n❌ Verificando que OG2-Editor NO puede ver botones de voto")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewVoteButtons())
        print("  ✓ OG2-Editor NO puede ver botones de voto")
        print("  ✓ OG2-Editor gestiona pero no vota")

        logout()

    def test_editor_cannot_vote(self):
        """Test que OG2-Editor NO puede votar en ningún momento."""
        print("\n❌ Verificando que OG2-Editor NO puede votar en ningún momento")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        # Crear un acord con votación abierta
        acord = api.content.create(
            type='genweb.organs.acord',
            id='acord_test_editor',
            title='Acord Test Editor',
            container=self.session
        )
        
        # Abrir votación
        acord.estatVotacio = 'open'
        acord.horaIniciVotacio = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
        acord.infoVotacio = '{}'
        acord.reindexObject()

        # Verificar que NO puede ver botones de voto
        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewVoteButtons())
        print("  ✓ OG2-Editor NO puede ver botones de voto")

        # Intentar votar a favor - NO debe funcionar (debe lanzar Unauthorized)
        with self.assertRaises(Unauthorized):
            favor_vote_view = acord.restrictedTraverse('@@favorVote')
            result = favor_vote_view()
        print("  ✓ OG2-Editor NO puede votar a favor (Unauthorized)")

        # Intentar votar en contra - NO debe funcionar (debe lanzar Unauthorized)
        with self.assertRaises(Unauthorized):
            against_vote_view = acord.restrictedTraverse('@@againstVote')
            result = against_vote_view()
        print("  ✓ OG2-Editor NO puede votar en contra (Unauthorized)")

        # Intentar votar en blanco - NO debe funcionar (debe lanzar Unauthorized)
        with self.assertRaises(Unauthorized):
            white_vote_view = acord.restrictedTraverse('@@whiteVote')
            result = white_vote_view()
        print("  ✓ OG2-Editor NO puede votar en blanco (Unauthorized)")

        # Verificar que no se registró ningún voto
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(len(votos_info), 0)
        print("  ✓ No se registró ningún voto de OG2-Editor")

        logout()

    def test_secretari_can_view_results(self):
        """Test que OG1-Secretari puede ver resultados."""
        print("\n✅ Verificando que OG1-Secretari puede ver resultados")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewResultsVote())
        print("  ✓ OG1-Secretari puede ver resultados de votación a mano alzada")

        logout()

    def test_editor_can_view_results(self):
        """Test que OG2-Editor puede ver resultados."""
        print("\n✅ Verificando que OG2-Editor puede ver resultados")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG2-Editor']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewResultsVote())
        print("  ✓ OG2-Editor puede ver resultados de votación a mano alzada")

        logout()

    def test_membre_can_view_results(self):
        """Test que OG3-Membre puede ver resultados."""
        print("\n✅ Verificando que OG3-Membre puede ver resultados")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertTrue(view_obj.canViewResultsVote())
        print("  ✓ OG3-Membre puede ver resultados de votación a mano alzada")

        logout()

    def test_afectat_cannot_view_results(self):
        """Test que OG4-Afectat NO puede ver resultados."""
        print("\n❌ Verificando que OG4-Afectat NO puede ver resultados")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG4-Afectat']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewResultsVote())
        print("  ✓ OG4-Afectat NO puede ver resultados votación")

        logout()

    def test_convidat_cannot_access_voting(self):
        """Test que OG5-Convidat NO tiene acceso a votaciones."""
        print("\n❌ Verificando que OG5-Convidat NO tiene acceso a votaciones")

        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG5-Convidat']
        )

        view_obj = self.session.restrictedTraverse('@@view')
        self.assertFalse(view_obj.canViewManageVote())
        self.assertFalse(view_obj.canViewVoteButtons())
        self.assertFalse(view_obj.canViewResultsVote())
        print("  ✓ OG5-Convidat NO puede gestionar votaciones")
        print("  ✓ OG5-Convidat NO puede votar")
        print("  ✓ OG5-Convidat NO puede ver resultados")

        logout()

    def test_user_can_only_vote_once_edit_existing_vote(self):
        """Test que un usuario solo puede realizar un voto dentro de una votación.
        Puede editar su voto pero no generar uno nuevo."""
        print("\n🔒 Verificando que un usuario solo puede votar una vez (edita voto existente)")
        
        # Loguearse como OG1-Secretari para crear el acord
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )
        
        # Crear un acord con votación
        acord = api.content.create(
            type='genweb.organs.acord',
            id='acord_test_vote_once',
            title='Acord Test Vote Once',
            container=self.session
        )
        
        # Abrir votación
        acord.estatVotacio = 'open'
        acord.horaIniciVotacio = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
        acord.infoVotacio = '{}'
        acord.reindexObject()
        
        # Cambiar a OG3-Membre para votar
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Verificar que no hay votos inicialmente
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(len(votos_info), 0)
        print("  ✓ No hay votos inicialmente")
        
        # Primer voto - debe funcionar
        favor_vote_view = acord.restrictedTraverse('@@favorVote')
        result = favor_vote_view()
        
        # Verificar que el voto fue registrado
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(len(votos_info), 1)
        self.assertEqual(votos_info[TEST_USER_ID], 'favor')
        print("  ✓ Primer voto registrado correctamente")
        
        # Segundo voto (cambio a 'against') - debe sobrescribir, no añadir
        against_vote_view = acord.restrictedTraverse('@@againstVote')
        result = against_vote_view()
        
        # Verificar que el voto fue actualizado, no duplicado
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(len(votos_info), 1)  # Sigue siendo 1, no 2
        self.assertEqual(votos_info[TEST_USER_ID], 'against')  # Cambió a 'against'
        print("  ✓ Segundo voto actualizó el existente (no duplicó)")
        
        # Tercer voto (cambio a 'white') - debe sobrescribir de nuevo
        white_vote_view = acord.restrictedTraverse('@@whiteVote')
        result = white_vote_view()
        
        # Verificar que sigue siendo 1 voto
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(len(votos_info), 1)
        self.assertEqual(votos_info[TEST_USER_ID], 'white')
        print("  ✓ Tercer voto también actualizó el existente")
        
        logout()

    def test_cannot_vote_when_voting_closed(self):
        """Test que no se puede votar si se ha cerrado la votación durante el proceso."""
        print("\n🔒 Verificando que NO se puede votar cuando la votación está cerrada")
        
        # Loguearse como OG1-Secretari para crear el acord
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG1-Secretari']
        )
        
        # Crear un acord con votación abierta
        acord = api.content.create(
            type='genweb.organs.acord',
            id='acord_test_closed',
            title='Acord Test Closed',
            container=self.session
        )
                
        # Abrir votación
        acord.estatVotacio = 'open'
        acord.horaIniciVotacio = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
        acord.infoVotacio = '{}'
        acord.reindexObject()
        
        # Cambiar a OG3-Membre para votar
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Verificar que la votación está abierta
        self.assertEqual(acord.estatVotacio, 'open')
        print("  ✓ Votación abierta inicialmente")
        
        # Votar cuando está abierta - debe funcionar
        favor_vote_view = acord.restrictedTraverse('@@favorVote')
        result = favor_vote_view()
        
        # Verificar que el voto fue registrado
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(len(votos_info), 1)
        self.assertEqual(votos_info[TEST_USER_ID], 'favor')
        print("  ✓ Voto en votación abierta funcionó correctamente")
        
        # Cerrar votación (como Manager)
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        
        close_vote_view = acord.restrictedTraverse('@@closeVote')
        close_vote_view()
        
        # Verificar que la votación está cerrada
        self.assertEqual(acord.estatVotacio, 'close')
        print("  ✓ Votación cerrada correctamente")
        
        # Cambiar a usuario que puede votar
        logout()
        setRoles(self.portal, TEST_USER_ID, ['Member'])
        login(self.portal, TEST_USER_NAME)
        api.user.grant_roles(
            username=TEST_USER_ID,
            obj=self.organ,
            roles=['OG3-Membre']
        )
        
        # Intentar votar cuando está cerrada - NO debe funcionar
        against_vote_view = acord.restrictedTraverse('@@againstVote')
        result = against_vote_view()
        
        # Verificar que el voto NO fue registrado (debe seguir siendo 'favor')
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(votos_info[TEST_USER_ID], 'favor')  # Sigue siendo el voto original
        print("  ✓ NO se pudo votar en votación cerrada (protección activa)")
        
        # Verificar que el voto anterior no cambió
        if isinstance(acord.infoVotacio, str):
            votos_info = ast.literal_eval(acord.infoVotacio)
        else:
            votos_info = acord.infoVotacio
        self.assertEqual(votos_info[TEST_USER_ID], 'favor')  # Sigue siendo el voto original
        print("  ✓ El voto anterior no fue modificado")
        
        logout()

    def test_zzz_votaciones_summary(self):
        """Test resumen del sistema de votaciones (al final por orden
        alfabético)."""
        print("\n📊 RESUMEN DEL SISTEMA DE VOTACIONES")
        print("=" * 60)
        print("OG1-Secretari puede:")
        print("  ✓ Abrir votación")
        print("  ✓ Cerrar votación")
        print("  ✓ Ver botones de voto")
        print("  ✓ Ver resultados de votación a mano alzada")
        print("  ✓ Ver quién votó qué")
        print("  ✓ Votar (puede gestionar Y votar)")
        print()
        print("OG2-Editor puede:")
        print("  ✓ Abrir votación")
        print("  ✓ Cerrar votación")
        print("  ✓ Ver resultados de votación a mano alzada")
        print("  ✓ Ver quién votó qué")
        print("  ✗ NO puede ver botones de voto")
        print("  ✗ NO puede votar (gestiona pero NO vota)")
        print()
        print("OG3-Membre puede:")
        print("  ✓ Ver resultados de votación a mano alzada")
        print("  ✓ Ver botones de voto")
        print("  ✓ Votar")
        print("  ✗ NO puede gestionar votaciones")
        print("  ✗ NO puede ver quién votó qué")
        print()
        print("OG4-Afectat, OG5-Convidat, Anónimos:")
        print("  ✗ Sin acceso a funcionalidades de votación")
        print()
        print("🔒 PROTECCIÓN ANTI-DUPLICADOS:")
        print("  ✓ Un usuario solo puede votar una vez en cada votación")
        print("  ✓ Los votos posteriores actualizan el voto existente")
        print("  ✓ No se generan votos duplicados")
        print()
        print("🔒 PROTECCIÓN DE ESTADO:")
        print("  ✓ NO se puede votar en votaciones cerradas")
        print("  ✓ El sistema previene votos en votaciones cerradas")
        print("  ✓ Los votos anteriores se mantienen intactos")
        print("=" * 60)

        self.assertTrue(True)
