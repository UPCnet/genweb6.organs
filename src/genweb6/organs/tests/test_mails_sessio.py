# -*- coding: utf-8 -*-
"""Tests de los formularios de correo de la sesión.

- mail_convocar: convoca la sesión y envía la convocatoria.
- mail_informar: informa de la sesión.
- mail_message: mensaje libre a los miembros.
- excusar_assist_sessio: registra la excusa (no envía correo).

Todos dejan entrada en el log de la sesión (annotation genweb.organs.logMail).
"""
import unicodedata
import unittest

from AccessControl import Unauthorized
from plone import api
from plone.app.testing import logout
from zope.annotation.interfaces import IAnnotations

from genweb6.organs.tests.base import ORGAN_FROM_MAIL
from genweb6.organs.tests.base import OrgansFunctionalTestCase


LOG_KEY = 'genweb.organs.logMail'
EXCUSE_KEY = 'genweb.organs.excuse'


class MailsSessioTestCase(OrgansFunctionalTestCase):

    def setUp(self):
        super(MailsSessioTestCase, self).setUp()
        self.organ.adrecaLlista = 'llista@example.com'
        self.session = self.create_session('planificada', title='Sessio Mails')
        self.session.llocConvocatoria = 'Sala de Juntes'
        self.install_fake_ldap()
        self.reset_mails()

    def log(self, key=LOG_KEY):
        return IAnnotations(self.session).get(key) or []

    def submit(self, view_name, user_id=None, button='send', **fields):
        """Envía un formulario z3c.form de la sesión."""
        form = {}
        for name, value in fields.items():
            form['form.widgets.' + name] = value
            if name in ('message', 'membresConvocats', 'membresConvidats'):
                form['form.widgets.{0}.mimeType'.format(name)] = 'text/html'
        form['form.buttons.' + button] = '1'
        if user_id:
            with self.as_user(user_id):
                return self.call_view(self.session, view_name, method='POST', **form)
        return self.call_view(self.session, view_name, method='POST', **form)

    def prefilled(self, view_name):
        view = self.session.restrictedTraverse('@@' + view_name)
        self.request.form.clear()
        self.request['REQUEST_METHOD'] = 'GET'
        view.update()
        return view

    # ------------------------------------------------------------------
    # mail_convocar
    # ------------------------------------------------------------------
    def test_convocar_prefill(self):
        view = self.prefilled('mail_convocar')
        self.assertEqual(view.widgets['sender'].value, ORGAN_FROM_MAIL)
        self.assertEqual(view.widgets['recipients'].value, 'llista@example.com')
        # El títol es normalitza a NFKD (ò -> o + accent combinat)
        title = unicodedata.normalize('NFC', view.widgets['fromTitle'].value)
        self.assertRegex(title, r'^Convocatòria Sessio Mails - \d{2}/\d{2}/\d{4} - \d{2}:\d{2}$')
        body = view.widgets['message'].value.raw
        self.assertIn('Sala de Juntes', body)
        self.assertIn('excusar_assist_sessio', body)
        self.assertIn('Modalitat de la sessió', body)

    @unittest.expectedFailure
    def test_convocar_prefill_es_includes_modality(self):
        """BUG mail_convocar.py (rama 'es'): la línea de modalidad no se
        concatena (falta `moreData +=`), así que en castellano nunca sale."""
        self.session.language = 'es'
        view = self.prefilled('mail_convocar')
        self.assertIn('Modalidad de la sesión', view.widgets['message'].value.raw)

    def test_convocar_prefill_en(self):
        self.session.language = 'en'
        view = self.prefilled('mail_convocar')
        self.assertTrue(view.widgets['fromTitle'].value.startswith('Call '))
        self.assertIn('Session modality', view.widgets['message'].value.raw)

    def test_convocar_sends_mail_and_transitions(self):
        self.submit('mail_convocar',
                    recipients='membre1@example.com',
                    fromTitle='Convocatoria test',
                    message='<p>Cos</p>')
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        mail = mails[0]
        self.assertEqual(mail.mfrom, ORGAN_FROM_MAIL)
        self.assertEqual(mail.subject, 'Convocatoria test')
        self.assertEqual(mail.recipients, ['membre1@example.com'])
        self.assertIn('Cos', mail.body)

        self.assertEqual(api.content.get_state(self.session), 'convocada')
        self.assertEqual(self.session.adrecaLlista, 'membre1@example.com')
        entry = self.log()[-1]
        self.assertEqual(entry['message'], 'Sending mail convocatoria')
        self.assertEqual(entry['toMail'], 'membre1@example.com')

    @unittest.expectedFailure
    def test_convocar_prefilled_body_links(self):
        """A CONFIRMAR EN NAVEGADOR. El cuerpo pre-rellenado lleva enlaces
        '----@@----http://host/...'; action_send reemplaza '----@@----http:/'
        por 'http://', lo que deja 'http:///host/...' si el HTML llega tal
        cual. Si TinyMCE no colapsa la doble barra, los enlaces de la
        convocatoria (sesión y excusar) llegan rotos. Igual en mail_informar
        y mail_message."""
        body = self.prefilled('mail_convocar').widgets['message'].value.raw
        self.submit('mail_convocar', recipients='membre1@example.com',
                    fromTitle='Convocatoria', message=body)
        sent = self.sent_mails()[0].body
        self.assertNotIn('----@@----', sent)
        self.assertIn('href=' + self.session.absolute_url(), sent.replace('"', ''))
        self.assertIn(self.session.absolute_url() + '/excusar_assist_sessio', sent)

    def test_convocar_resolveuid_links_absolute(self):
        self.submit('mail_convocar',
                    recipients='membre1@example.com',
                    fromTitle='Convocatoria',
                    message='<a href="resolveuid/abc">doc</a>')
        portal_url = self.portal.absolute_url()
        self.assertIn(portal_url + '/ca/resolveuid/abc',
                      self.sent_mails()[0].body)

    def test_convocar_multiple_recipients(self):
        self.submit('mail_convocar',
                    recipients='membre1@example.com, membre2@example.com',
                    fromTitle='Convocatoria',
                    message='<p>Cos</p>')
        self.assertEqual(sorted(self.sent_mails()[0].recipients),
                         ['membre1@example.com', 'membre2@example.com'])

    def test_convocar_from_convocada_logs_not_sent(self):
        """Comportamiento ACTUAL al reenviar la convocatoria de una sesión ya
        convocada: el correo SÍ se envía, pero la transición 'convocar' no es
        válida, salta el except y el log/mensaje dicen 'Missatge no enviat'."""
        api.content.transition(obj=self.session, transition='convocar')
        self.submit('mail_convocar',
                    recipients='membre1@example.com',
                    fromTitle='Reenviament',
                    message='<p>Cos</p>')
        self.assertEqual(len(self.sent_mails()), 1)
        self.assertEqual(self.log()[-1]['message'], 'Missatge no enviat')

    def test_convocar_required_fields(self):
        self.submit('mail_convocar', recipients='', fromTitle='', message='')
        self.assertEqual(self.sent_mails(), [])
        self.assertEqual(api.content.get_state(self.session), 'planificada')

    def test_convocar_permissions(self):
        for user_id in ('membre1', 'afectat', 'convidat'):
            with self.assertRaises(Unauthorized, msg=user_id):
                self.submit('mail_convocar', user_id=user_id,
                            recipients='x@example.com', fromTitle='t',
                            message='<p>m</p>')
        self.assertEqual(self.sent_mails(), [])

        self.submit('mail_convocar', user_id='secretari',
                    recipients='x@example.com', fromTitle='t', message='<p>m</p>')
        self.assertEqual(len(self.sent_mails()), 1)

    def test_convocar_anonymous(self):
        logout()
        with self.assertRaises(Unauthorized):
            self.submit('mail_convocar', recipients='x@example.com',
                        fromTitle='t', message='<p>m</p>')

    # ------------------------------------------------------------------
    # mail_informar
    # ------------------------------------------------------------------
    def test_informar_sends_mail(self):
        api.content.transition(obj=self.session, transition='convocar')
        self.submit('mail_informar', user_id='editor',
                    recipients='afectat@example.com',
                    fromTitle='Informació sessió',
                    message='<p>Info</p>')
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].mfrom, ORGAN_FROM_MAIL)
        self.assertEqual(mails[0].subject, 'Informació sessió')
        self.assertEqual(mails[0].recipients, ['afectat@example.com'])
        self.assertEqual(self.log()[-1]['message'], 'Sending mail informar sessio')
        # Informar no cambia el estado
        self.assertEqual(api.content.get_state(self.session), 'convocada')

    def test_informar_prefill_includes_punts(self):
        self.create_punt(self.session, id='p1', title='Punt Pressupost')
        view = self.prefilled('mail_informar')
        self.assertIn('Punt Pressupost', view.widgets['message'].value.raw)

    # ------------------------------------------------------------------
    # mail_message
    # ------------------------------------------------------------------
    def test_message_sends_mail(self):
        self.submit('mail_message', user_id='secretari',
                    recipients='membre1@example.com',
                    fromTitle='Missatge',
                    message='<p>Hola</p>')
        mails = self.sent_mails()
        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].subject, 'Missatge')
        self.assertIn('Hola', mails[0].body)
        self.assertEqual(self.log()[-1]['message'], 'Sending mail new message')
        self.assertEqual(api.content.get_state(self.session), 'planificada')

    def test_log_entries_are_numbered(self):
        for i in range(3):
            self.submit('mail_message', recipients='membre1@example.com',
                        fromTitle='M{0}'.format(i), message='<p>m</p>')
        # La creación de la sesión ya deja una entrada ('New session created')
        log = self.log()
        self.assertEqual(log[0]['message'], 'New session created')
        self.assertEqual([e['index'] for e in log], list(range(1, len(log) + 1)))
        self.assertEqual(len(log), 4)

    # ------------------------------------------------------------------
    # excusar_assist_sessio
    # ------------------------------------------------------------------
    def test_excusar_registers_excuse_without_mail(self):
        api.content.transition(obj=self.session, transition='convocar')
        self.submit('excusar_assist_sessio', user_id='membre1',
                    name='Membre U', email='membre1@example.com',
                    comments='Estic de viatge')
        excuses = self.log(EXCUSE_KEY)
        self.assertEqual(len(excuses), 1)
        self.assertEqual(excuses[0]['message'], 'Estic de viatge')
        self.assertEqual(excuses[0]['email'], 'membre1@example.com')
        self.assertEqual(excuses[0]['index'], 1)
        self.assertEqual(self.sent_mails(), [])

    def test_excusar_requires_comments(self):
        api.content.transition(obj=self.session, transition='convocar')
        self.submit('excusar_assist_sessio', user_id='membre1',
                    name='M', email='m@example.com', comments='')
        self.assertEqual(self.log(EXCUSE_KEY), [])

    def test_excusar_permissions(self):
        api.content.transition(obj=self.session, transition='convocar')
        for user_id in ('editor', 'afectat'):
            with self.assertRaises(Unauthorized, msg=user_id):
                self.submit('excusar_assist_sessio', user_id=user_id,
                            comments='No puc')
        for user_id in ('secretari', 'convidat'):
            self.submit('excusar_assist_sessio', user_id=user_id,
                        comments='No puc')
        self.assertEqual(len(self.log(EXCUSE_KEY)), 2)
