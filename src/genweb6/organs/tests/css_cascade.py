# -*- coding: utf-8 -*-
"""Evaluador mínim de CSS per a tests: calcula `display` d'un element.

No és un navegador: només resol la propietat `display` aplicant
- les regles de fulls CSS compilats (minificats),
- @media per amplada (min-width / max-width), ignorant print,
- la cascada: !important > especificitat > ordre,
- l'herència de "no visible": si un antecessor té display:none, l'element
  tampoc es veu.

Els selectors s'avaluen amb soupsieve (suporta :not, :has, :first-child...).
Selectors amb pseudo-elements o pseudo-classes dinàmiques (:hover, :focus...)
s'ignoren: no apliquen a l'estat inicial de la pàgina.
"""
import re

import soupsieve as sv


DYNAMIC_PSEUDO = re.compile(
    r'::|:(hover|focus|focus-visible|focus-within|active|visited|target|'
    r'checked|disabled|enabled|placeholder-shown|invalid|valid|autofill|'
    r'-webkit-[\w-]+|-moz-[\w-]+|-ms-[\w-]+)\b')


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------
def _strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def _find_block_end(css, start):
    """Índex del '}' que tanca el bloc que comença a `start` ('{')."""
    depth = 0
    i = start
    in_str = None
    while i < len(css):
        ch = css[i]
        if in_str:
            if ch == '\\':
                i += 2
                continue
            if ch == in_str:
                in_str = None
        elif ch in ('"', "'"):
            in_str = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(css) - 1


def parse_rules(css, media=()):
    """Retorna [(media_tuple, selector_text, declarations_text)]."""
    css = _strip_comments(css)
    rules = []
    i = 0
    while i < len(css):
        brace = css.find('{', i)
        if brace == -1:
            break
        prelude = css[i:brace].strip()
        end = _find_block_end(css, brace)
        body = css[brace + 1:end]
        # Sentències @import/@charset sense bloc abans del prelude
        while prelude.startswith('@') and ';' in prelude and not prelude.startswith(('@media', '@supports', '@layer', '@container')):
            prelude = prelude.split(';', 1)[1].strip()
        if prelude.startswith('@media'):
            rules.extend(parse_rules(body, media + (prelude[6:].strip(),)))
        elif prelude.startswith(('@supports', '@layer', '@container')):
            rules.extend(parse_rules(body, media))
        elif prelude.startswith('@'):
            pass  # @font-face, @keyframes, @page...
        elif prelude:
            rules.append((media, prelude, body))
        i = end + 1
    return rules


def media_matches(query, width):
    """Avalua una media query (llista separada per comes) per a una amplada."""
    for part in query.split(','):
        part = part.strip().lower()
        if not part:
            continue
        negate = part.startswith('not ')
        if negate:
            part = part[4:]
        if 'print' in part or 'speech' in part:
            ok = False
        else:
            ok = True
            for feature, value in re.findall(r'\(\s*([a-z-]+)\s*(?::\s*([^)]+))?\)', part):
                if feature in ('min-width', 'max-width'):
                    m = re.match(r'([\d.]+)\s*(px|em|rem)?', value or '')
                    if not m:
                        ok = False
                        break
                    px = float(m.group(1)) * (16 if m.group(2) in ('em', 'rem') else 1)
                    if feature == 'min-width' and width < px:
                        ok = False
                    if feature == 'max-width' and width > px:
                        ok = False
                elif feature in ('prefers-reduced-motion', 'prefers-color-scheme',
                                 'forced-colors', 'prefers-contrast'):
                    ok = False  # preferències no actives per defecte
                elif feature in ('min-height', 'max-height', 'orientation',
                                 'hover', 'pointer', 'any-hover', 'any-pointer',
                                 'min-resolution', '-webkit-min-device-pixel-ratio'):
                    pass  # no afecten la decisió de display per amplada
                else:
                    pass
        if negate:
            ok = not ok
        if ok:
            return True
    return False


def _display_decl(body):
    """Valor de `display` del bloc (l'últim guanya) i si és !important."""
    found = None
    for decl in body.split(';'):
        if ':' not in decl:
            continue
        prop, value = decl.split(':', 1)
        if prop.strip().lower() == 'display':
            value = value.strip()
            important = '!important' in value.replace(' ', '')
            value = value.replace('!important', '').replace('! important', '').strip()
            found = (value, important)
    return found


# ----------------------------------------------------------------------
# Especificitat
# ----------------------------------------------------------------------
def _split_top_level(text, sep=','):
    parts, depth, cur = [], 0, ''
    for ch in text:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def specificity(selector):
    a = b = c = 0
    s = selector
    # Pseudo-classes amb arguments: :not/:is/:has -> màxim dels arguments; :where -> 0
    while True:
        m = re.search(r':(not|is|has|where|matches)\(', s)
        if not m:
            break
        start = m.end() - 1
        depth, j = 0, start
        while j < len(s):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        inner = s[start + 1:j]
        if m.group(1) != 'where':
            best = max((specificity(x) for x in _split_top_level(inner)), default=(0, 0, 0))
            a, b, c = a + best[0], b + best[1], c + best[2]
        s = s[:m.start()] + ' ' + s[j + 1:]
    s = re.sub(r'\[[^\]]*\]', lambda _: ' .attr ', s)
    a += len(re.findall(r'#[\w-]+', s))
    b += len(re.findall(r'\.[\w-]+', s))
    b += len(re.findall(r'(?<!:):[\w-]+', s))
    c += len(re.findall(r'::[\w-]+', s))
    c += len(re.findall(r'(?:^|[\s>+~(])([a-zA-Z][\w-]*)', s))
    return (a, b, c)


# ----------------------------------------------------------------------
# Cascada
# ----------------------------------------------------------------------
class Stylesheets(object):
    """Fulls CSS carregats en ordre (com a la pàgina)."""

    def __init__(self, *css_texts):
        self.rules = []
        order = 0
        for css in css_texts:
            for media, selector_text, body in parse_rules(css):
                decl = _display_decl(body)
                if decl is None:
                    continue
                for selector in _split_top_level(selector_text):
                    if DYNAMIC_PSEUDO.search(selector):
                        continue
                    try:
                        compiled = sv.compile(selector)
                    except Exception:
                        continue
                    self.rules.append((media, selector, compiled, decl, specificity(selector), order))
                    order += 1

    def display(self, element, width):
        """`display` calculat de l'element (sense herència) per a una amplada."""
        best = None
        for media, selector, compiled, (value, important), spec, order in self.rules:
            if media and not all(media_matches(q, width) for q in media):
                continue
            try:
                if not compiled.match(element):
                    continue
            except Exception:
                continue
            key = (important, spec, order)
            if best is None or key > best[0]:
                best = (key, value, selector)
        return (best[1], best[2]) if best else (None, None)

    def hidden_by(self, element, width):
        """Retorna (element, selector) del primer antecessor (o ell mateix)
        amb display:none, o None si és visible."""
        node = element
        while node is not None and getattr(node, 'name', None) not in (None, '[document]'):
            value, selector = self.display(node, width)
            if value == 'none':
                return node, selector
            # L'atribut hidden també amaga (estil UA), llevat que el CSS digui el contrari
            if node.has_attr('hidden') and value is None:
                return node, '[hidden]'
            node = node.parent
        return None


def describe(node):
    ident = node.get('id')
    classes = '.'.join(node.get('class') or [])
    return '<{0}{1}{2}>'.format(
        node.name, '#' + ident if ident else '', '.' + classes if classes else '')
