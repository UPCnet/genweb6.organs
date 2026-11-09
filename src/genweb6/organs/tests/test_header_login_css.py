# -*- coding: utf-8 -*-
"""L'opció d'identificar-se de la capçalera ha de ser visible en PC i mòbil.

La capçalera és la de genweb6.core (viewlet genweb.header) i pinta el login
dues vegades:
- PC:    #portal-navbar #portal-globalnav li.nav-item.nav-action > a
- Mòbil: #portal-navbar-mobile #gwMobileNavbar li.nav-item > a#personaltools-login-mobile

El CSS d'organs (theme/scss/_generic.scss, commit 5d2ca1a) amaga els
`.nav-item` del menú i torna a mostrar el del login. Aquest test renderitza
la pàgina com a anònim i avalua els CSS compilats que es serveixen
(genweb6.theme theme.min.css + organs theme-organs.min.css) per a una
amplada de PC i una de mòbil, calculant el `display` de l'enllaç i de tots
els seus antecessors (veure css_cascade.py).

Si algú torna a compilar el SCSS i trenca la regla, aquest test falla.
"""
import os

import transaction
from bs4 import BeautifulSoup
from plone.testing.zope import Browser
from zope.component import getMultiAdapter

import genweb6.organs
import genweb6.theme
import unittest

from genweb6.organs.testing import GENWEB6_ORGANS_FUNCTIONAL_TESTING
from genweb6.organs.tests.css_cascade import describe
from genweb6.organs.tests.css_cascade import Stylesheets


DESKTOP = 1280
TABLET = 800      # <= 992px: genweb6.theme ja mostra la capçalera mòbil
MOBILE = 375

THEME_CSS = os.path.join(os.path.dirname(genweb6.theme.__file__),
                         'theme', 'stylesheets', 'theme.min.css')
ORGANS_CSS = os.path.join(os.path.dirname(genweb6.organs.__file__),
                          'theme', 'stylesheets', 'theme-organs.min.css')


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


_CSS = []


def stylesheets():
    """CSS del tema i després el bundle d'organs (mateix ordre que la pàgina).
    Es carrega un sol cop (el runner de Zope no crida setUpClass)."""
    if not _CSS:
        _CSS.append(Stylesheets(_read(THEME_CSS), _read(ORGANS_CSS)))
    return _CSS[0]


class HeaderLoginCssTestCase(unittest.TestCase):

    layer = GENWEB6_ORGANS_FUNCTIONAL_TESTING

    def setUp(self):
        self.css = stylesheets()
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        request = self.layer['request']
        setupview = getMultiAdapter((self.portal, request), name='setup-view')
        setupview.apply_default_language_settings()
        setupview.setup_multilingual()
        setupview.createContent()
        transaction.commit()

        browser = Browser(self.app)
        browser.handleErrors = False
        browser.open(self.portal.absolute_url() + '/ca')
        self.soup = BeautifulSoup(browser.contents, 'lxml')
        self.header = self.soup.select_one('#header')
        self.assertIsNotNone(self.header, "La pàgina no té #header (viewlet genweb.header)")

    # ------------------------------------------------------------------
    def desktop_login(self):
        links = [a for a in self.soup.select('#portal-navbar #portal-globalnav li.nav-action a')
                 if 'login' in (a.get('href') or '') or 'login' in (a.get('id') or '')]
        self.assertTrue(links, 'No hi ha enllaç de login al menú de PC (#portal-globalnav li.nav-action)')
        return links[0]

    def mobile_login(self):
        link = self.soup.select_one('#portal-navbar-mobile a#personaltools-login-mobile')
        self.assertIsNotNone(link, 'No hi ha a#personaltools-login-mobile al menú mòbil')
        return link

    def open_mobile_menu(self):
        """Simula obrir l'offcanvas (botó hamburguesa)."""
        offcanvas = self.soup.select_one('#gwMobileNavbar')
        offcanvas['class'] = (offcanvas.get('class') or []) + ['show']

    def assertVisible(self, element, width, label):
        hidden = self.css.hidden_by(element, width)
        if hidden:
            node, selector = hidden
            self.fail('{0} NO és visible a {1}px: {2} té display:none per la regla `{3}`'.format(
                label, width, describe(node), selector))

    def assertHidden(self, element, width, label):
        self.assertIsNotNone(self.css.hidden_by(element, width),
                             '{0} hauria d\'estar amagat a {1}px'.format(label, width))

    # ------------------------------------------------------------------
    # Login visible
    # ------------------------------------------------------------------
    def test_login_visible_on_desktop(self):
        self.assertVisible(self.desktop_login(), DESKTOP, 'El login de PC')

    def test_login_visible_on_mobile(self):
        self.open_mobile_menu()
        toggler = self.soup.select_one('#portal-navbar-mobile button.navbar-toggler')
        self.assertVisible(toggler, MOBILE, 'El botó del menú mòbil')
        self.assertVisible(self.mobile_login(), MOBILE, 'El login de mòbil')

    def test_login_visible_on_tablet(self):
        self.open_mobile_menu()
        self.assertVisible(self.mobile_login(), TABLET, 'El login de mòbil (tauleta)')

    # ------------------------------------------------------------------
    # Comprovacions del propi evaluador (si fallen, el test no és fiable)
    # ------------------------------------------------------------------
    def test_sanity_desktop_menu_hidden_on_mobile(self):
        self.assertHidden(self.desktop_login(), MOBILE, 'El login de PC')

    def test_sanity_mobile_menu_hidden_on_desktop(self):
        self.assertHidden(self.soup.select_one('#portal-navbar-mobile'), DESKTOP, 'El menú mòbil')

    def test_sanity_detects_broken_organs_rule(self):
        """Mutació: sense l'excepció `:has(a#personaltools-login-mobile)` del
        CSS d'organs, el login de mòbil quedaria amagat. Si el test no ho
        detecta, l'avaluador no serveix."""
        organs = _read(ORGANS_CSS)
        exception = ',#header .navbar-nav .nav-item:not(.nav-action):has(a#personaltools-login-mobile)'
        self.assertIn(exception, organs,
                      "No trobo l'excepció del login al CSS d'organs compilat")
        broken = Stylesheets(_read(THEME_CSS), organs.replace(exception, ''))
        self.open_mobile_menu()
        hidden = broken.hidden_by(self.mobile_login(), MOBILE)
        self.assertIsNotNone(hidden, 'Amb la regla trencada el login hauria de quedar amagat')
        self.assertIn('nav-item:not(.nav-action)', hidden[1])
