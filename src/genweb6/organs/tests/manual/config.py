# -*- coding: utf-8 -*-
"""Càrrega de la configuració dels tests contra PRE.

Llegeix tests/manual/manual_settings.env (no versionat) i/o variables d'entorn.
Les variables d'entorn tenen prioritat sobre el fitxer.
"""
from types import SimpleNamespace

import os


HERE = os.path.dirname(__file__)
ENV_FILE = os.environ.get('ORGANS_PRE_ENV', os.path.join(HERE, 'manual_settings.env'))


def _read_env_file(path):
    values = {}
    if not os.path.exists(path):
        return values
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load():
    values = _read_env_file(ENV_FILE)
    for key in list(values) + [k for k in os.environ if k.startswith(('GDOC_', 'PRE_', 'LOCAL_', 'LDAP_'))]:
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


CONFIG = load()
# La bateria només es llança manualment; si falta configuració, se salta
# indicant quines claus falten.
ENABLED = True
SKIP_REASON = 'Falta configuració a tests/manual/manual_settings.env (veure manual_settings.env.example)'


def require(*keys):
    """Retorna True si totes les claus tenen valor."""
    return ENABLED and all(CONFIG.get(k) for k in keys)


def ldap_bind_password():
    """Contrasenya del bind de ldapUPC: LDAP_BIND_PASSWORD o, si no hi és,
    la variable d'entorn ldapbindpasswd (la que rep la instància via buildout)."""
    return CONFIG.get('LDAP_BIND_PASSWORD') or os.environ.get('ldapbindpasswd', '')


def firma_settings():
    """Settings amb la mateixa forma que IFirmaDocumentalSettings."""
    c = CONFIG
    return SimpleNamespace(
        gdoc_url=c.get('GDOC_URL', '').rstrip('/'),
        gdoc_user=c.get('GDOC_USER', ''),
        gdoc_hash=c.get('GDOC_HASH', ''),
        gdoc_fons_id=c.get('GDOC_FONS_ID', ''),
        codiexpedient_url=c.get('CODIEXPEDIENT_URL', '').rstrip('/'),
        codiexpedient_apikey=c.get('CODIEXPEDIENT_APIKEY', ''),
        portafirmes_url=c.get('PORTAFIRMES_URL', '').rstrip('/'),
        portafirmes_apikey=c.get('PORTAFIRMES_APIKEY', ''),
        copiesautentiques_url=c.get('COPIESAUTENTIQUES_URL', '').rstrip('/'),
        copiesautentiques_apikey=c.get('COPIESAUTENTIQUES_APIKEY', ''),
        signaturacsv_url=c.get('SIGNATURACSV_URL', '').rstrip('/'),
        signaturacsv_apikey=c.get('SIGNATURACSV_APIKEY', ''),
    )
