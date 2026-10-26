# -*- coding: utf-8 -*-
from Acquisition import aq_chain
from Acquisition import aq_inner
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin

from datetime import datetime
from plone import api
from plone.app.layout.navigation.root import getNavigationRootObject
from plone.memoize import instance
from plone.registry.interfaces import IRegistry
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility

from genweb6.core.purge import purge_varnish_paths
from genweb6.organs import _
from genweb6.organs.controlpanel import IOrgansSettings

import ast
import unicodedata


def isConvidat(self):
    """ Return true if user has role OG4-Afectat """
    if not api.user.is_anonymous():
        username = api.user.get_current().id
        roles = getUserRoles(self, self.context, username)
        if 'OG5-Convidat' in roles:
            return True
    return False


def isAfectat(self):
    """ Return true if user has role OG4-Afectat """
    if not api.user.is_anonymous():
        username = api.user.get_current().id
        roles = getUserRoles(self, self.context, username)
        if 'OG4-Afectat' in roles:
            return True
    return False


def isMembre(self):
    """ Return true if user has role OG3-Membre """
    if not api.user.is_anonymous():
        username = api.user.get_current().id
        roles = getUserRoles(self, self.context, username)
        if 'OG3-Membre' in roles:
            return True
    return False


def isEditor(self):
    """ Returns true if user has role OG2-Editor """
    if not api.user.is_anonymous():
        username = api.user.get_current().id
        roles = getUserRoles(self, self.context, username)
        if 'OG2-Editor' in roles:
            return True
    return False


def isSecretari(self):
    """ Return true if user has role OG1-Secretari """
    if not api.user.is_anonymous():
        username = api.user.get_current().id
        roles = getUserRoles(self, self.context, username)
        if 'OG1-Secretari' in roles:
            return True
    return False


def isManager(self):
    """ Return true if user has role Manager """
    if not api.user.is_anonymous():
        username = api.user.get_current().id
        roles = getUserRoles(self, self.context, username)
        if 'Manager' in roles:
            return True
    return False


@instance.memoize
def getUserRoles(self, context, username):
    try:
        return api.user.get_roles(username=username, obj=context)
    except:
        return []


def checkhasRol(check_roles, user_roles):
    for check_rol in check_roles:
        if check_rol in user_roles:
            return True
    return False


def isAnon(self):
    """ Return true if user has role OG1-Secretari """
    if api.user.is_anonymous():
        return True


def addEntryLog(context, sender, message, recipients):
    """ Adds entry log with the values:
            context: where the actions is executed
            sender: who sends the mail
            message: the message
            recipients: the recipients of the message
    """

    KEY = 'genweb.organs.logMail'
    annotations = IAnnotations(context)

    # This is used to remove all the log entries:
    # import ipdb;ipdb.set_trace()
    # annotations[KEY] = []
    # To remove some entry:
    # aaa = annotations[KEY]
    # pp(aaa)       # Search the desired entry position
    # aaa.pop(0)    # remove the entry

    if annotations is not None:
        try:
            # Get data and append values
            if annotations.get(KEY) is not None:
                data = annotations.get(KEY)
            else:
                data = []
        except:
            # If it's empty, initialize data
            data = []

        dateMail = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        if not sender:
            anon = api.user.is_anonymous()
            if anon:
                sender = _(u'Anonymous user')
            else:
                portal = api.portal.get()
                plugins = portal.acl_users.plugins.listPlugins(IPropertiesPlugin)
                # We use the most preferent plugin
                try:
                    pplugin = plugins[2][1]
                    all_user_properties = pplugin.enumerateUsers(
                        api.user.get_current().id)
                    fullname = ''
                    for user in all_user_properties:
                        if user['id'] == api.user.get_current().id:
                            fullname = user['sn']
                            pass
                    if fullname:
                        sender = fullname + ' [' + api.user.get_current().id + ']'
                    else:
                        sender = api.user.get_current().id

                except:
                    # Not LDAP plugin configured
                    user = api.user.get_current()
                    sender = user.getProperty(
                        'fullname') + ' [' + api.user.get_current().id + ']'
        try:
            index = len(annotations.get(KEY))
        except:
            index = 0

        values = dict(index=index + 1,
                      dateMail=dateMail,
                      message=message,
                      fromMail=sender,
                      toMail=recipients)

        data.append(values)
        annotations[KEY] = data


