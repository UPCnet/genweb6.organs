# 🧪 Tests de genweb6.organs - Guía de Ejecución

Esta guía documenta cómo ejecutar los tests de permisos implementados para `genweb6.organs`.

## 📋 Índice de Tests Implementados

### ✅ Tests de Permisos Completos

1. **test_create_sessions.py**
   - Verifica quién puede crear sesiones
   - Cubre los 3 tipos de órganos

2. **test_file_permission_in_organs_oberts.py**
   - Permisos de archivos (visiblefile/hiddenfile) en órganos abiertos
   - Todos los roles + anónimos

3. **test_file_permission_in_organs_restricted_to_membres.py**
   - Permisos de archivos en órganos restringidos a miembros
   - Regla especial: OG3-Membre/OG5-Convidat solo ven hiddenfile

4. **test_file_permission_in_organs_restricted_to_afectats.py**
   - Permisos de archivos en órganos restringidos a afectados
   - Reglas especiales para OG3-Membre y OG4-Afectat

5. **test_actes_view_permission_in_organs_oberts.py**
   - Vista de actas/audios en órganos abiertos
   - Todos los roles, todos los estados

6. **test_actes_view_permission_in_organs_restricted_to_membres.py** ⭐ NUEVO
   - Vista de actas/audios en órganos restringidos a miembros
   - OG4-Afectat sin acceso

7. **test_actes_view_permission_in_organs_restricted_to_afectats.py** ⭐ NUEVO
   - Vista de actas/audios en órganos restringidos a afectados
   - OG4-Afectat sin acceso a actas

8. **test_content_type_permissions.py** ⭐ ACTUALIZADO
   - Permisos CRWDE sobre tipos de contenido
   - Por estado de sesión (PLANIFICADA, CONVOCADA, REALITZADA, TANCADA, EN_CORRECCIO)
   - Cobertura: 5/5 estados (100%)

9. **test_organ_permissions.py** ⭐ NUEVO
   - Permisos RWD sobre el órgano
   - Todos los roles + anónimos

10. **test_organ_tabs.py** ⭐ NUEVO
    - Visibilidad de pestañas del órgano (Sessions, Actes, FAQ)
    - Todos los roles + anónimos
    - 8 tests implementados

11. **test_session_actions_by_state.py** ⭐ NUEVO
    - Acciones sobre sesiones por estado de workflow
    - Convoca, Realitza, Excusa, Missatge, Presentació, Historial
    - 22 tests implementados

12. **test_organ_actions.py** ⭐ NUEVO
    - Acciones sobre el órgano (Crear sessió, Numera, Exportar acords)
    - Verificación de métodos viewOrdena, viewExportAcords
    - 12 tests implementados

13. **test_acta_actions.py** ⭐ NUEVO
    - Acciones sobre actas (Vista prèvia, Imprimeix)
    - Todos los roles según estado y tipo de órgano
    - 9 tests implementados

14. **test_votaciones.py** ⭐ NUEVO
    - Sistema de votaciones completo
    - Obrir/Tancar votació, Botons per votar, Resultados
    - 12 tests implementados

15. **test_quorum.py** ⭐ NUEVO
    - Sistema de quorum completo
    - Gestionar/Añadir/Eliminar quorum
    - Permisos para Manager, OG1-Secretari, OG2-Editor, OG3-Membre
    - 12 tests implementados

16. **test_document_fitxer_permissions_in_punt.py** ⭐ NUEVO
    - Permisos para crear Document/Fitxer dentro de Punts
    - OG2-Editor puede crear en PLANIFICADA, CONVOCADA, REALITZADA, EN_CORRECCIO
    - OG2-Editor NO puede crear en TANCADA (solo RW)
    - OG3-Membre solo READ en estados CONVOCADA+
    - 13 tests implementados

17. **test_manager_permissions.py** ⭐ BAJA PRIORIDAD
    - Verificación explícita de permisos del rol Manager
    - Acceso completo a todos los tipos de órganos y estados
    - Permisos CRWDE completos sin restricciones
    - 7 tests implementados (6 funcionales + 1 resumen)

18. **test_annex_permissions.py** ⭐ BAJA PRIORIDAD
    - Verificación de estructura de Annex (contenido dentro de Acta)
    - Annex hereda permisos de su Acta contenedora
    - Verificación de creación y estructura en todos los estados
    - 6 tests implementados (5 funcionales + 1 resumen)

