# -*- coding: utf-8 -*-
"""ldapUPC ha d'estar actiu i el primer a IPropertiesPlugin.

Si no, member.getProperty('email') no retorna l'email de l'LDAP i els
correus de votació no s'envien (sendVoteEmail surt si no hi ha email).
No cal xarxa: només es crea el plugin, no s'hi connecta.
"""
from unittest import mock

import unittest

from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin

from genweb6.organs.setuphandlers import setup_ldapupc_properties_plugin
from genweb6.organs.tests.base import OrgansFunctionalTestCase


try:
    from genweb6.core.browser.helpers import helpers_ldap
    HAS_LDAP = helpers_ldap.HAS_LDAP
except ImportError:  # pragma: no cover
    HAS_LDAP = False

if HAS_LDAP:
    # Registra el 'LDAP delegate'. A la instància ho fa la inicialització de
    # Zope; a la capa de test no, i sense això LDAPUserFolder no es pot crear
    # (setSetupLDAPUPC s'empassa l'error i deixa un ldapUPC a mitges).
    import Products.LDAPUserFolder.LDAPDelegate  # noqa: F401


def create_ldapupc(bind_password=''):
    """Crea ldapUPC amb el mateix codi que producció (genweb6.core)."""
    with mock.patch.object(helpers_ldap, 'LDAP_PASSWORD', bind_password):
        helpers_ldap.setSetupLDAPUPC()


def inner_ldap_folder(portal):
    """LDAPUserFolder intern de ldapUPC (sense adquisició)."""
    from Acquisition import aq_base
    return aq_base(portal.acl_users.ldapUPC).__dict__.get('acl_users')


@unittest.skipUnless(HAS_LDAP, 'Products.PloneLDAP no instal·lat')
class LdapPropertiesPluginTestCase(OrgansFunctionalTestCase):

    def plugins(self):
        return self.portal.acl_users.plugins

    def test_ldapupc_created(self):
        """ldapUPC complet: amb el seu LDAPUserFolder intern ben configurat."""
        from Products.LDAPUserFolder.LDAPUserFolder import LDAPUserFolder
        create_ldapupc()
        self.assertIn('ldapUPC', self.portal.acl_users.objectIds())
        luf = inner_ldap_folder(self.portal)
        self.assertIsInstance(luf, LDAPUserFolder)
        self.assertEqual(luf.users_base, 'ou=Users,dc=upc,dc=edu')
        self.assertEqual([s['host'] for s in luf.getServers()], ['ldap.upc.edu'])

    def test_setup_activates_and_moves_top(self):
        create_ldapupc()
        # Situació que provoca el problema: ldapUPC no actiu com a properties
        if 'ldapUPC' in self.plugins().listPluginIds(IPropertiesPlugin):
            self.plugins().deactivatePlugin(IPropertiesPlugin, 'ldapUPC')
        self.assertNotIn('ldapUPC', self.plugins().listPluginIds(IPropertiesPlugin))

        setup_ldapupc_properties_plugin(self.portal)

        ids = self.plugins().listPluginIds(IPropertiesPlugin)
        self.assertEqual(ids[0], 'ldapUPC')

    def test_setup_moves_existing_plugin_to_top(self):
        create_ldapupc()
        setup_ldapupc_properties_plugin(self.portal)
        self.plugins().movePluginsDown(IPropertiesPlugin, ['ldapUPC'])
        self.assertNotEqual(self.plugins().listPluginIds(IPropertiesPlugin)[0], 'ldapUPC')

        setup_ldapupc_properties_plugin(self.portal)
        self.assertEqual(self.plugins().listPluginIds(IPropertiesPlugin)[0], 'ldapUPC')

    def test_setup_idempotent(self):
        create_ldapupc()
        setup_ldapupc_properties_plugin(self.portal)
        setup_ldapupc_properties_plugin(self.portal)
        ids = self.plugins().listPluginIds(IPropertiesPlugin)
        self.assertEqual(ids[0], 'ldapUPC')
        self.assertEqual(ids.count('ldapUPC'), 1)

    def test_setup_without_ldapupc_does_nothing(self):
        if 'ldapUPC' in self.portal.acl_users.objectIds():
            self.portal.acl_users.manage_delObjects(['ldapUPC'])
        before = self.plugins().listPluginIds(IPropertiesPlugin)
        setup_ldapupc_properties_plugin(self.portal)
        self.assertEqual(self.plugins().listPluginIds(IPropertiesPlugin), before)

    def test_profile_setup_various_configures_ldapupc(self):
        """Reinstal·lar genweb6.upc recrea ldapUPC sense IPropertiesPlugin;
        el setupVarious del perfil de genweb6.organs l'ha de deixar el primer."""
        from genweb6.organs import setuphandlers

        create_ldapupc()
        if 'ldapUPC' in self.plugins().listPluginIds(IPropertiesPlugin):
            self.plugins().deactivatePlugin(IPropertiesPlugin, 'ldapUPC')

        class _ProfileContext(object):
            def readDataFile(self, filename):
                return 'marker'

        setuphandlers.setupVarious(_ProfileContext())
        self.assertEqual(self.plugins().listPluginIds(IPropertiesPlugin)[0], 'ldapUPC')