def addExcuse(context, name, email, message):
    """ Adds entry log with the values:
            context: where the actions is executed
            name: who make the excuse
            email: user email
            excuse message: description of the excuse
    """

    KEY = 'genweb.organs.excuse'
    annotations = IAnnotations(context)

    # This is used to remove all the log entries:
    # import ipdb;ipdb.set_trace()
    # annotations[KEY] = []
    # To remove some entry:
    # aaa = annotations[KEY]
    # pp(aaa)       # Search the desired entry position
    # aaa.pop(0)    # remove the entry

    if annotations is not None:
        try:
            # Get data and append values
            if annotations.get(KEY) is not None:
                data = annotations.get(KEY)
            else:
                data = []
        except:
            # If it's empty, initialize data
            data = []

        date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        try:
            index = len(annotations.get(KEY))
        except:
            index = 0

        values = dict(index=index + 1,
                      date=date,
                      name=name,
                      email=email,
                      message=message)

        data.append(values)
        annotations[KEY] = data


def addPoint(context, names, title, justification, path):
    """ Adds entry log with the values:
            context: where the actions is executed
            names: who makes the point
            title: title of the proposed point
            justification: why
    """

    KEY = 'genweb.organs.point'
    annotations = IAnnotations(context)

    # This is used to remove all the log entries:
    # import ipdb;ipdb.set_trace()
    # annotations[KEY] = []
    # To remove some entry:
    # aaa = annotations[KEY]
    # pp(aaa)       # Search the desired entry position
    # aaa.pop(0)    # remove the entry

    if annotations is not None:
        try:
            # Get data and append values
            if annotations.get(KEY) is not None:
                data = annotations.get(KEY)
            else:
                data = []
        except:
            # If it's empty, initialize data
            data = []

        date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        try:
            index = len(annotations.get(KEY))
        except:
            index = 0

        values = dict(index=index + 1,
                      date=date,
                      names=names,
                      title=title,
                      justification=justification,
                      path=path)

        data.append(values)
        annotations[KEY] = data