19. **test_end_to_end_workflow.py** ⭐ BAJA PRIORIDAD
    - Tests End-to-End de flujos completos
    - Flujo básico: Crear → Convocar → Realizar → Cerrar
    - Flujo con votación: Incluye acuerdos y votaciones
    - Flujo completo: Múltiples puntos, acuerdos, documentos y actas
    - 5 tests implementados (4 funcionales + 1 resumen)

20. **test_search_own_organs_regression.py** ⭐ NUEVO - REGRESSION TEST
    - Test de regresión para bug de roles locales (brain vs objeto)
    - Verifica que `getOwnOrgans()` en search.py usa objeto real
    - Prueba usuarios con/sin roles, múltiples órganos, color por defecto
    - 9 tests funcionales implementados

21. **test_portlet_lamevavinculacio.py** ⭐ NUEVO - REGRESSION TEST
    - Test de regresión para portlet "La Meva Vinculació"
    - Verifica consistencia con search.py (mismo patrón brain/objeto)
    - Verifica optimizaciones (sin doble getObject)
    - 3 tests de integración implementados

### ✅ Tests de lógica de negocio (noviembre 2026)

Además de permisos, estos ficheros prueban **qué hace** el código. Usan la base común
`base.py` (ver más abajo).

22. **test_votacions_flux.py** — 37 tests
    - Abrir / cerrar / reabrir / anular votaciones, acuerdos y esmenas
    - Varias votaciones abiertas a la vez; no se puede votar con la votación cerrada
    - **Correo de voto** (destinatario, remitente `organ.fromMail`, asunto, cuerpo con el sentido del voto), en acuerdo de sesión, de punto y en esmena
    - **Correo de anulación** (Bcc a los votantes, solo en sesiones no realizadas/cerradas)
    - Recuentos de `@@reloadVoteStats` según rol, permisos reales de las vistas, persistencia en ZODB

23. **test_quorum_flux.py** — 23 tests
    - Abrir / cerrar / numerar quórums, registrar asistencia sin duplicados, eliminar
    - `checkHasQuorum`, `showOpenQuorum`, persistencia en ZODB
    - Quórum y votación son independientes (se puede votar sin estar en el quórum)

24. **test_mails_sessio.py** — 18 tests
    - `mail_convocar` (pre-relleno ca/es/en, envío, transición a convocada, log), `mail_informar`, `mail_message`
    - `excusar_assist_sessio` (registra la excusa, no envía correo), permisos

25. **test_firma_client_unit.py** — 19 tests (sin red)
    - `ClientFirma` con `requests` simulado: URLs, cabeceras `X-Api-Key`, payloads, timeouts y errores → `ClientFirmaException`

26. **test_firma_local.py** — 20 tests (sin red)
    - Callback de Portafirmes `@@updateInfoPortafirmes` (signada, rebutjada, cancelada ignorada, órgano restringido)
    - `estatFirmaActa`, `hasFirmaActa`, permisos locales del acta firmada, aviso al modificar una sesión firmada

27. **test_utils_logic.py** — 22 tests
    - Unitarios: `checkhasRol`, `canViewSessionState`, `normalize_url`, `get_date_range`
    - `canViewAcord/Punt/Subpunt` coherentes con la matriz `SESSION_VIEW_ROLES` (3 tipos × 5 estados × 5 roles)
    - `get_organ/get_session/get_acord`, colores de estado, log, renumeración al borrar, `@@exportCSV`

28. **test_ordre_dia_views.py** — 16 tests
    - `@@deleteElement` / `@@removeElement`, `@@fcmoveTable` (mover puntos y subpuntos), `@@changeActualState` / `@@changeSubpuntState`

29. **test_setuphandlers_ldap.py** — 6 tests (sin red)
    - `ldapUPC` activo y **primero en IPropertiesPlugin** tras `setup_ldapupc_properties_plugin` y tras el `setupVarious` del perfil.
      Si no, `member.getProperty('email')` no devuelve el email del LDAP y no salen los correos de voto.

