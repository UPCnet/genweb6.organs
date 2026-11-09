# -*- coding: utf-8 -*-
"""Base comuna per als tests funcionals de genweb6.organs.

Proporciona:
- Estructura mínima (carpeta d'òrgans + òrgan) creada a cada test.
- Helpers per crear sessions, punts, acords i esmenes.
- Usuaris de prova amb email i rols locals sobre l'òrgan.
- MockMailHost per capturar els correus enviats.
"""
from contextlib import contextmanager
from email import message_from_bytes
from email import message_from_string
from email.header import decode_header
from email.header import make_header

import ast
import datetime
import unittest
import warnings

from Acquisition import aq_base
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.textfield.value import RichTextValue
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from persistent.list import PersistentList
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost
from Products.MailHost.MailHost import _mungeHeaders
from zope.component import getMultiAdapter
from zope.component import getSiteManager

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING


ORGAN_FROM_MAIL = 'organ@example.com'

# id -> (email, rol local sobre l'òrgan)
DEFAULT_USERS = {
    'secretari': ('secretari@example.com', 'OG1-Secretari'),
    'editor': ('editor@example.com', 'OG2-Editor'),
    'membre1': ('membre1@example.com', 'OG3-Membre'),
    'membre2': ('membre2@example.com', 'OG3-Membre'),
    'membre3': ('membre3@example.com', 'OG3-Membre'),
    'afectat': ('afectat@example.com', 'OG4-Afectat'),
    'convidat': ('convidat@example.com', 'OG5-Convidat'),
    'membre_sense_email': ('', 'OG3-Membre'),
}

SESSION_TRANSITIONS = {
    'planificada': [],
    'convocada': ['convocar'],
    'realitzada': ['convocar', 'realitzar'],
    'tancada': ['convocar', 'realitzar', 'tancar'],
    'en_correccio': ['convocar', 'realitzar', 'tancar', 'corregir'],
}


def as_dict(value):
    """infoVotacio / infoQuorums poden estar guardats com a str o dict."""
    if value is None or value == '':
        return {}
    if isinstance(value, str):
        return ast.literal_eval(value)
    return value


class RecordingMailHost(MockMailHost):
    """MockMailHost que també guarda els destinataris reals (sobre).

    MailHost elimina la capçalera Bcc i la passa als destinataris del sobre,
    així que per comprovar els Bcc cal guardar `mto`.
    """

    def reset(self):
        super(RecordingMailHost, self).reset()
        self.recipients = PersistentList()

    def send(self, messageText, mto=None, mfrom=None, subject=None,
             encode=None, immediate=False, charset=None, msg_type=None):
        msg, mto, mfrom = _mungeHeaders(
            messageText, mto, mfrom, subject, charset, msg_type, encode)
        self.messages.append(msg)
        self.recipients.append(list(mto))


class SentMail(object):
    """Correu capturat pel MockMailHost, ja parsejat."""

    def __init__(self, raw, recipients=None):
        self.raw = raw
        self.recipients = recipients or []
        if isinstance(raw, bytes):
            self.message = message_from_bytes(raw)
        else:
            self.message = message_from_string(raw)

    def header(self, name):
        value = self.message.get(name)
        if value is None:
            return None
        return str(make_header(decode_header(value)))

    @property
    def mfrom(self):
        return self.header('From')

    @property
    def mto(self):
        return self.header('To')

    @property
    def bcc(self):
        return self.header('Bcc')

    @property
    def subject(self):
        return self.header('Subject')

    @property
    def body(self):
        parts = []
        for part in self.message.walk():
            if part.get_content_maintype() == 'text':
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                parts.append(payload.decode(charset))
        return '\n'.join(parts)


class _FakeLdapUsers(object):
    def searchUsers(self, **kw):
        return []


class FakeLdapPlugin(object):
    """Substitut mínim de acl_users.ldapUPC (excusar_assist hi accedeix
    directament). searchUsers no troba res -> el formulari usa els camps."""

    def __init__(self):
        self.acl_users = _FakeLdapUsers()