def FilesandDocumentsInside(self):
    """ Fitxers i documents d'un punt / subpunt / acord.

        - open_organ: Sec, Ed, Mem, Afe, Conv veuen les dues parts diferenciades;
          la resta (anònims i autenticats sense rol) només la pública.
        - restricted_to_members_organ: Sec, Ed, Mem, Conv veuen les dues parts;
          la resta no veu res.
        - restricted_to_affected_organ: Sec, Ed, Mem, Conv veuen les dues parts;
          Afe només la pública; la resta no veu res.
    """
    organ_tipus = self.context.organType

    portal_catalog = api.portal.get_tool(name='portal_catalog')
    folder_path = '/'.join(self.context.getPhysicalPath())
    values = portal_catalog.unrestrictedSearchResults(
        portal_type=['genweb.organs.file', 'genweb.organs.document'],
        sort_on='getObjPositionInParent',
        path={'query': folder_path,
              'depth': 1})

    if organ_tipus == 'open_organ':
        reserved_roles = ['Manager', 'OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                          'OG4-Afectat', 'OG5-Convidat']
        public_roles = None  # tothom
    elif organ_tipus == 'restricted_to_affected_organ':
        reserved_roles = ['Manager', 'OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                          'OG5-Convidat']
        public_roles = reserved_roles + ['OG4-Afectat']
    else:
        reserved_roles = ['Manager', 'OG1-Secretari', 'OG2-Editor', 'OG3-Membre',
                          'OG5-Convidat']
        public_roles = reserved_roles

    results = []
    for obj in values:
        value = obj.getObject()
        roles = getUserRoles(self, value, api.user.get_current().id)

        show_only_public = not checkhasRol(reserved_roles, roles)
        if show_only_public and public_roles is not None and not checkhasRol(public_roles, roles):
            continue

        if obj.portal_type == 'genweb.organs.file':
            has_public = bool(value.visiblefile)
            has_reserved = bool(value.hiddenfile)
            icon = 'bi bi-file-earmark-pdf'
        else:
            has_public = bool(value.defaultContent)
            has_reserved = bool(value.alternateContent)
            icon = 'bi bi-file-earmark-text'

        if show_only_public:
            # Sense part pública → no es llista
            if not has_public:
                continue
            has_reserved = False

        has_double_content = has_public and has_reserved
        if has_double_content:
            class_css = icon + ' text-success double-icon'
        elif has_reserved:
            class_css = icon + ' text-danger'
        elif has_public:
            class_css = icon + ' text-success'
        else:
            class_css = icon

        if checkhasRol(['Manager', 'OG1-Secretari', 'OG2-Editor'], roles):
            # Editor i Secretari veuen contingut. NO obren en finestra nova
            results.append(dict(title=obj.Title,
                                portal_type=obj.portal_type,
                                absolute_url=obj.getURL(),
                                target=None,
                                classCSS=class_css))
            continue

        # Doble contingut → vista de l'objecte amb les dues parts diferenciades
        absolute_url = obj.getURL()
        if obj.portal_type == 'genweb.organs.file' and not has_double_content:
            info_firma = getattr(value, 'info_firma', None) or {}
            if not isinstance(info_firma, dict):
                info_firma = ast.literal_eval(info_firma)

            if has_public:
                if info_firma.get('public', {}).get('uploaded', False):
                    absolute_url = obj.getURL() + '/viewFileGDoc?visibility=public'
                else:
                    absolute_url = obj.getURL() + '/@@display-file/visiblefile/' + value.visiblefile.filename
            elif has_reserved:
                if info_firma.get('private', {}).get('uploaded', False):
                    absolute_url = obj.getURL() + '/viewFileGDoc?visibility=private'
                else:
                    absolute_url = obj.getURL() + '/@@display-file/hiddenfile/' + value.hiddenfile.filename

        results.append(dict(title=obj.Title,
                            portal_type=obj.portal_type,
                            absolute_url=absolute_url,
                            target=None if has_double_content else '_blank',
                            classCSS=class_css))
    return results


def SubPuntsInside(self):
    # Returns punts and acords inside Punts
    portal_catalog = api.portal.get_tool(name='portal_catalog')
    folder_path = '/'.join(self.context.getPhysicalPath())
    values = portal_catalog.unrestrictedSearchResults(
        portal_type=['genweb.organs.subpunt', 'genweb.organs.acord'],
        sort_on='getObjPositionInParent',
        path={'query': folder_path,
              'depth': 1})
    results = []
    for obj in values:
        item = obj._unrestrictedGetObject()
        if obj.portal_type == 'genweb.organs.acord':
            agreement = item.agreement
        else:
            agreement = False
        results.append(dict(title=obj.Title,
                            proposalPoint=item.proposalPoint,
                            agreement=agreement,
                            absolute_url=obj.getURL()))
    return results


def getColor(self, organ=None):
    # Get custom colors on passed organ states
    # OPTIMIZATION: Aceptar organ pre-calculado para evitar get_organ repetidos
    color = '#777777'
    try:
        obj = self._unrestrictedGetObject()
        estat = obj.estatsLlista
        if organ is None:
            organ = get_organ(obj)
        values = organ.estatsLlista.raw
        for value in values.split('</p>'):
            if value != '':
                item_net = unicodedata.normalize("NFKD", value).rstrip(
                    ' ').replace('<p>', '').replace('</p>', '').replace('\r\n', '')
                if estat == ' '.join(item_net.split()[:-1]).lstrip():
                    return item_net.split(' ')[
                        -1:][0].rstrip(' ').replace(
                        '<p>', '').replace(
                        '</p>', '').lstrip(' ')
    except:
        pass
    return color


def estatsCanvi(self, organ=None):
    # Returns real names from estats
    # OPTIMIZATION: Aceptar organ pre-calculado para evitar get_organ repetidos
    if organ is None:
        organ = get_organ(self._unrestrictedGetObject())
    values = organ.estatsLlista
    # Soporte Plone 6: si es RichTextValue, usar .raw
    from plone.app.textfield.value import RichTextValue
    if isinstance(values, RichTextValue):
        values = values.raw
    items = []
    for value in values.split('</p>'):
        if value != '':
            item_net = unicodedata.normalize("NFKD", value).rstrip(
                ' ').replace('<p>', '').replace('</p>', '').replace('\r\n', '')
            estat = ' '.join(item_net.split()[:-1]).lstrip()
            color = ' '.join(item_net.split()[-1:]).lstrip()
            items.append(dict(title=estat, color=color))
    return items


def session_wf_state(self):
    # Returns session state. Check it recurring all path...
    from genweb6.organs.content.sessio.sessio import ISessio
    if ISessio.providedBy(self.context):
        portal_state = api.content.get_state(obj=self.context)
        return portal_state
    else:
        portal_state = self.context.unrestrictedTraverse('@@plone_portal_state')
        root = getNavigationRootObject(self.context, portal_state.portal())
        physical_path = aq_inner(self.context).getPhysicalPath()
        relative = physical_path[len(root.getPhysicalPath()):]
        for i in range(len(relative)):
            now = relative[:i + 1]
            obj = aq_inner(root.unrestrictedTraverse(now))
            if ISessio.providedBy(obj):
                session_state = api.content.get_state(obj=obj)
                return session_state


def get_settings_property(property_id):
    settings = getUtility(IRegistry).forInterface(IOrgansSettings)
    return getattr(settings, property_id, None)


def get_organ(context):
    from genweb6.organs.content.organgovern.organgovern import IOrgangovern
    if IOrgangovern.providedBy(context):
        return context
    else:
        portal_state = context.unrestrictedTraverse('@@plone_portal_state')
        root = getNavigationRootObject(context, portal_state.portal())
        physical_path = aq_inner(context).getPhysicalPath()
        relative = physical_path[len(root.getPhysicalPath()):]
        for i in range(len(relative)):
            now = relative[:i + 1]
            obj = aq_inner(root.unrestrictedTraverse(now))
            if IOrgangovern.providedBy(obj):
                return obj
    return None


def get_session(context):
    from genweb6.organs.content.sessio.sessio import ISessio
    if ISessio.providedBy(context):
        return context
    else:
        portal_state = context.unrestrictedTraverse('@@plone_portal_state')
        root = getNavigationRootObject(context, portal_state.portal())
        physical_path = aq_inner(context).getPhysicalPath()
        relative = physical_path[len(root.getPhysicalPath()):]
        for i in range(len(relative)):
            now = relative[:i + 1]
            obj = aq_inner(root.unrestrictedTraverse(now))
            if ISessio.providedBy(obj):
                return obj
    return None


def getLdapUserData(user, typology=None):
    acl_users = api.portal.get_tool(name='acl_users')
    if not typology:
        search_result = acl_users.searchUsers(id=user, exactMatch=True)
    else:
        search_result = acl_users.searchUsers(
            id=user, exactMatch=True, typology=typology)
    return search_result


def get_acord(context):
    from genweb6.organs.content.acord.acord import IAcord
    for obj in aq_chain(context):
        if IAcord.providedBy(obj):
            return obj
    return None


def checkHasOpenVote(context):
    acord = get_acord(context)
    if acord:
        if acord.estatVotacio == 'open':
            return True

        acord_folder_path = '/'.join(acord.getPhysicalPath())
        portal_catalog = api.portal.get_tool(name='portal_catalog')
        esmenas = portal_catalog.unrestrictedSearchResults(
            portal_type=['genweb.organs.votacioacord'],
            sort_on='getObjPositionInParent',
            path={'query': acord_folder_path,
                    'depth': 1})

        for esmena in esmenas:
            if esmena.getObject().estatVotacio == 'open':
                return True

    return False


def getFilesSessio(context):
    portal_catalog = api.portal.get_tool('portal_catalog')
    session = get_session(context)
    session_path = '/'.join(session.getPhysicalPath())
    punts = portal_catalog.searchResults(
        portal_type=['genweb.organs.acord', 'genweb.organs.punt'],
        path={'query': session_path, 'depth': 1},
        sort_on='getObjPositionInParent'
    )
    files = []
    for punt in punts:
        files_punt = portal_catalog.searchResults(
            portal_type=['genweb.organs.file'],
            path={'query': punt.getPath(), 'depth': 1},
            sort_on='getObjPositionInParent'
        )

        for file in files_punt:
            files.append(file.getObject())

        if punt.getObject().portal_type == 'genweb.organs.acord':
            continue

        subpunts = portal_catalog.searchResults(
            portal_type=['genweb.organs.acord', 'genweb.organs.subpunt'],
            path={'query': punt.getPath(), 'depth': 1},
            sort_on='getObjPositionInParent'
        )

        for subpunt in subpunts:
            files_subpunt = portal_catalog.searchResults(
                portal_type=['genweb.organs.file'],
                path={'query': subpunt.getPath(), 'depth': 1},
                sort_on='getObjPositionInParent'
            )
            for file in files_subpunt:
                files.append(file.getObject())

    return [file for file in files if file.visiblefile or file.hiddenfile]


def purge_cache_varnish(self):
    paths = []
    paths.append('_purge_all')
    purge_varnish_paths(self, paths)


def normalize_url(url):
    """ Afegeix https:// si l'enllaç no té esquema (evita enllaços relatius) """
    url = (url or '').strip()
    if url and '://' not in url and not url.startswith(('mailto:', 'tel:', '/')):
        return 'https://' + url
    return url
