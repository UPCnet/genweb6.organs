# -*- coding: utf-8 -*-
"""Vista manageFiles: gestió de visibilitat fitxers (Restringit/Públic).
   Per a totes les seccions (Consell de Govern, Consell Social, etc.): sessió, punt, subpunt i acord.
"""

from plone import api
from zope.component import getMultiAdapter

from genweb6.organs import utils
from Products.Five.browser import BrowserView


def _is_sessio(context):
    return getattr(context, 'portal_type', None) == 'genweb.organs.sessio'


class ManageFilesView(BrowserView):
    """Vista que mostra fitxers amb switches Restringit/Públic (ordre del dia en sessió, o llistat pla en punt/subpunt/acord)."""

    def canView(self):
        """Mateix criteri que canViewManageFilesButton."""
        return self._can_manage_files()

    def _can_manage_files(self):
        estat_sessio = utils.session_wf_state(self)
        if estat_sessio == 'tancada':
            return False
        roles = getattr(self, '_cached_roles', None)
        if roles is None:
            username = api.user.get_current().id
            roles = utils.getUserRoles(self, self.context, username)
        return bool(utils.checkhasRol(['Manager', 'OG1-Secretari', 'OG2-Editor'], roles))

    def PuntsInside(self):
        """Items amb files (ordre del dia si context és sessió; un sol bloc si és punt/subpunt/acord)."""
        if _is_sessio(self.context):
            return self._punts_inside_sessio()
        return self._single_container_items()

    def _punts_inside_sessio(self):
        """Punts i subpunts amb files (lògica actual de la sessió)."""
        base_view = getMultiAdapter((self.context, self.request), name='view')
        items = base_view.PuntsInside()
        for item in items:
            if not item.get('show', True):
                continue
            files = self._files_with_visibility_rows(item)
            item['files'] = files
            item['hasContent'] = bool(files or item.get('subpunts'))
            for sub in item.get('subpunts') or []:
                sub_files = self._files_with_visibility_rows(sub)
                sub['files'] = sub_files
        return [i for i in items if i.get('show', True)]

    def _single_container_items(self):
        """Un sol item per al context (punt, subpunt o acord) amb els seus fitxers."""
        files = self._files_from_container(self.context)
        return [{
            'id': self.context.id,
            'title': self.context.Title(),
            'proposalPoint': getattr(self.context, 'proposalPoint', ''),
            'agreement': getattr(self.context, 'agreement', None),
            'files': files,
            'hasContent': bool(files),
            'show': True,
            'subpunts': [],
        }]

    def _files_from_container(self, container):
        """Fitxers amb visibility_rows dins d'un contenidor (punt, subpunt, acord)."""
        folder_path = '/'.join(container.getPhysicalPath())
        return self._files_in_path(folder_path, container.id)

    def _files_with_visibility_rows(self, item):
        """Retorna llista de dicts per a genweb.organs.file amb visibility_rows (per item de PuntsInside)."""
        folder_path = '/'.join(self.context.getPhysicalPath()) + '/' + item['id']
        return self._files_in_path(folder_path, item['id'])

    def _files_in_path(self, folder_path, item_id):
        """Cerca genweb.organs.file a folder_path i retorna llistat amb visibility_rows."""
        portal_catalog = api.portal.get_tool(name='portal_catalog')
        values = portal_catalog.unrestrictedSearchResults(
            portal_type=['genweb.organs.file'],
            sort_on='getObjPositionInParent',
            path={'query': folder_path, 'depth': 1})
        results = []
        for obj in values:
            value = obj.getObject()
            file_url = value.absolute_url()
            file_id = str(item_id) + '/' + obj.id
            title = obj.Title
            visibility_rows = self._visibility_rows_for_file(value, file_url, file_id)
            if not visibility_rows:
                continue
            has_visible = bool(getattr(value, 'visiblefile', None))
            has_hidden = bool(getattr(value, 'hiddenfile', None))
            if has_visible and has_hidden:
                class_css = 'bi bi-file-earmark-pdf text-success'
            elif has_hidden:
                class_css = 'bi bi-file-earmark-pdf text-danger'
            else:
                class_css = 'bi bi-file-earmark-pdf text-success'
            results.append({
                'title': title,
                'absolute_url': file_url,
                'id': file_id,
                'classCSS': class_css,
                'visibility_rows': visibility_rows,
            })
        return results

    def _visibility_rows_for_file(self, file_obj, file_url, file_id):
        """Per un genweb.organs.file retorna 1 o 2 filas (Restringit, Públic)."""
        rows = []
        has_visible = bool(getattr(file_obj, 'visiblefile', None))
        has_hidden = bool(getattr(file_obj, 'hiddenfile', None))
        has_both = has_visible and has_hidden

        if has_hidden:
            row_id = file_id + '-visibleToHidden'
            other_row_id = (file_id + '-hiddenToVisible') if has_both else ''
            rows.append({
                'file_url': file_url,
                'action': 'visibleToHidden',
                'other_action': 'hiddenToVisible',
                'label': 'Restringit',
                'css_class': 'text-danger',
                'switch_pill_class': 'visibility-switch-restringit',
                'is_active': has_hidden,
                'has_both': has_both,
                'row_id': row_id,
                'other_row_id': other_row_id,
            })
        if has_visible:
            row_id = file_id + '-hiddenToVisible'
            other_row_id = (file_id + '-visibleToHidden') if has_both else ''
            rows.append({
                'file_url': file_url,
                'action': 'hiddenToVisible',
                'other_action': 'visibleToHidden',
                'label': 'Públic',
                'css_class': 'text-success',
                'switch_pill_class': 'visibility-switch-public',
                'is_active': has_visible,
                'has_both': has_both,
                'row_id': row_id,
                'other_row_id': other_row_id,
            })
        return rows
