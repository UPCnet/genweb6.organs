# -*- coding: utf-8 -*-
"""Bateria manual: votació amb el teu usuari UPC real (LDAP), en local.

No toca cap Plone de PRE. A la instància de test:

1. Es crea ldapUPC amb el mateix codi que producció
   (genweb6.core setSetupLDAPUPC + setup_ldapupc_properties_plugin).
2. Es fa login real per HTTP amb LOCAL_USER / LOCAL_PASSWORD contra l'LDAP.
3. L'email s'obté de l'LDAP (member.getProperty('email')), no es configura.
4. Es vota i es comprova que el correu de vot va a aquest email.

Els correus NO s'envien: es capturen i s'imprimeixen per consola, com fa
Products.PrintingMailHost a la instància local.

Necessita xarxa cap a ldap.upc.edu:636 i la contrasenya del bind
(LDAP_BIND_PASSWORD o la variable d'entorn ldapbindpasswd).

    bin/test -s genweb6.organs --tests-pattern='^manual$' --test-file-pattern='^manual_'
"""
from unittest import mock

import base64
import json
import unittest

import transaction
from plone import api
from plone.testing.zope import Browser
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin

from genweb6.organs.setuphandlers import setup_ldapupc_properties_plugin
from genweb6.organs.tests.base import as_dict
from genweb6.organs.tests.base import ORGAN_FROM_MAIL
from genweb6.organs.tests.base import OrgansFunctionalTestCase
from genweb6.organs.tests.base import RecordingMailHost
from genweb6.organs.tests.base import SentMail
from genweb6.organs.tests.manual.config import CONFIG
from genweb6.organs.tests.manual.config import ldap_bind_password
from genweb6.organs.tests.manual.config import require


SKIP_REASON = ('Falta LOCAL_USER / LOCAL_PASSWORD a tests/manual/manual_settings.env '
               'o la contrasenya del bind LDAP (LDAP_BIND_PASSWORD / ldapbindpasswd)')


@unittest.skipUnless(require('LOCAL_USER', 'LOCAL_PASSWORD') and ldap_bind_password(),
                     SKIP_REASON)
class UsuariLdapVotacioTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(UsuariLdapVotacioTestCase, self).setUp()
        from genweb6.core.browser.helpers import helpers_ldap
        # Registra el 'LDAP delegate' (a la instància ho fa Zope en arrencar)
        import Products.LDAPUserFolder.LDAPDelegate  # noqa: F401

        with mock.patch.object(helpers_ldap, 'LDAP_PASSWORD', ldap_bind_password()):
            helpers_ldap.setSetupLDAPUPC()
        from Acquisition import aq_base
        luf = aq_base(self.portal.acl_users.ldapUPC).__dict__.get('acl_users') \
            if 'ldapUPC' in self.portal.acl_users.objectIds() else None
        self.assertIsNotNone(luf, "No s'ha pogut crear ldapUPC (LDAPUserFolder intern)")
        setup_ldapupc_properties_plugin(self.portal)

        self.user_id = CONFIG['LOCAL_USER']
        self.organ.manage_setLocalRoles(self.user_id, ['OG3-Membre'])
        self.organ.reindexObjectSecurity()

        self.session = self.create_session('convocada', title='Sessio Prova LDAP')
        self.acord = self.create_acord(self.session, title='Acord Prova LDAP')
        self.call_view(self.acord, 'openPublicVote')
        self.reset_mails()
        transaction.commit()

        # Les peticions HTTP fan servir la seva pròpia còpia del MailHost:
        # capturem els correus en memòria del procés.
        self.captured = []
        original_send = RecordingMailHost.send
        captured = self.captured

        def capturing_send(mh, messageText, mto=None, mfrom=None, *args, **kw):
            original_send(mh, messageText, mto, mfrom, *args, **kw)
            captured.append((mh.messages[-1], list(mh.recipients[-1])))

        patcher = mock.patch.object(RecordingMailHost, 'send', capturing_send)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.browser = self.make_browser(CONFIG['LOCAL_PASSWORD'])

    def make_browser(self, password):
        browser = Browser(self.app)
        browser.handleErrors = True
        browser.raiseHttpErrors = False
        credentials = '{0}:{1}'.format(self.user_id, password)
        browser.addHeader(
            'Authorization',
            'Basic ' + base64.b64encode(credentials.encode('utf-8')).decode('ascii'))
        return browser

    def ldap_email(self):
        user = api.user.get(username=self.user_id)
        self.assertIsNotNone(user, "L'usuari {0} no es troba a l'LDAP".format(self.user_id))
        return user.getProperty('email')

    def sent_mails(self):
        return [SentMail(raw, rcpt) for raw, rcpt in self.captured]

    def reset_mails(self):
        super(UsuariLdapVotacioTestCase, self).reset_mails()
        if hasattr(self, 'captured'):
            del self.captured[:]

    def http_vote(self, view, browser=None):
        browser = browser or self.browser
        browser.open(self.acord.absolute_url() + '/@@' + view)
        transaction.begin()  # veure els canvis fets per la petició HTTP
        return browser.contents

    def print_mails(self, title):
        print('\n' + '=' * 70)
        print(title)
        print('=' * 70)
        for mail in self.sent_mails():
            print('Destinataris: {0}'.format(', '.join(mail.recipients)))
            raw = mail.raw.decode('utf-8') if isinstance(mail.raw, bytes) else str(mail.raw)
            print(raw)
            print('-' * 70)

    # ------------------------------------------------------------------
    def test_ldapupc_first_properties_plugin(self):
        ids = self.portal.acl_users.plugins.listPluginIds(IPropertiesPlugin)
        self.assertEqual(ids[0], 'ldapUPC')

    def test_email_from_ldap(self):
        email = self.ldap_email()
        print("\nEmail de {0} segons l'LDAP: {1!r}".format(self.user_id, email))
        self.assertTrue(email and '@' in email,
                        "L'LDAP no retorna email per a {0}".format(self.user_id))

    def test_login_with_ldap_password(self):
        self.browser.open(self.portal.absolute_url() + '/@@personal-information')
        self.assertNotIn('__ac_password', self.browser.contents,
                         'El login amb LOCAL_PASSWORD ha fallat')

    def test_vote_mail_to_ldap_email(self):
        email = self.ldap_email()
        contents = self.http_vote('favorVote')
        self.assertEqual(json.loads(contents)['status'], 'success')
        self.assertEqual(as_dict(self.acord.infoVotacio), {self.user_id: 'favor'})

        mails = self.sent_mails()
        self.print_mails('Correu de vot per a {0}'.format(email))
        self.assertEqual(len(mails), 1, 'No s\'ha generat el correu de vot')
        self.assertEqual(mails[0].recipients, [email])
        self.assertEqual(mails[0].mfrom, ORGAN_FROM_MAIL)
        self.assertIn('has votat a favor', mails[0].body)

    def test_change_vote_sends_second_mail(self):
        self.http_vote('favorVote')
        self.http_vote('againstVote')
        mails = self.sent_mails()
        self.print_mails('Canvi de vot')
        self.assertEqual(len(mails), 2)
        self.assertIn('has votat en contra', mails[1].body)

    def test_remove_vote_mail(self):
        email = self.ldap_email()
        self.http_vote('whiteVote')
        self.reset_mails()
        self.call_view(self.acord, 'removeVote')  # com a Manager
        mails = self.sent_mails()
        self.print_mails('Anul·lació de votació (Bcc a {0})'.format(email))
        self.assertEqual(len(mails), 1)
        self.assertIn(email, mails[0].recipients)

    def test_wrong_password_cannot_vote(self):
        browser = self.make_browser('contrasenya-incorrecta')
        contents = self.http_vote('favorVote', browser)
        self.assertNotIn('"success"', contents)
        self.assertEqual(as_dict(self.acord.infoVotacio), {})
        self.assertEqual(self.sent_mails(), [])
