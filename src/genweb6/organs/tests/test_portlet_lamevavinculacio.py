# -*- coding: utf-8 -*-
"""Test del portlet La Meva Vinculació.

REGRESSION TEST: Verifica que el portlet usa correctamente getObject()
para obtener roles locales, igual que search.py.

El portlet debe:
1. Usar obj._unrestrictedGetObject() para roles
2. Usar obj.getURL() para la URL (metadata)
3. Manejar eventsColor = None correctamente
"""
import unittest
import warnings
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout, setRoles
from plone import api
from zope.component import getMultiAdapter
from Products.CMFPlone.interfaces import ISelectableConstrainTypes

from genweb6.organs.testing import GENWEB6_ORGANS_INTEGRATION_TESTING


class TestPortletLaMevaVinculacio(unittest.TestCase):
    """Test de regresión para portlet La Meva Vinculació."""

    layer = GENWEB6_ORGANS_INTEGRATION_TESTING

    def setUp(self):
        """Configurar entorno de test."""
        # Suprimir warnings
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_portlet_code_uses_getobject_for_roles(self):
        """REGRESSION: Verificar que el código del portlet usa getObject().

        Este test verifica el código fuente del portlet en lugar de ejecutarlo,
        para asegurar que usa el patrón correcto de brain vs objeto.
        """
        print("\n🐛 REGRESSION TEST: Código del portlet usa objeto real")

        import inspect
        from genweb6.organs.portlets.lamevavinculacio.lamevavinculacio import Renderer

        # Obtener código fuente
        source = inspect.getsource(Renderer.getOwnOrgans)

        # Verificar que hace getObject() ANTES de get_roles()
        print("  ✓ Verificando que hace _unrestrictedGetObject()...")
        self.assertIn('_unrestrictedGetObject()', source,
                      "Debe hacer getObject() del brain")

        print("  ✓ Verificando que llama api.user.get_roles() con objeto...")
        self.assertIn('api.user.get_roles(username=username, obj=organ)', source,
                      "Debe usar 'organ' (objeto) no 'obj' (brain)")

        # Verificar optimizaciones
        print("  ✓ Verificando que usa obj.getURL() (metadata)...")
        self.assertIn('obj.getURL()', source,
                      "Debe usar getURL() (metadata) no getObject().absolute_url()")

        print("  ✓ Verificando que usa obj.Title (metadata)...")
        self.assertIn('obj.Title', source,
                      "Debe usar Title (metadata) no getObject().Title()")

        # Verificar protección contra None
        print("  ✓ Verificando protección contra eventsColor = None...")
        self.assertIn("or '#007bc0'", source,
                      "Debe tener protección contra eventsColor None")

        print("\n  ✅ REGRESSION TEST PASADO: Código del portlet correcto")
        print("     - Usa _unrestrictedGetObject() para roles")
        print("     - Usa metadata del brain (getURL, Title)")
        print("     - Protege contra eventsColor = None")

    def test_portlet_code_matches_search_pattern(self):
        """Verificar que portlet y search.py usan el mismo patrón."""
        print("\n🔍 Verificando consistencia entre portlet y search.py")

        import inspect
        from genweb6.organs.portlets.lamevavinculacio.lamevavinculacio import Renderer as PortletRenderer
        from genweb6.organs.browser.search.search import Search

        # Obtener código fuente de ambos
        portlet_source = inspect.getsource(PortletRenderer.getOwnOrgans)
        search_source = inspect.getsource(Search.getOwnOrgans)

        # Verificar patrones comunes
        patterns = [
            '_unrestrictedGetObject()',
            'api.user.get_roles(username=username, obj=organ)',
            'obj.getURL()',
            'obj.Title',
            "or '#007bc0'",
        ]

        for pattern in patterns:
            portlet_has = pattern in portlet_source
            search_has = pattern in search_source

            print(f"  ✓ Patrón '{pattern}': Portlet={portlet_has}, Search={search_has}")
            self.assertEqual(portlet_has, search_has,
                             f"Portlet y Search deben usar el mismo patrón: {pattern}")

        print("\n  ✅ Portlet y Search usan patrones consistentes")

    def test_portlet_code_does_not_double_getobject(self):
        """Verificar que portlet no hace doble getObject()."""
        print("\n⚡ Verificando que portlet no hace doble getObject()")

        import inspect
        from genweb6.organs.portlets.lamevavinculacio.lamevavinculacio import Renderer

        source = inspect.getsource(Renderer.getOwnOrgans)

        # NO debe tener obj.getObject().absolute_url()
        print("  ✓ Verificando que NO usa obj.getObject().absolute_url()...")
        self.assertNotIn('obj.getObject().absolute_url()', source,
                         "No debe hacer doble getObject() - usar obj.getURL()")

        # NO debe tener obj.getObject().Title()
        print("  ✓ Verificando que NO usa obj.getObject().Title()...")
        self.assertNotIn('obj.getObject().Title()', source,
                         "No debe hacer getObject() para Title - usar obj.Title")

        print("\n  ✅ Portlet optimizado correctamente: sin doble getObject()")
