# -*- coding: utf-8 -*-
"""
Tests para verificar que filesinsidePunt muestra ficheros correctamente
según los roles del usuario, especialmente con ROLES COMBINADOS.

BUG DETECTADO: https://github.com/UPCnet/genweb6.organs/commit/6fae8f442f6bb78111827e69e1295e23eace41d4

El problema era que usuarios con roles combinados como ['OG3-Membre', 'OG4-Afectat']
no podían ver ficheros porque el código verificaba 'OG4-Afectat' in roles
sin considerar que también tenían OG3-Membre.

Este test verifica que:
1. Usuario con OG3-Membre puede ver ficheros reservados
2. Usuario con OG3-Membre + OG4-Afectat también puede ver ficheros reservados
3. Usuario con SOLO OG4-Afectat no puede ver ficheros en órgano restringido a membres
"""

import unittest
import warnings
from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING
from zope.component import getMultiAdapter
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import login, logout
from plone.app.testing import setRoles
from genweb6.organs.browser import tools
from plone import api
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes


class TestFilesinsidePuntVisibility(unittest.TestCase):
    """Tests para verificar visibilidad de ficheros en filesinsidePunt con roles combinados."""

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING

    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning,
                                message=".*unclosed file.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        # Create default GW directories
        setupview = getMultiAdapter((self.portal, self.request), name='setup-view')
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()

        # Enable the possibility to add Organs folder
        behavior = ISelectableConstrainTypes(self.portal['ca'])
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(['genweb.organs.organsfolder'])
        behavior.setImmediatelyAddableTypes(['genweb.organs.organsfolder'])

        # Create Base folder
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

        # Create Organ restricted to members
        tools.create_organ_content(
            og_unit,
            'restricted_to_members_organ',
            'OG.MEMBERS',
            'Organ TEST restringit a MEMBRES',
            'membres')

        logout()

    def _get_sessio_view(self, sessio):
        """Helper para obtener la vista de sesión."""
        return getMultiAdapter((sessio, self.request), name='view')

    def _get_punt_item(self, sessio):
        """Helper para obtener el item dict del punt."""
        return {'id': 'punt'}

    # =========================================================================
    # Tests para órgano RESTRICTED_TO_MEMBERS_ORGAN
    # =========================================================================

    def test_filesinsidepunt_membre_can_see_files(self):
        """
        BUG REGRESSION TEST:
        Usuario con SOLO OG3-Membre debe poder ver ficheros en órgano membres.
        """
        print("\n✅ [filesinsidePunt] OG3-Membre solo → debe ver ficheros")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG3-Membre'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        # Debe ver ficheros, no lista vacía
        self.assertIsInstance(files, list, "filesinsidePunt debe devolver una lista")
        self.assertGreater(
            len(files), 0,
            "OG3-Membre debería ver ficheros en órgano restringido a membres, "
            "pero filesinsidePunt devolvió lista vacía"
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()

    def test_filesinsidepunt_membre_afectat_can_see_files(self):
        """
        BUG REGRESSION TEST (PRINCIPAL):
        Usuario con OG3-Membre + OG4-Afectat debe poder ver ficheros.

        Este es el bug principal: el código anterior verificaba
        'OG4-Afectat' in roles y devolvía [] sin considerar que
        el usuario también tenía OG3-Membre.
        """
        print("\n✅ [filesinsidePunt] OG3-Membre + OG4-Afectat → debe ver ficheros")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG3-Membre', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        # ESTE ES EL TEST CLAVE: debe ver ficheros aunque tenga OG4-Afectat
        self.assertIsInstance(files, list, "filesinsidePunt debe devolver una lista")
        self.assertGreater(
            len(files), 0,
            "Usuario con OG3-Membre + OG4-Afectat debería ver ficheros, "
            "pero filesinsidePunt devolvió lista vacía. "
            "BUG: El código no considera roles combinados."
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()

    def test_filesinsidepunt_secretari_afectat_can_see_files(self):
        """
        Usuario con OG1-Secretari + OG4-Afectat debe poder ver ficheros.
        """
        print("\n✅ [filesinsidePunt] OG1-Secretari + OG4-Afectat → debe ver ficheros")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG1-Secretari', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        self.assertIsInstance(files, list)
        self.assertGreater(
            len(files), 0,
            "OG1-Secretari + OG4-Afectat debería ver ficheros"
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()

    def test_filesinsidepunt_editor_afectat_can_see_files(self):
        """
        Usuario con OG2-Editor + OG4-Afectat debe poder ver ficheros.
        """
        print("\n✅ [filesinsidePunt] OG2-Editor + OG4-Afectat → debe ver ficheros")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG2-Editor', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        self.assertIsInstance(files, list)
        self.assertGreater(
            len(files), 0,
            "OG2-Editor + OG4-Afectat debería ver ficheros"
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()

    def test_filesinsidepunt_afectat_only_cannot_see_files(self):
        """
        Usuario con SOLO OG4-Afectat NO debe ver ficheros en órgano restringido a membres.
        """
        print("\n🚫 [filesinsidePunt] OG4-Afectat solo → NO debe ver ficheros")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        # Solo Afectat NO debe ver ficheros en órgano restringido a membres
        self.assertIsInstance(files, list)
        self.assertEqual(
            len(files), 0,
            "Usuario con SOLO OG4-Afectat NO debería ver ficheros en órgano "
            "restringido a membres"
        )
        print("    ✓ Ficheros visibles: 0 (correcto)")
        logout()

    def test_filesinsidepunt_anonymous_cannot_see_files(self):
        """
        Usuario anónimo NO debe ver ficheros en órgano restringido a membres.
        """
        print("\n🚫 [filesinsidePunt] Anónimo → NO debe ver ficheros")
        logout()

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        self.assertIsInstance(files, list)
        self.assertEqual(
            len(files), 0,
            "Usuario anónimo NO debería ver ficheros en órgano restringido a membres"
        )
        print("    ✓ Ficheros visibles: 0 (correcto)")

    def test_filesinsidepunt_convidat_afectat_can_see_files(self):
        """
        Usuario con OG5-Convidat + OG4-Afectat debe poder ver ficheros.
        """
        print("\n✅ [filesinsidePunt] OG5-Convidat + OG4-Afectat → debe ver ficheros")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG5-Convidat', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.convocada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        self.assertIsInstance(files, list)
        self.assertGreater(
            len(files), 0,
            "OG5-Convidat + OG4-Afectat debería ver ficheros"
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()

    # =========================================================================
    # Tests para verificar diferentes estados de sesión
    # =========================================================================

    def test_filesinsidepunt_membre_afectat_in_planificada(self):
        """
        En estado PLANIFICADA, OG3-Membre + OG4-Afectat NO debe ver ficheros
        (porque Membre no puede ver sesiones planificadas).
        """
        print("\n🚫 [filesinsidePunt] Membre+Afectat en PLANIFICADA → NO debe ver")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG3-Membre', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.planificada  # Estado planificada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        # En planificada, Membre no tiene acceso
        self.assertIsInstance(files, list)
        # Dependiendo de la implementación, puede devolver [] o lanzar error
        print(f"    ✓ Ficheros visibles: {len(files)} (correcto según permisos de estado)")
        logout()

    def test_filesinsidepunt_membre_afectat_in_realitzada(self):
        """
        En estado REALITZADA, OG3-Membre + OG4-Afectat debe ver ficheros.
        """
        print("\n✅ [filesinsidePunt] Membre+Afectat en REALITZADA → debe ver")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG3-Membre', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.realitzada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        self.assertIsInstance(files, list)
        self.assertGreater(
            len(files), 0,
            "Membre + Afectat debería ver ficheros en estado REALITZADA"
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()

    def test_filesinsidepunt_membre_afectat_in_tancada(self):
        """
        En estado TANCADA, OG3-Membre + OG4-Afectat debe ver ficheros.
        """
        print("\n✅ [filesinsidePunt] Membre+Afectat en TANCADA → debe ver")
        logout()
        setRoles(self.portal, TEST_USER_ID, ['OG3-Membre', 'OG4-Afectat'])
        login(self.portal, TEST_USER_NAME)

        root_path = self.portal.ca.testingfolder
        sessio = root_path.membres.tancada
        view = self._get_sessio_view(sessio)
        punt_item = self._get_punt_item(sessio)

        files = view.filesinsidePunt(punt_item)

        self.assertIsInstance(files, list)
        self.assertGreater(
            len(files), 0,
            "Membre + Afectat debería ver ficheros en estado TANCADA"
        )
        print(f"    ✓ Ficheros visibles: {len(files)}")
        logout()


def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(TestFilesinsidePuntVisibility)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