30. **test_header_login_css.py** — 6 tests (sin navegador)
    - El enlace **Identifica't** de la cabecera es visible en **PC (1280px)**, **tablet (800px)** y **móvil (375px, menú abierto)**
    - Renderiza la página como anónimo y evalúa los CSS compilados que se sirven (`genweb6.theme` `theme.min.css` + `theme-organs.min.css`) con `css_cascade.py`: `@media` por ancho, `!important`, especificidad, orden y `display:none` de los antecesores
    - Protege la regla de `_generic.scss` (commit 5d2ca1a). Si se recompila el SCSS y se rompe, falla indicando qué elemento y qué regla lo ocultan
    - Incluye una prueba de mutación: sin la excepción `:has(a#personaltools-login-mobile)` el test detecta el login oculto

### 🔒 Batería manual `manual/` (NO se ejecuta con `bin/test`)

Ver la sección [Batería manual](#-batería-manual-firma-pre-y-correos-de-voto-con-usuario-ldap).

## 🚀 Comandos de Ejecución

### Ejecutar TODOS los tests

```bash
cd organs6.buildout   # raíz del buildout
./bin/test -s genweb6.organs
```

### Ejecutar tests específicos

#### Tests de creación de sesiones
```bash
./bin/test -s genweb6.organs -t test_create_sessions
```

#### Tests de permisos de archivos
```bash
# Órganos abiertos
./bin/test -s genweb6.organs -t test_file_permission_in_organs_oberts

# Órganos restringidos a miembros
./bin/test -s genweb6.organs -t test_file_permission_in_organs_restricted_to_membres

# Órganos restringidos a afectados
./bin/test -s genweb6.organs -t test_file_permission_in_organs_restricted_to_afectats
```

#### Tests de vista de actas
```bash
# Órganos abiertos
./bin/test -s genweb6.organs -t test_actes_view_permission_in_organs_oberts

# Órganos restringidos a miembros ⭐ NUEVO
./bin/test -s genweb6.organs -t test_actes_view_permission_in_organs_restricted_to_membres

# Órganos restringidos a afectados ⭐ NUEVO
./bin/test -s genweb6.organs -t test_actes_view_permission_in_organs_restricted_to_afectats
```

#### Tests de permisos CRWDE ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_content_type_permissions
```

#### Tests de permisos sobre órganos ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_organ_permissions
```

#### Tests de pestañas del órgano ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_organ_tabs
```

#### Tests de acciones sobre sesiones por estado ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_session_actions_by_state
```

#### Tests de acciones sobre el órgano ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_organ_actions
```

#### Tests de acciones sobre actas ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_acta_actions
```

#### Tests de votaciones ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_votaciones
```

#### Tests de quorum ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_quorum
```

#### Tests de Document/Fitxer en Punts ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_document_fitxer_permissions_in_punt
```

#### Tests de Manager (baja prioridad) ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_manager_permissions
```

#### Tests de Annex (baja prioridad) ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_annex_permissions
```

#### Tests End-to-End (baja prioridad) ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_end_to_end_workflow
```

#### Tests de Regresión - Roles Locales ⭐ NUEVO
```bash
# Test de regresión search.py (9 tests)
./bin/test -s genweb6.organs -t test_search_own_organs_regression

# Test de regresión portlet (3 tests)
./bin/test -s genweb6.organs -t test_portlet_lamevavinculacio

# Ejecutar ambos tests de regresión (12 tests)
./bin/test -s genweb6.organs -t test_search_own_organs_regression -t test_portlet_lamevavinculacio
```

#### Solo los tests nuevos (noviembre 2026) — 167 tests, ~5 min
```bash
./bin/test -s genweb6.organs -m 'test_(votacions_flux|quorum_flux|mails_sessio|firma_client_unit|firma_local|utils_logic|ordre_dia_views|setuphandlers_ldap|header_login_css)$'

# Para ver qué tests entran sin ejecutarlos, añadir --list-tests
```

#### Tests de lógica de negocio (noviembre 2026)
```bash
# Votaciones + correo de voto
./bin/test -s genweb6.organs -t test_votacions_flux

# Quórum
./bin/test -s genweb6.organs -t test_quorum_flux

# Correos de la sesión
./bin/test -s genweb6.organs -t test_mails_sessio

# Firma documental sin red (cliente HTTP simulado + lógica local)
./bin/test -s genweb6.organs -t test_firma_client_unit -t test_firma_local

# Utilidades, permisos y orden del día
./bin/test -s genweb6.organs -t test_utils_logic -t test_ordre_dia_views

# Configuración ldapUPC (email para los correos de voto)
./bin/test -s genweb6.organs -t test_setuphandlers_ldap

# Login visible en la cabecera (PC / tablet / móvil)
./bin/test -s genweb6.organs -t test_header_login_css
```

#### Ejecutar todos los tests ultra-exhaustivos (baja prioridad) ⭐ NUEVO
```bash
# Ejecutar los 3 tests de baja prioridad (Manager, Annex, E2E)
./bin/test -s genweb6.organs -t "test_manager_permissions|test_annex_permissions|test_end_to_end_workflow"
```

#### Ejecutar todos los tests de acciones y UI (88 tests) ⭐ NUEVO
```bash
./bin/test -s genweb6.organs -t test_organ_tabs -t test_session_actions_by_state -t test_organ_actions -t test_acta_actions -t test_votaciones -t test_quorum -t test_document_fitxer_permissions_in_punt
```

### Ejecutar con verbosidad

```bash
# Ver detalles de ejecución
./bin/test -s genweb6.organs -vvv

# Ver solo nombres de tests
./bin/test -s genweb6.organs -v
```

### Ejecutar con coverage

```bash
# Coverage con reporte
./bin/test -s genweb6.organs --coverage=coverage_report

# Ver el reporte generado
# El reporte se guarda en la carpeta coverage_report/
```

### Ejecutar solo un test específico

```bash
# Ejecutar un solo método de test
./bin/test -s genweb6.organs -t test_secretari_permissions_in_planificada
```

## 🔒 Batería manual: firma PRE y correos de voto con usuario LDAP

Tests que dependen de servicios reales o de credenciales. Están en `tests/manual/` y sus
ficheros empiezan por `manual_`, así que **el `bin/test` normal (y el CI) no los descubre**.
Solo se lanzan a mano:

```bash
./bin/test -s genweb6.organs --tests-pattern='^manual$' --test-file-pattern='^manual_'
```

| Fichero | Qué prueba | Necesita |
|---------|-----------|----------|
| `manual_firma_pre.py` | `ClientFirma` contra los servicios de **PRE**: código de expediente, gDOC (crear expediente, subir, consultar), Signatura CSV, Portafirmes (enviar y cancelar), Còpies Autèntiques. Limpia lo que crea. | Claves `GDOC_*`, `CODIEXPEDIENT_*`, `PORTAFIRMES_*`, `SIGNATURACSV_*`, `COPIESAUTENTIQUES_*`, `GDOC_SERIE_TEST`, `GDOC_AUTHOR_TEST`, `PRE_SIGNANT` |
| `manual_vots_ldap.py` | Tu **usuario UPC real**, en local (no toca ningún Plone de PRE): crea `ldapUPC`, login HTTP contra el LDAP, email leído del LDAP, voto y **correo de voto/anulación a ese email** | `LOCAL_USER`, `LOCAL_PASSWORD`, `LDAP_BIND_PASSWORD` (o variable `ldapbindpasswd`), red hacia ldap.upc.edu:636 |

**Configuración**: copiar `manual/manual_settings.env.example` a `manual/manual_settings.env` y rellenar.
- `manual_settings.env` está en `.gitignore`: **no se sube**. No usar `git add -f`.
- Recomendado: `chmod 600 src/genweb6/organs/tests/manual/manual_settings.env`.
- Los tests sin la configuración que necesitan se **saltan** indicando qué falta.
- Las variables de entorno con el mismo nombre tienen prioridad sobre el fichero.

**Qué NO se comprueba en PRE**: que el acta acabe firmada/rechazada. Lo resuelve Portafirmes de forma
asíncrona; esa parte se cubre en `test_firma_local.py` simulando el callback.

Los correos **no se envían nunca**: se capturan y se imprimen por consola (como
`Products.PrintingMailHost` en la instancia local).

## 🧱 Base común para tests nuevos (`base.py`)

`OrgansFunctionalTestCase` (capa funcional) prepara en cada test:
- Carpeta de órganos + órgano (`organ_type = 'open_organ'` por defecto, `fromMail = organ@example.com`)
- Usuarios con email y rol local sobre el órgano: `secretari`, `editor`, `membre1..3`, `afectat`, `convidat`, `membre_sense_email`
- `RecordingMailHost`: captura correos **y destinatarios del sobre** (MailHost elimina la cabecera `Bcc`)

Helpers:
```python
session = self.create_session('realitzada')      # aplica las transiciones necesarias
punt = self.create_punt(session)
acord = self.create_acord(punt)
esmena = self.create_esmena(acord)

with self.as_user('membre1'):
    self.call_view(acord, 'favorVote')            # restrictedTraverse: comprueba permisos

self.call_view(session, 'mail_message', method='POST', **form)   # formularios z3c.form
mails = self.sent_mails()                         # .mfrom .mto .subject .body .recipients
```

Notas:
- Los formularios z3c.form se envían con `method='POST'`; con GET el parche de Plone ignora el request.
- Crear una sesión ya deja una entrada en el log (`New session created`).
- El runner no descubre subcarpetas de `tests/`: los tests normales van en `tests/test_*.py`.

## 🐞 Fallos conocidos (`@unittest.expectedFailure`)

Son bugs reales detectados por los tests. La suite pasa en verde; cuando se corrija el bug, el test
saldrá como *unexpected success* y hay que **quitar el decorador**.

| Test | Bug |
|------|-----|
| `test_votacions_flux::test_reload_stats_unknown_uid` | `@@reloadVoteStats` con UID inexistente devuelve `False` y `json_response` peta (error 500) |
| `test_mails_sessio::test_convocar_prefill_es_includes_modality` | `mail_convocar` en castellano no añade la modalidad (falta `moreData +=`) |
| `test_mails_sessio::test_convocar_prefilled_body_links` | Enlaces `----@@----http://…` quedan como `http:///…` — **a confirmar en navegador** (depende de TinyMCE) |
| `test_firma_client_unit::test_http_error_non_json_body` | Error HTTP con cuerpo no JSON lanza `JSONDecodeError` en vez de `ClientFirmaException` |
| `test_firma_local::test_estat_firma_acta_without_state` | `estatFirmaActa` sin estado: `estats_map.get['pendent']` → `TypeError` |

## 📊 Interpretación de los Prints

Los tests incluyen prints informativos con emojis para facilitar el seguimiento:

### Emojis utilizados

- ✅ **Verde**: Test de permisos permitidos (debería tener acceso)
- ❌ **Rojo**: Test de restricciones (NO debería tener acceso)
- ✓ **Checkmark**: Verificación individual exitosa
- ⚠️ **Warning**: Advertencia o nota informativa
- 📊 **Gráfico**: Resumen de permisos
- 🐛 **Bug**: Test de regresión para prevenir bugs conocidos
- 🔍 **Lupa**: Verificación de consistencia entre componentes
- ⚡ **Rayo**: Optimizaciones de performance
- ℹ️ **Info**: Información de debug

### Ejemplo de output

```
✅ Verificando permisos del rol OG1-Secretari en órgano membres
  ✓ Verificando acceso en sesión PLANIFICADA
  ✓ Acceso correcto a actas en sesión PLANIFICADA
  ✓ Verificando acceso en sesión CONVOCADA
  ✓ Acceso correcto a actas en sesión CONVOCADA
  ✓ Verificación completa como OG1-Secretari

❌ Verificando restricciones del rol OG3-Membre en órgano membres
  ✓ Verificando restricciones en sesión PLANIFICADA
  ✓ Acceso denegado correctamente en sesión PLANIFICADA
  ✓ Verificando acceso permitido en sesión CONVOCADA
  ✓ Acceso permitido en sesión CONVOCADA
  ✓ Verificación completa como OG3-Membre

🐛 REGRESSION TEST: Brain vs Objeto para roles locales
======================================================================
  ❌ Probando api.user.get_roles() con BRAIN del catálogo:
     Roles devueltos: ['Member', 'Authenticated']
     ✓ Brain NO tiene roles locales (comportamiento esperado)

  ✅ Probando api.user.get_roles() con OBJETO REAL:
     Roles devueltos: ['OG1-Secretari', 'Member', 'Authenticated']
     ✓ Objeto real SÍ tiene roles locales (correcto)
     ✓ getOwnOrgans() usa objeto real correctamente

  ✅ REGRESSION TEST PASADO: Bug de brain vs objeto no ocurre
======================================================================
```

## 🔍 Debugging

### Ejecutar con ipdb

Si un test falla y quieres debuggear:

```bash
# Ejecutar con debugger automático en errores
./bin/test -s genweb6.organs --ipdb
```

### Ver logs detallados

```bash
# Ejecutar con verbosidad máxima
./bin/test -s genweb6.organs -vvv
```

### Ejecutar un solo test con debug

```bash
# Añadir ipdb.set_trace() en el código del test
import ipdb; ipdb.set_trace()

# Ejecutar el test
./bin/test -s genweb6.organs -t nombre_del_test
```

## 📝 Notas Importantes

### Request del Layer

Los tests usan `self.request = self.layer['request']` en lugar de crear un `TestRequest()`.
Esto es crítico para tests funcionales en Plone 6.

### Warnings Suprimidos

Los tests suprimen warnings molestos:
- `ResourceWarning`: Archivos blob no cerrados explícitamente
- `DeprecationWarning`: Avisos de deprecación de Plone

### Logout entre Tests

Todos los tests hacen `logout()` al inicio y al final para aislar estados.

### Estados de Workflow

Los tests cubren 5 estados de sesión:
1. `planificada` (estado inicial)
2. `convocada` (transición: convocar)
3. `realitzada` (transiciones: convocar, realitzar)
4. `tancada` (transiciones: convocar, realitzar, tancar)
5. `en_correccio` (transiciones: convocar, realitzar, tancar, corregir)

## 🎯 Permisos Verificados

### Por Rol

| Rol | Permisos sobre Órgano | Crear Sesiones | Actas | Archivos |
|-----|----------------------|----------------|-------|----------|
| **OG1-Secretari** | RWD | ✅ | ✅ Todos | ✅ Todos |
| **OG2-Editor** | RW | ✅ | ✅ Todos | ✅ Todos |
| **OG3-Membre** | R | ❌ | ⚠️ Desde CONVOCADA | ⚠️ Reglas especiales |
| **OG4-Afectat** | R | ❌ | ⚠️ Solo TANCADA (open) | ⚠️ Reglas especiales |
| **OG5-Convidat** | R | ❌ | ⚠️ Desde CONVOCADA | ⚠️ Reglas especiales |
| **Anónimo** | R (solo open) | ❌ | ❌ (except open) | ⚠️ Solo visiblefile |

### Por Estado de Sesión

#### PLANIFICADA
- Solo OG1-Secretari y OG2-Editor
- CRWDE (Secretari) / CRWE (Editor)

#### CONVOCADA, REALITZADA, EN_CORRECCIO
- OG1-Secretari: CRWDE
- OG2-Editor: CRWE
- Otros roles: R (solo lectura)

#### TANCADA
- OG1-Secretari: RWDE (sin Create)
- OG2-Editor: RWE (sin Create)
- Otros roles: R (solo lectura)

## 📚 Documentación Relacionada

- **Documento de Permisos**: `docs/resumen_permisos_organs.html`
- **Cobertura de Tests**: `docs/tests_coverage.md`
- **Base común de tests**: `src/genweb6/organs/tests/base.py`
- **Batería manual**: `src/genweb6/organs/tests/manual/`
- **Testing Layer**: `src/genweb6/organs/testing.py`

## 🐛 Troubleshooting

### Test falla con "Unauthorized"

Verifica:
1. ¿El usuario tiene el rol correcto?
2. ¿El rol está asignado al objeto correcto (órgano)?
3. ¿El estado de la sesión es el esperado?

### Test falla con "AttributeError"

Verifica:
1. ¿Los objetos se crearon correctamente en setUp?
2. ¿Las transiciones de workflow se aplicaron?
3. ¿Existe el archivo/contenido que intentas acceder?

### Tests muy lentos

- Los tests funcionales son más lentos que los de integración
- Cada test crea una estructura completa de órgano/sesiones
- Considera ejecutar solo los tests que necesitas durante desarrollo

## 📊 Coverage Report

### Generar reporte de cobertura

```bash
# Desde el directorio del paquete
cd src/genweb6.organs

# Ejecutar coverage con todos los tests
../../bin/coverage run --source=src/genweb6/organs ../../bin/test -s genweb6.organs

# Generar reporte HTML
../../bin/coverage html -d coverage_report

# Abrir en navegador
open coverage_report/index.html
```

### Ejecutar coverage con un test específico

```bash
cd src/genweb6.organs

# Solo test_votaciones
../../bin/coverage run --source=src/genweb6/organs ../../bin/test -s genweb6.organs -t test_votaciones

# Generar reporte
../../bin/coverage html -d coverage_report
```

### Ver reporte en texto

```bash
cd src/genweb6.organs
../../bin/coverage report --show-missing
```

### Configuración Coverage (.coveragerc)

El archivo `.coveragerc` en `src/genweb6.organs/` está configurado correctamente:

```ini
[run]
source = src/genweb6/organs

[report]
include =
    src/genweb6/organs/*

omit =
    */test*
    */tests/*
    */testing/*

[html]
directory = coverage_report
```

## ✅ Checklist antes de Commit

- [ ] Todos los tests pasan: `./bin/test -s genweb6.organs`
- [ ] Coverage generado correctamente (ver comandos arriba)
- [ ] No hay prints de debug olvidados (excepto los informativos)
- [ ] No hay `import ipdb; ipdb.set_trace()` olvidados
- [ ] Los mensajes de commit siguen el formato convencional

## 📊 Resumen de Tests Implementados

**Total: 387 tests en la suite normal** (`./bin/test -s genweb6.organs`), 0 failures, 0 errors
— 5 de ellos marcados como fallo esperado (ver *Fallos conocidos*).
Batería manual aparte: 13 tests (`manual/`).

**Tests de lógica de negocio (noviembre 2026)**:
- ✅ 37 tests - Flujo de votaciones y correo de voto/anulación
- ✅ 23 tests - Flujo de quórum
- ✅ 18 tests - Correos de la sesión
- ✅ 19 tests - Cliente de firma documental (sin red)
- ✅ 20 tests - Firma documental local (callback, estados, permisos)
- ✅ 22 tests - Utilidades, coherencia de permisos, renumeración, ExportCSV
- ✅ 16 tests - Vistas del orden del día
- ✅ 6 tests - Configuración ldapUPC
- ✅ 6 tests - Login visible en la cabecera (PC / tablet / móvil)

**Tests de permisos (21 ficheros originales)**:
- ✅ 8 tests - Pestañas del órgano
- ✅ 22 tests - Acciones sobre sesiones por estado
- ✅ 12 tests - Acciones sobre el órgano
- ✅ 12 tests - Sistema de votaciones
- ✅ 12 tests - Sistema de quorum
- ✅ 9 tests - Acciones sobre actas
- ✅ 13 tests - Document/Fitxer en Punts
- ✅ 8 tests - Permisos CRWDE (5 estados de workflow)
- ✅ 7 tests - Permisos Manager (6 funcionales + 1 resumen)
- ✅ 6 tests - Estructura Annex (5 funcionales + 1 resumen)
- ✅ 5 tests - Flujos End-to-End (4 funcionales + 1 resumen)
- ✅ 9 tests - Regresión search.py (brain vs objeto) ⭐ NUEVO
- ✅ 3 tests - Regresión portlet La Meva Vinculació ⭐ NUEVO
- ✅ Tests adicionales para tipos de órganos y otros casos

**Estado**: ✅ 0 failures, 0 errors
**Cobertura**: ✅ todas las tablas de permisos de `docs/resumen_permisos_organs.html`. La cobertura de
**código** es menor: medirla con `coverage` (ver abajo) antes de fijar un umbral en CI.

### 🐛 Tests de Regresión (Brain vs Objeto)

Los nuevos tests de regresión previenen un bug crítico donde `api.user.get_roles()`
no devolvía roles locales al pasarle un brain del catálogo en lugar del objeto real.

**📚 Documentación técnica completa**: Ver [`docs/BUGFIX_2025-11-27_LOCAL_ROLES.md`](../../docs/BUGFIX_2025-11-27_LOCAL_ROLES.md) para:
- Explicación detallada del problema (código incorrecto vs correcto)
- Debugging paso a paso con ipdb
- Verificación manual con comandos shell
- Conceptos técnicos (brain vs objeto, por qué roles no están en metadata)
- Lecciones aprendidas

**Archivos afectados**:
- `search.py::getOwnOrgans()` - Vista de búsqueda
- `portlet/lamevavinculacio.py::getOwnOrgans()` - Portlet de vinculación

**Bug**: Los roles locales (`__ac_local_roles__`) NO están en metadata del catálogo.
**Solución**: Siempre hacer `organ = obj._unrestrictedGetObject()` antes de
llamar `api.user.get_roles(obj=organ)`.

**Optimizaciones**:
- ✅ Usar metadata del brain (`obj.getURL()`, `obj.Title`) cuando sea posible
- ✅ Solo leer del objeto real lo que NO está en metadata (`eventsColor`, roles)
- ✅ Protección doble contra `None`: `getattr(..., default) or default`

### 🎯 Tests de Quorum

El test de quorum (`test_quorum.py`) verifica 3 permisos específicos:

| Permiso | Manager | OG1-Secretari | OG2-Editor | OG3-Membre | Otros |
|---------|---------|---------------|------------|------------|-------|
| **Gestionar quorum** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Añadir quorum** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Eliminar quorum** | ✅ | ❌ | ❌ | ❌ | ❌ |

**Particularidades**:
- **OG2-Editor**: Puede gestionar pero NO añadir quorum
- **OG3-Membre**: Puede añadir pero NO gestionar quorum
- **Manager**: Único con permiso para eliminar quorum

---

**Última actualización**: 9 Noviembre 2026
**Versión de Plone**: 6.0.15
**Total tests**: 387 en la suite normal (0 failures, 0 errors) + 13 en la batería manual `manual/` ✅
**Bugfix**: ⭐ Bug de roles locales (brain vs objeto) - 12 tests de regresión añadidos

---

## 📌 Resumen rápido

### Automáticos — `./bin/test -s genweb6.organs` (387 tests, también en CI)

Solo los nuevos (167): `./bin/test -s genweb6.organs -m 'test_(votacions_flux|quorum_flux|mails_sessio|firma_client_unit|firma_local|utils_logic|ordre_dia_views|setuphandlers_ldap|header_login_css)$'`

| Qué | Ficheros |
|-----|----------|
| **Permisos y visibilidad** por rol × tipo de órgano × estado (órganos, sesiones, actas, ficheros, pestañas, acciones) | `test_*permission*`, `test_*visibility*`, `test_organ_*`, `test_session_actions_by_state`, `test_acta_actions`, `test_create_sessions`… |
| **Votaciones**: ciclo de vida, votos, recuentos y **correo de voto / anulación** | `test_votaciones`, `test_votacions_flux` |
| **Quórum**: abrir, cerrar, asistencia, persistencia | `test_quorum`, `test_quorum_flux` |
| **Correos de sesión**: convocar, informar, mensaje, excusar | `test_mails_sessio` |
| **Firma documental sin red**: cliente HTTP simulado, callback de Portafirmes, estados y permisos del acta | `test_firma_client_unit`, `test_firma_local` |
| **Lógica**: utilidades, orden del día (borrar / mover / estados), ExportCSV | `test_utils_logic`, `test_ordre_dia_views` |
| **ldapUPC** primero en Properties Plugins (sin él no hay email → no hay correo de voto) | `test_setuphandlers_ldap` |
| **Login visible en la cabecera** en PC, tablet y móvil (evaluando los CSS compilados) | `test_header_login_css` |
| **Regresiones** y flujos end-to-end | `test_search_own_organs_regression`, `test_portlet_lamevavinculacio`, `test_end_to_end_workflow` |

### Manuales — solo a mano, con credenciales (`tests/manual/`, 13 tests)

```bash
./bin/test -s genweb6.organs --tests-pattern='^manual$' --test-file-pattern='^manual_' -vv
```

| Qué | Fichero | Necesita |
|-----|---------|----------|
| **Firma contra PRE**: código de expediente, gDOC, Signatura CSV, Portafirmes (enviar + cancelar), Còpies Autèntiques | `manual_firma_pre.py` | Claves de los servicios de PRE |
| **Correos de voto con tu usuario UPC real**: login LDAP, email del LDAP, voto / cambio / anulación (correos por consola, no se envían) | `manual_vots_ldap.py` | `LOCAL_USER`, `LOCAL_PASSWORD`, bind LDAP |

Credenciales en `tests/manual/manual_settings.env` (ignorado por git; plantilla en `manual_settings.env.example`).
