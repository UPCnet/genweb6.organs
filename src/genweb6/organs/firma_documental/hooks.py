# -*- coding: utf-8 -*-
from Products.statusmessages.interfaces import IStatusMessage

from genweb6.organs import _
from genweb6.organs import utils
from genweb6.organs.browser.events.change import estatFirma


def warningContentIsSigned(content, event):
    """
    Mostra un warning quan s'afegeix o modifica contingut
    dins d'una sessió que té documentació enviada a firmar.
    """

    # Verificar que és un tipus de contingut d'organs
    portal_type = getattr(content, 'portal_type', None)
    if not portal_type or not portal_type.startswith('genweb.organs.'):
        return

    # Obtenir la sessió
    try:
        session = utils.get_session(content)
    except:
        return

    if not session:
        return

    # Si la sessió està signada o enviada a signar, mostrar warning
    estat_firma = estatFirma(session)
    estat_firma = estat_firma['class'] if estat_firma else None
    if estat_firma in ('signada', 'pendent', 'pendent_signants'):
        request = getattr(content, 'REQUEST', None)
        if request:
            if estat_firma == 'signada':
                msg = _(u"Aquesta sessió té documentació ja signada. "
                        u"Els canvis realitzats no es reflectiran en la documentació ja signada.")
            else:
                msg = _(u"Aquesta sessió té documentació ja enviada a signar. "
                        u"Els canvis realitzats no es reflectiran en la documentació ja enviada.")
            IStatusMessage(request).addStatusMessage(msg, type="warning")