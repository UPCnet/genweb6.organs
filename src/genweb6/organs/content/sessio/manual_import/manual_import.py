# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from Products.statusmessages.interfaces import IStatusMessage

from plone import api
from Products.Five.browser import BrowserView

from genweb6.organs import _
from genweb6.organs.content.sessio.sessio import ISessio
from genweb6.organs.interfaces import IGenweb6OrgansLayer
from genweb6.organs.utils import addEntryLog
from genweb6.organs import utils

import transaction
import unicodedata


class ManualImport(BrowserView):
    """ Browser view for manual structure creation
    """

    def __call__(self):
        """ Process the form submission """
        # Check permissions
        migrated_property = hasattr(self.context, 'migrated')
        if migrated_property and self.context.migrated is True:
            raise Unauthorized

        try:
            username = api.user.get_current().id
            roles = api.user.get_roles(username=username, obj=self.context)
            if not utils.checkhasRol(['Manager', 'OG1-Secretari', 'OG2-Editor'], roles):
                raise Unauthorized
        except:
            raise Unauthorized

        # Get form data
        message = self.request.form.get('form.widgets.message', '')
        action = self.request.form.get('form.buttons.send', '')

        if action == 'Cancel·la' or not action:
            message = _(u"Operation Cancelled.")
            IStatusMessage(self.request).addStatusMessage(message, type="warning")
            return self.request.response.redirect(self.context.absolute_url())

        if not message or message.strip() == '':
            message = 'Falten els valors dels punts. Cap canvi realitzat.'
            lang = self.context.language
            if lang == 'es':
                message = "Faltan los valores de los puntos. No se ha realizado ningún cambio."
            if lang == 'en':
                message = "Required values missing. No changes made."
            IStatusMessage(self.request).addStatusMessage(message, type="error")
            return self.request.response.redirect(self.context.absolute_url())

        """ Adding message information to context in annotation format """
        addEntryLog(self.context, None, _(u'Massive agreements imported'), '')

        # Creating new objects
        text = message

        # OPTIMIZATION: Cachear órgano y estado por defecto
        organ = utils.get_organ(self.context)

        values = organ.estatsLlista
        if hasattr(values, 'raw'):
            values = values.raw
        value = values.split('</p>')[0]
        item_net = unicodedata.normalize("NFKD", value).rstrip(
            ' ').replace('<p>', '').replace('</p>', '').replace('\r\n', '')
        defaultEstat = ' '.join(item_net.split()[:-1]).lstrip()

        # OPTIMIZATION: Cachear catalog y folder_path
        portal_catalog = api.portal.get_tool(name='portal_catalog')
        folder_path = '/'.join(self.context.getPhysicalPath())
        puntsInFolder = portal_catalog.searchResults(
            portal_type=['genweb.organs.punt', 'genweb.organs.acord'],
            sort_on='getObjPositionInParent',
            path={'query': folder_path,
                  'depth': 1})
        index = len(puntsInFolder) + 1

        content = text.splitlines()
        subindex = 0
        previousPuntContainer = None
        errors = None
        for line in content:
            if len(line) == 0:
                continue

            # OPTIMIZATION: Cachear line.strip() y split para evitar llamadas repetidas
            line_stripped = line.lstrip().rstrip()
            is_top_level = not line.startswith((' ', '\t'))

            if is_top_level:
                # No hi ha blanks, es un punt o un acord
                # OPTIMIZATION: Evitar split múltiple, hacer solo una vez
                parts = line_stripped.split(' ')
                portal_type = parts[0].upper()
                title = ' '.join(parts[1:]) if len(parts) > 1 else line_stripped

                # OPTIMIZATION: Determinar tipo de contenido sin conversión str redundante
                if portal_type == 'A':  # Es tracta d'un acord
                    content_type = 'genweb.organs.acord'
                elif portal_type == 'P':  # Es tracta d'un punt
                    content_type = 'genweb.organs.punt'
                else:  # Supossem que per defecte sense espais es un Punt
                    content_type = 'genweb.organs.punt'
                    title = line_stripped

                with api.env.adopt_roles(['OG1-Secretari']):
                    obj = api.content.create(
                        type=content_type,
                        title=title,
                        container=self.context)

                obj.proposalPoint = str(index)
                obj.estatsLlista = defaultEstat
                index = index + 1
                subindex = 1
                previousPuntContainer = obj
                obj.reindexObject()
            else:
                # hi ha blanks, es un subpunt o un acord
                # OPTIMIZATION: Evitar split múltiple, hacer solo una vez
                parts = line_stripped.split(' ')
                portal_type = parts[0].upper()
                title = ' '.join(parts[1:]) if len(parts) > 1 else line_stripped

                if previousPuntContainer.portal_type == 'genweb.organs.punt':
                    # OPTIMIZATION: Determinar tipo de contenido sin conversión str redundante
                    if portal_type == 'A':  # Es tracta d'un acord
                        content_type = 'genweb.organs.acord'
                    elif portal_type == 'P':  # Es tracta d'un punt (subpunt)
                        content_type = 'genweb.organs.subpunt'
                    else:  # Supossem que per defecte sense espais es un Subpunt
                        content_type = 'genweb.organs.subpunt'
                        title = line_stripped

                    with api.env.adopt_roles(['OG1-Secretari']):
                        newobj = api.content.create(
                            type=content_type,
                            title=title,
                            container=previousPuntContainer)

                    newobj.proposalPoint = str(index - 1) + '.' + str(subindex)
                    newobj.estatsLlista = defaultEstat
                    newobj.reindexObject()
                    subindex = subindex + 1
                else:
                    # dintre d'un acord no podem crear res...
                    errors = _(
                        u"No s'han creat tot els elements perque no segueixen la norma. Dintre d'un Acord no es pot afeigr res.")
                    subindex = subindex - 1

        transaction.commit()

        if errors:
            IStatusMessage(self.request).addStatusMessage(errors, type="error")
            return self.request.response.redirect(self.context.absolute_url())
        else:
            message = "S'han creats els punts indicats."
            lang = self.context.language
            if lang == 'es':
                message = "Se han creado los puntos indicados."
            if lang == 'en':
                message = "Indicated fields have been created."
            IStatusMessage(self.request).addStatusMessage(message, type="success")
            return self.request.response.redirect(self.context.absolute_url())
