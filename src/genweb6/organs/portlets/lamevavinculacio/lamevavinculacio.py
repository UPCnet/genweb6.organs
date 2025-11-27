# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone import api
from plone.app.portlets.portlets import base
from plone.memoize import instance
from plone.portlets.interfaces import IPortletDataProvider
from zope.interface import implementer

from genweb6.organs import _
from genweb6.organs import utils


class ILaMevaVinculacioOrgansPortlet(IPortletDataProvider):
    """A portlet displaying a organs linked with me
    """


@implementer(ILaMevaVinculacioOrgansPortlet)
class Assignment(base.Assignment):
    title = _(u'Organs La Meva Vinculació')


class Renderer(base.Renderer):
    render = ViewPageTemplateFile('lamevavinculacio.pt')

    @instance.memoize
    def getOwnOrgans(self):
        """Get organs linked to current user.

        OPTIMIZATION: Request-level cache to avoid repeated calls per page load.
        The portlet is rendered multiple times in a single request.
        """
        if not api.user.is_anonymous():
            results = []
            portal_catalog = api.portal.get_tool(name='portal_catalog')
            root_path = '/'.join(api.portal.get().getPhysicalPath())
            lt = getToolByName(self, 'portal_languages')
            lang = lt.getPreferredLanguage()
            values = portal_catalog.searchResults(
                portal_type=['genweb.organs.organgovern'],
                path=root_path + '/' + lang,
                sort_on='sortable_title')
            username = api.user.get_current().id

            for obj in values:
                # NOTE: No se puede optimizar más - api.user.get_roles() necesita
                # el objeto real para leer roles locales (no están en metadata)
                organ = obj._unrestrictedGetObject()

                all_roles = api.user.get_roles(username=username, obj=organ)
                roles = [o for o in all_roles if o in [
                    'OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                    'OG4-Afectat', 'OG5-Convidat']]

                if roles:
                    results.append(dict(
                        url=obj.getURL(),  # ← Metadata del brain (no doble getObject)
                        title=obj.Title,   # ← Metadata del brain
                        color=getattr(organ, 'eventsColor', '#007bc0') or '#007bc0',
                        role=roles))

            return results


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
