# -*- coding: utf-8 -*-

from plone import api
from Products.CMFPlone.interfaces import INonInstallable
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from zope.interface import implementer

import logging

logger = logging.getLogger(__name__)

NEW_INDEXES = [('estatAprovacio', 'FieldIndex'),
               ('dataSessio', 'DateIndex'),
               ('serie', 'FieldIndex')]


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "genweb6.organs:uninstall",
        ]

    def getNonInstallableProducts(self):
        """Hide the upgrades package from site-creation and quickinstaller."""
        return ["genweb6.organs.upgrades"]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def add_catalog_indexes(catalog):
    indexables = []
    indexes = catalog.indexes()
    for name, meta_type in NEW_INDEXES:
        if name not in indexes:
            catalog.addIndex(name, meta_type)
            indexables.append(name)
    if len(indexables) > 0:
        catalog.manage_reindexIndex(ids=indexables)


def setup_ldapupc_properties_plugin(site):
    """
    Activa ldapUPC com a IPropertiesPlugin i el posa el primer.
    Si no, member.getProperty('email') no funciona (correus de votació).
    Cal perquè la reinstal·lació de genweb6.upc recrea ldapUPC sense
    aquesta interfície activada.
    """
    acl_users = site.acl_users
    if 'ldapUPC' not in acl_users.objectIds():
        logger.warning('ldapUPC no existeix: no es configura IPropertiesPlugin')
        return

    plugins = acl_users.plugins
    if 'ldapUPC' not in plugins.listPluginIds(IPropertiesPlugin):
        plugins.activatePlugin(IPropertiesPlugin, 'ldapUPC')
    plugins.movePluginsTop(IPropertiesPlugin, ['ldapUPC'])
    logger.info('ldapUPC activat i primer a IPropertiesPlugin')


# def disable_acquire_permission(site):
#     """
#     Desactiva Acquire del permiso 'Access contents information' en objetos
#     sensibles. Esto evita que usuarios anónimos puedan acceder a información
#     sensible pero permite el acceso a Manager.

#     Args:
#         site: portal site
#     """
#     permission = "Access contents information"
#     object_names = [
#         'acl_users', 'portal_actions', 'portal_memberdata', 'portal_modifier',
#         'portal_purgepolicy', 'portal_referencefactories', 'portal_skins',
#         'portal_transforms', 'portal_types']

#     for object_name in object_names:
#         try:
#             obj = getattr(site, object_name)

#             # Desactivar adquisición del permiso pero mantener acceso para Manager
#             # manage_permission(permission, roles, acquire)
#             # roles=['Manager'] → acceso limitado
#             # acquire=0 → NO hereda del padre (evita acceso anónimo)
#             obj.manage_permission(
#                 permission,
#                 roles=['Manager'],
#                 acquire=0
#             )

#             msg = (f"🔒 Acquire deshabilitado para '{permission}' "
#                    f"en {object_name}")
#             print(f"{msg} (acceso solo Manager)")
#         except Exception as e:
#             print(f"⚠️ Error deshabilitando Acquire en {object_name}: {e}")


def setupVarious(context):
    if context.readDataFile('genweb6.organs_various.txt') is None:
        return

    catalog = api.portal.get_tool("portal_catalog")
    add_catalog_indexes(catalog)
    setup_ldapupc_properties_plugin(api.portal.get())
    # site = api.portal.get()
    # disable_acquire_permission(site)
