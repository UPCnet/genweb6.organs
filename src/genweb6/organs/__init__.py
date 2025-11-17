"""Init and utils."""
from plone.protect.monkey import marmoset_patch
from zope.i18nmessageid import MessageFactory

from genweb6.core.portlets.navigation.navigation import buildFolderTree
from genweb6.organs.navigation_patched import customBuildFolderTree

_ = MessageFactory('genweb6.organs')
_GW = MessageFactory('genweb')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    pass


marmoset_patch(buildFolderTree, customBuildFolderTree)