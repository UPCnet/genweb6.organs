# -*- coding: utf-8 -*-
"""REGRESSION TEST: api.user.get_roles() necesita objeto real, no brain.

BUG ORIGINAL (2025-11-27):
En getOwnOrgans() se intentó optimizar usando api.user.get_roles(obj=brain)
pero los roles locales NO están en la metadata del catálogo.

Este test verifica que getOwnOrgans() devuelve correctamente los órganos
donde el usuario tiene roles locales asignados.
"""
import unittest
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from plone import api
from zope.component import getMultiAdapter
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
import warnings

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


class TestSearchOwnOrgansRegression(unittest.TestCase):
    """REGRESSION: Verificar que getOwnOrgans() detecta roles locales."""

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING

    def setUp(self):
        """Configurar entorno de test igual que test_create_sessions.py."""
        # Suprimir warnings
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        # Create default GW directories (CLAVE!)
        setupview = getMultiAdapter(
            (self.portal, self.request),
            name='setup-view'
        )
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()

        # IMPORTANTE: Configurar idioma por defecto a 'ca'
        # (por defecto es 'en' pero los tests crean contenido en 'ca')
        from zope.component import getUtility
        from plone.registry.interfaces import IRegistry
        registry = getUtility(IRegistry)
        registry['plone.default_language'] = 'ca'

        # Enable the possibility to add Organs folder
        behavior = ISelectableConstrainTypes(self.portal['ca'])
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(['genweb.organs.organsfolder'])
        behavior.setImmediatelyAddableTypes(['genweb.organs.organsfolder'])

        # Create Organs Test Folder
        try:
            api.content.delete(
                obj=self.portal['ca']['testingfolder'],
                check_linkintegrity=False
            )
        except Exception:
            pass

        og_unit = api.content.create(
            type='genweb.organs.organsfolder',
            id='testingfolder',
            title='Organ Tests',
            container=self.portal['ca']
        )

        # Create test organs
        self.organ1 = api.content.create(
            type='genweb.organs.organgovern',
            id='test-organ-1',
            title='Test Organ 1',
            container=og_unit,
            safe_id=True
        )
        self.organ1.eventsColor = '#ff0000'
        self.organ1.reindexObject()

        self.organ2 = api.content.create(
            type='genweb.organs.organgovern',
            id='test-organ-2',
            title='Test Organ 2',
            container=og_unit,
            safe_id=True
        )
        self.organ2.eventsColor = '#00ff00'
        self.organ2.reindexObject()

        self.organ3 = api.content.create(
            type='genweb.organs.organgovern',
            id='test-organ-3',
            title='Test Organ 3',
            container=og_unit,
            safe_id=True
        )
        self.organ3.reindexObject()

        # IMPORTANTE: Commit para que el catálogo se actualice
        import transaction
        transaction.commit()

        # Create test users
        self.secretari = api.user.create(
            email='secretari@test.com',
            username='secretari',
            password='secret123'
        )

        self.editor = api.user.create(
            email='editor@test.com',
            username='editor',
            password='secret123'
        )

        self.membre = api.user.create(
            email='membre@test.com',
            username='membre',
            password='secret123'
        )

        self.no_roles_user = api.user.create(
            email='noroles@test.com',
            username='noroles',
            password='secret123'
        )

        logout()

    def _assign_local_roles(self, obj, user_id, roles):
        """Asignar roles locales a un usuario."""
        obj.manage_setLocalRoles(user_id, roles)
        obj.reindexObjectSecurity()

    def test_anonymous_sees_no_organs(self):
        """Usuario anónimo no ve órganos."""
        print("\n❌ Verificando restricciones para usuario anónimo")

        # Usuario anónimo (sin login)
        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        print("  ✓ Usuario anónimo no ve órganos")
        self.assertEqual(len(own_organs), 0,
                         "Anónimo no debe ver órganos")

        print("  ✓ Verificación completa para usuario anónimo")

    def test_user_without_roles_sees_no_organs(self):
        """Usuario sin roles locales no ve órganos."""
        print("\n❌ Verificando restricciones para usuario sin roles")

        login(self.portal, 'noroles')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        print("  ✓ Usuario sin roles no ve órganos")
        self.assertEqual(len(own_organs), 0,
                         "Usuario sin roles no debe ver órganos")

        print("  ✓ Verificación completa para usuario sin roles")

    def test_secretari_sees_assigned_organ(self):
        """REGRESSION: Secretari con rol local ve su órgano.

        Este es el test principal que detecta el bug:
        - Si se usa brain: NO encuentra el órgano
        - Si se usa objeto: SÍ encuentra el órgano
        """
        print("\n✅ Verificando permisos del rol OG1-Secretari")

        # Asignar rol local de Secretari en organ1
        self._assign_local_roles(self.organ1, 'secretari', ['OG1-Secretari'])

        login(self.portal, 'secretari')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        # DEBE ver 1 órgano
        print("  ✓ Secretari ve el órgano donde tiene rol asignado")
        self.assertEqual(len(own_organs), 1,
                         "Secretari debe ver el órgano donde tiene rol")

        # Verificar datos del órgano
        organ_data = own_organs[0]
        self.assertIn('test-organ-1', organ_data['url'])
        self.assertEqual(organ_data['title'], 'Test Organ 1')
        self.assertEqual(organ_data['color'], '#ff0000')
        self.assertIn('OG1-Secretari', organ_data['role'])

        print("  ✓ Datos del órgano correctos (título, color, rol)")
        print("  ✓ Verificación completa como OG1-Secretari")

    def test_editor_sees_multiple_organs(self):
        """Editor con roles en múltiples órganos los ve todos."""
        print("\n✅ Verificando permisos del rol OG2-Editor (múltiples órganos)")

        # Asignar rol de Editor en organ1 y organ2
        self._assign_local_roles(self.organ1, 'editor', ['OG2-Editor'])
        self._assign_local_roles(self.organ2, 'editor', ['OG2-Editor'])

        login(self.portal, 'editor')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        # DEBE ver 2 órganos
        print("  ✓ Editor ve los 2 órganos donde tiene rol")
        self.assertEqual(len(own_organs), 2,
                         "Editor debe ver ambos órganos")

        # Verificar que están ambos
        organ_titles = [o['title'] for o in own_organs]
        self.assertIn('Test Organ 1', organ_titles)
        self.assertIn('Test Organ 2', organ_titles)

        print("  ✓ Ambos órganos devueltos correctamente")
        print("  ✓ Verificación completa como OG2-Editor")

    def test_membre_sees_assigned_organ(self):
        """Membre con rol local ve su órgano."""
        print("\n✅ Verificando permisos del rol OG3-Membre")

        self._assign_local_roles(self.organ3, 'membre', ['OG3-Membre'])

        login(self.portal, 'membre')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        print("  ✓ Membre ve el órgano donde tiene rol")
        self.assertEqual(len(own_organs), 1)
        self.assertIn('test-organ-3', own_organs[0]['url'])

        print("  ✓ Verificación completa como OG3-Membre")

    def test_user_with_multiple_roles_in_same_organ(self):
        """Usuario con múltiples roles en mismo órgano."""
        print("\n✅ Verificando usuario con múltiples roles (Secretari + Editor + Membre)")

        # Asignar múltiples roles
        self._assign_local_roles(
            self.organ1,
            'secretari',
            ['OG1-Secretari', 'OG2-Editor', 'OG3-Membre']
        )

        login(self.portal, 'secretari')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        print("  ✓ Usuario ve el órgano (1 órgano)")
        self.assertEqual(len(own_organs), 1)

        # Verificar que tiene todos los roles
        roles = own_organs[0]['role']
        self.assertIn('OG1-Secretari', roles)
        self.assertIn('OG2-Editor', roles)
        self.assertIn('OG3-Membre', roles)

        print("  ✓ Todos los roles devueltos correctamente (Secretari, Editor, Membre)")
        print("  ✓ Verificación completa para usuario con múltiples roles")

    def test_organ_without_events_color_has_default(self):
        """Órgano sin eventsColor usa color por defecto."""
        print("\n✅ Verificando color por defecto para órgano sin eventsColor")

        # organ3 no tiene eventsColor configurado
        self._assign_local_roles(self.organ3, 'secretari', ['OG1-Secretari'])

        login(self.portal, 'secretari')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        # Debe tener color por defecto
        print("  ✓ Órgano sin eventsColor usa color por defecto (#007bc0)")
        self.assertEqual(own_organs[0]['color'], '#007bc0')

        print("  ✓ Verificación completa de color por defecto")

    def test_organs_sorted_alphabetically(self):
        """Los órganos se devuelven ordenados alfabéticamente."""
        print("\n✅ Verificando orden alfabético de órganos")

        # Asignar roles en todos los órganos
        self._assign_local_roles(self.organ1, 'secretari', ['OG1-Secretari'])
        self._assign_local_roles(self.organ2, 'secretari', ['OG1-Secretari'])
        self._assign_local_roles(self.organ3, 'secretari', ['OG1-Secretari'])

        login(self.portal, 'secretari')

        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )

        own_organs = view.getOwnOrgans()

        # Verificar orden alfabético
        titles = [o['title'] for o in own_organs]
        print(f"  ✓ Órganos devueltos en orden alfabético: {titles}")
        self.assertEqual(titles, sorted(titles),
                         "Órganos deben estar ordenados alfabéticamente")

        print("  ✓ Verificación completa de orden alfabético")

    def test_regression_brain_vs_object_for_roles(self):
        """REGRESSION TEST: Demostrar diferencia entre brain y objeto.

        Este test demuestra técnicamente por qué getObject() es necesario.
        """
        print("\n🐛 REGRESSION TEST: Brain vs Objeto para roles locales")
        print("=" * 70)

        # Asignar rol local
        self._assign_local_roles(self.organ1, 'secretari', ['OG1-Secretari'])

        login(self.portal, 'secretari')

        # Obtener brain del catálogo
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='genweb.organs.organgovern',
            id='test-organ-1'
        )
        self.assertEqual(len(brains), 1)
        brain = brains[0]

        # ❌ Brain NO tiene roles locales
        print("\n  ❌ Probando api.user.get_roles() con BRAIN del catálogo:")
        roles_from_brain = api.user.get_roles(username='secretari', obj=brain)
        print(f"     Roles devueltos: {roles_from_brain}")
        self.assertNotIn('OG1-Secretari', roles_from_brain,
                         "Brain NO debe tener roles locales (bug esperado)")
        print("     ✓ Brain NO tiene roles locales (comportamiento esperado)")

        # ✅ Objeto real SÍ tiene roles locales
        print("\n  ✅ Probando api.user.get_roles() con OBJETO REAL:")
        organ = brain._unrestrictedGetObject()
        roles_from_object = api.user.get_roles(username='secretari', obj=organ)
        print(f"     Roles devueltos: {roles_from_object}")
        self.assertIn('OG1-Secretari', roles_from_object,
                      "Objeto real DEBE tener roles locales")
        print("     ✓ Objeto real SÍ tiene roles locales (correcto)")

        # Verificar que getOwnOrgans() usa objeto real (no brain)
        print("\n  🔍 Verificando que getOwnOrgans() usa objeto real:")
        view = api.content.get_view(
            name='search',
            context=self.portal,
            request=self.request
        )
        own_organs = view.getOwnOrgans()

        # Si usa brain: NO encuentra nada (bug)
        # Si usa objeto: SÍ encuentra 1 órgano (correcto)
        print(f"     Órganos encontrados: {len(own_organs)}")
        self.assertEqual(len(own_organs), 1,
                         "getOwnOrgans() DEBE usar objeto real, no brain")
        self.assertIn('OG1-Secretari', own_organs[0]['role'],
                      "Debe devolver el rol local correctamente")
        print("     ✓ getOwnOrgans() usa objeto real correctamente")

        print("\n  ✅ REGRESSION TEST PASADO: Bug de brain vs objeto no ocurre")
        print("=" * 70)