class OrgansFunctionalTestCase(unittest.TestCase):
    """Base per a tests funcionals amb òrgan, usuaris i MockMailHost."""

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING
    organ_type = 'open_organ'

    def setUp(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)
        warnings.filterwarnings('ignore', category=DeprecationWarning)

        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

        setupview = getMultiAdapter((self.portal, self.request), name='setup-view')
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()

        behavior = ISelectableConstrainTypes(self.portal['ca'])
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(['genweb.organs.organsfolder'])
        behavior.setImmediatelyAddableTypes(['genweb.organs.organsfolder'])

        self.organs_folder = api.content.create(
            type='genweb.organs.organsfolder',
            id='testingfolder',
            title='Organ Tests',
            container=self.portal['ca'])

        self.organ = self.create_organ(self.organ_type)

        self.setup_mailhost()
        self.users = {}
        for user_id, (email, role) in DEFAULT_USERS.items():
            self.create_user(user_id, email=email, role=role)

    # ------------------------------------------------------------------
    # Correu
    # ------------------------------------------------------------------
    def setup_mailhost(self):
        self.portal._original_MailHost = self.portal.MailHost
        self.mailhost = RecordingMailHost('MailHost')
        self.mailhost.smtp_host = 'localhost'
        self.portal.MailHost = self.mailhost
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(self.mailhost, provided=IMailHost)
        api.portal.set_registry_record('plone.email_from_address', 'noreply@example.com')
        api.portal.set_registry_record('plone.email_charset', 'utf-8')
        if not self.portal.hasProperty('email_charset'):
            self.portal.manage_addProperty('email_charset', 'utf-8', 'string')
        self.addCleanup(self.teardown_mailhost)

    def teardown_mailhost(self):
        self.portal.MailHost = self.portal._original_MailHost
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(aq_base(self.portal._original_MailHost), provided=IMailHost)

    def sent_mails(self):
        return [SentMail(raw, rcpt) for raw, rcpt in
                zip(self.mailhost.messages, self.mailhost.recipients)]

    def reset_mails(self):
        self.mailhost.reset()

    def install_fake_ldap(self):
        acl_users = self.portal.acl_users
        if 'ldapUPC' in acl_users.__dict__:
            return
        acl_users.ldapUPC = FakeLdapPlugin()
        self.addCleanup(delattr, acl_users, 'ldapUPC')

    # ------------------------------------------------------------------
    # Usuaris
    # ------------------------------------------------------------------
    def create_user(self, user_id, email='', role=None, obj=None):
        properties = {'fullname': user_id.capitalize()}
        user = api.user.create(
            username=user_id,
            email=email or 'placeholder-{0}@example.com'.format(user_id),
            password='Secret.12345',
            roles=['Member'],
            properties=properties)
        if not email:
            # api.user.create exigeix email: el buidem després
            user.setMemberProperties({'email': ''})
        if role:
            api.user.grant_roles(
                username=user_id, obj=obj or self.organ, roles=[role])
        self.users[user_id] = user
        return user

    @contextmanager
    def as_user(self, user_id):
        """Executa el bloc autenticat com a `user_id` i torna a Manager."""
        logout()
        login(self.portal, user_id)
        try:
            yield
        finally:
            logout()
            login(self.portal, TEST_USER_NAME)

    # ------------------------------------------------------------------
    # Contingut
    # ------------------------------------------------------------------
    def create_organ(self, organ_type='open_organ', id='organ'):
        organ = api.content.create(
            type='genweb.organs.organgovern',
            id=id,
            title='Organ {0}'.format(organ_type),
            container=self.organs_folder,
            safe_id=True)
        organ.acronim = 'OG.TEST'
        organ.organType = organ_type
        organ.fromMail = ORGAN_FROM_MAIL
        return organ

    def create_session(self, state='realitzada', id='sessio', title='Sessio Test',
                       organ=None):
        now = datetime.datetime.now()
        session = api.content.create(
            type='genweb.organs.sessio',
            id=id,
            title=title,
            container=organ or self.organ,
            start=now,
            end=now + datetime.timedelta(hours=1),
            modality='attended',
            numSessioShowOnly='01',
            numSessio='01')
        # Els defaultFactory de bodyMail/signatura retornen str; el formulari
        # TTW els converteix a RichTextValue. Ho reproduïm aquí.
        for name in ('bodyMail', 'signatura'):
            value = getattr(session, name, None)
            if value is None or isinstance(value, str):
                setattr(session, name, RichTextValue(
                    value or '', 'text/html', 'text/x-html-safe'))
        for transition in SESSION_TRANSITIONS[state]:
            api.content.transition(obj=session, transition=transition)
        return session

    def create_punt(self, session, id='punt', title='Punt Test'):
        return api.content.create(
            type='genweb.organs.punt', id=id, title=title, container=session)

    def create_acord(self, container, id='acord', title='Acord Test'):
        acord = api.content.create(
            type='genweb.organs.acord', id=id, title=title, container=container)
        acord.infoVotacio = '{}'
        return acord

    def create_esmena(self, acord, id='esmena', title='Esmena Test',
                      estat='open'):
        esmena = api.content.create(
            type='genweb.organs.votacioacord', id=id, title=title, container=acord)
        esmena.estatVotacio = estat
        esmena.tipusVotacio = 'public'
        esmena.infoVotacio = '{}'
        return esmena

    def call_view(self, context, name, method='GET', **form):
        """Crida una vista amb comprovació de permisos (restrictedTraverse).

        Per enviar formularis z3c.form cal method='POST': el patch de Plone
        (Products.CMFPlone.patches.z3c_form) ignora el request si el mètode
        no coincideix amb el del formulari.
        """
        self.request['REQUEST_METHOD'] = method
        self.request.environ['REQUEST_METHOD'] = method
        self.request.form.clear()
        self.request.form.update(form)
        for key, value in form.items():
            setattr(self.request, key, value)
        view = context.restrictedTraverse('@@' + name)
        return view()
