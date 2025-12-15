# Guía Técnica: Decoradores de Memoización en Plone 6

## 📚 Índice

1. [Introducción](#introducción)
2. [@instance.memoize](#instancememoize)
3. [@view.memoize](#viewmemoize)
4. [Comparativa](#comparativa)
5. [Casos de uso](#casos-de-uso)
6. [Ejemplos prácticos](#ejemplos-prácticos)
7. [Casos Donde NO Funciona: Lecciones Aprendidas](#7-casos-donde-no-funciona-lecciones-aprendidas) ⚠️
8. [Problemas comunes](#8-problemas-comunes)
9. [Referencias](#9-referencias)

---

## 1. Introducción

Los decoradores de memoización (`memoize`) son técnicas de optimización que **cachean** (almacenan en memoria) los resultados de funciones costosas para evitar recalcularlos múltiples veces.

En Plone 6, el paquete `plone.memoize` proporciona varios decoradores especializados para diferentes niveles de caché:

| Decorador | Alcance | Duración | Compartido entre |
|-----------|---------|----------|------------------|
| `@instance.memoize` | Instancia de clase | 1 request | No (por instancia) |
| `@view.memoize` | Vista (BrowserView) | 1 request | No (por vista) |
| `@ram.cache` | RAM del proceso | Hasta invalidación | Sí (dentro del Zope) |

**⚠️ Importante:** En entornos multi-Zope (ZEO), `@ram.cache` **NO se comparte** entre procesos. Para caché distribuida se requiere Redis o Memcached.

---

## 2. @instance.memoize

### 📖 Definición

`@instance.memoize` es un decorador que cachea resultados de métodos **a nivel de instancia de clase** durante la duración de un único request HTTP.

### 🔧 Funcionamiento Interno

```python
from plone.memoize import instance

class MyClass:
    @instance.memoize
    def expensive_method(self, arg1, arg2):
        # Cálculo costoso
        return result
```

**¿Cómo funciona?**

1. **Primera llamada**: Ejecuta el método y guarda el resultado en `self._v_memoize_cache[key]`
2. **Llamadas posteriores**: Si los argumentos son idénticos, devuelve el resultado cacheado
3. **Caducidad**: La caché se limpia automáticamente al final del request (atributo volátil `_v_`)

### 🔑 Características Clave

| Característica | Valor |
|----------------|-------|
| **Scope** | Por instancia de objeto |
| **Persistencia** | Solo durante 1 request |
| **Thread-safe** | Sí (dentro del mismo request) |
| **Memoria** | Atributo volátil `_v_` (no persiste en ZODB) |
| **Invalidación** | Automática al final del request |
| **Compartido** | No (cada instancia tiene su propia caché) |

### ⚙️ Mecanismo de Cacheado

El decorador genera una **clave de caché** basada en:
- Nombre del método
- Argumentos posicionales (`args`)
- Argumentos con nombre (`kwargs`)

```python
# Ejemplo de claves generadas
method(1, 2)        → cache_key: ('method', (1, 2), {})
method(1, 2)        → HIT (misma clave)
method(1, 3)        → MISS (diferente clave)
method(x=1, y=2)    → cache_key: ('method', (), {'x': 1, 'y': 2})
```

### 📊 Análisis de Performance

**Caso real - Portlet `getOwnOrgans()`:**

| Métrica | Sin caché | Con `@instance.memoize` | Mejora |
|---------|-----------|-------------------------|--------|
| Llamadas | 5 | 1 | 80% ⬇️ |
| Tiempo total | 1.030s | 0.296s | 71% ⬇️ |
| Queries al catálogo | 5 | 1 | 80% ⬇️ |

### ✅ Ventajas

- ✓ Fácil de implementar (un decorador)
- ✓ No requiere configuración
- ✓ Limpieza automática
- ✓ Seguro (no persiste entre requests)
- ✓ Ideal para BrowserViews y Portlets

### ❌ Limitaciones

- ✗ Solo funciona dentro de un request
- ✗ No se comparte entre instancias
- ✗ No funciona con objetos no-hashables como argumentos
- ✗ No hay control de invalidación manual

### 🎯 Casos de Uso Ideales

1. **Portlets** que se renderizan varias veces en la misma página
2. **BrowserViews** con métodos llamados múltiples veces desde templates
3. **Adaptadores** que realizan cálculos costosos reutilizables en el request
4. **Funciones helper** en clases que procesan datos del catálogo

### 📝 Ejemplo Completo

```python
from plone import api
from plone.memoize import instance
from Products.Five.browser import BrowserView

class MyView(BrowserView):

    @instance.memoize
    def get_user_organs(self):
        """Obtiene órganos vinculados al usuario actual.

        OPTIMIZATION: Cache request-level para evitar búsquedas repetidas
        al catálogo cuando el template llama este método múltiples veces.
        """
        if api.user.is_anonymous():
            return []

        catalog = api.portal.get_tool('portal_catalog')
        results = catalog.searchResults(
            portal_type='genweb.organs.organgovern',
            sort_on='sortable_title'
        )

        username = api.user.get_current().id
        user_organs = []

        for brain in results:
            organ = brain._unrestrictedGetObject()
            roles = api.user.get_roles(username=username, obj=organ)

            if any(r in roles for r in ['OG1-Secretari', 'OG2-Editor']):
                user_organs.append({
                    'title': brain.Title,
                    'url': brain.getURL(),
                    'roles': roles
                })

        return user_organs

    @instance.memoize
    def get_organ_count(self):
        """Cuenta órganos del usuario (reutiliza el método cacheado)."""
        return len(self.get_user_organs())
```

**Template ZPT:**

```html
<tal:block tal:define="organs view/get_user_organs">
    <!-- Primera llamada a get_user_organs: ejecuta query -->
    <p>Tienes <span tal:content="python:len(organs)">0</span> órganos</p>

    <!-- Usa la variable 'organs' (no llama de nuevo a la función) -->
    <ul>
        <li tal:repeat="organ organs">
            <a tal:attributes="href organ/url" tal:content="organ/title">Título</a>
        </li>
    </ul>

    <!-- get_organ_count() internamente llama a get_user_organs() -->
    <!-- Sin memoize: segunda query | Con memoize: usa caché -->
    <p>Total: <span tal:content="view/get_organ_count">0</span></p>
</tal:block>
```

**Resultado:**
- Sin caché: **2 queries** al catálogo (1 en `tal:define` + 1 dentro de `get_organ_count`)
- Con caché: **1 query** al catálogo (la segunda usa caché)
- **Mejora: 50%** (se elimina 1 de las 2 queries)

---

## 3. @view.memoize

### 📖 Definición

`@view.memoize` es un decorador **especializado para BrowserViews** que cachea resultados considerando el **contexto** y la **request** como parte de la clave de caché.

### 🔧 Funcionamiento Interno

```python
from plone.memoize import view

class MyView(BrowserView):
    @view.memoize
    def expensive_method(self, arg1):
        # Cálculo costoso que depende de self.context y self.request
        return result
```

**¿Cómo funciona?**

1. **Clave de caché incluye:**
   - Nombre del método
   - Argumentos del método
   - **ID del contexto** (`self.context`)
   - **Hash de la request** (o parámetros específicos)

2. **Primera llamada**: Ejecuta y cachea
3. **Llamadas posteriores**: Devuelve caché si contexto + request + args coinciden

### 🔑 Características Clave

| Característica | Valor |
|----------------|-------|
| **Scope** | Por vista + contexto + request |
| **Persistencia** | Solo durante 1 request |
| **Thread-safe** | Sí |
| **Context-aware** | ✓ Sí (incluye contexto en clave) |
| **Request-aware** | ✓ Sí (puede incluir parámetros de request) |
| **Memoria** | Atributo en la instancia de vista |
| **Invalidación** | Automática al final del request |

### 🆚 Diferencia con @instance.memoize

```python
# @instance.memoize
# Cache key: (method_name, args, kwargs)
@instance.memoize
def get_items(self):
    # Se cachea por instancia, sin considerar contexto
    pass

# @view.memoize
# Cache key: (method_name, args, kwargs, context_id, request_hash)
@view.memoize
def get_items(self):
    # Se cachea considerando el contexto actual
    pass
```

### 📊 Ejemplo Comparativo

```python
from Products.Five.browser import BrowserView
from plone.memoize import instance, view

class ArticleView(BrowserView):

    @instance.memoize
    def get_related_wrong(self):
        """PROBLEMA: No considera el contexto.

        Si esta vista se usa en /article1 y /article2 en el mismo request
        (ej: en un batch), devolverá los mismos resultados para ambos.
        """
        return self.context.getRelatedItems()

    @view.memoize
    def get_related_correct(self):
        """CORRECTO: Considera el contexto.

        Cada artículo tendrá su propia caché basada en su ID.
        """
        return self.context.getRelatedItems()
```

**Escenario:**
```html
<!-- Listado de artículos -->
<tal:block tal:repeat="article articles">
    <div tal:define="view python:article.restrictedTraverse('@@article_view')">
        <!-- Con @instance.memoize: Todos devolverían los relacionados del primero -->
        <!-- Con @view.memoize: Cada uno devuelve sus propios relacionados -->
        <ul tal:define="related view/get_related_correct">
            <li tal:repeat="item related" tal:content="item/Title">Related</li>
        </ul>
    </div>
</tal:block>
```

### 🎯 Casos de Uso Ideales

1. **Métodos que acceden a `self.context`** (el contenido actual)
2. **Cálculos que dependen del objeto siendo renderizado**
3. **Vistas usadas en diferentes contextos** (listings, folders)
4. **Métodos que dependen de parámetros de la request**

### ⚠️ Cuándo NO usar @view.memoize

```python
# ❌ NO: Para métodos globales que no dependen del contexto
@view.memoize
def get_portal_title(self):
    return api.portal.get().Title()  # Igual para todo el sitio

# ✓ SÍ: Usar @instance.memoize en su lugar
@instance.memoize
def get_portal_title(self):
    return api.portal.get().Title()
```

### 📝 Ejemplo Completo

```python
from plone import api
from plone.memoize import view
from Products.Five.browser import BrowserView

class SessionView(BrowserView):
    """Vista para mostrar una sesión de órgano."""

    @view.memoize
    def get_points(self):
        """Obtiene los puntos de la sesión actual.

        OPTIMIZATION: Cache considerando el contexto (la sesión específica).
        Si esta vista se usa en múltiples sesiones, cada una tendrá su caché.
        """
        catalog = api.portal.get_tool('portal_catalog')

        # self.context = la sesión actual
        session_path = '/'.join(self.context.getPhysicalPath())

        results = catalog.searchResults(
            portal_type='genweb.organs.punt',
            path={'query': session_path, 'depth': 1},
            sort_on='getObjPositionInParent'
        )

        points = []
        for brain in results:
            obj = brain._unrestrictedGetObject()
            points.append({
                'title': brain.Title,
                'url': brain.getURL(),
                'state': brain.review_state,
                'agreement': getattr(obj, 'agreement', ''),
            })

        return points

    @view.memoize
    def get_point_count(self):
        """Cuenta puntos (reutiliza caché)."""
        return len(self.get_points())

    @view.memoize
    def has_agreements(self):
        """Verifica si hay acuerdos (reutiliza caché)."""
        return any(p['agreement'] for p in self.get_points())
```

### 🔬 Análisis Técnico de la Caché

```python
# Pseudocódigo interno de @view.memoize
def view_memoize(func):
    def wrapper(self, *args, **kwargs):
        # Genera clave considerando contexto
        cache_key = (
            func.__name__,
            args,
            frozenset(kwargs.items()),
            id(self.context),  # ← Diferencia clave
            _hash_request(self.request)  # ← Para query strings
        )

        if cache_key in self._v_cache:
            return self._v_cache[cache_key]

        result = func(self, *args, **kwargs)
        self._v_cache[cache_key] = result
        return result

    return wrapper
```

---

## 4. Comparativa

### 📊 Tabla Comparativa Completa

| Aspecto | @instance.memoize | @view.memoize | @ram.cache |
|---------|-------------------|---------------|------------|
| **Importación** | `plone.memoize.instance` | `plone.memoize.view` | `plone.memoize.ram` |
| **Alcance** | Instancia de clase | Vista + contexto | Proceso Zope |
| **Duración** | 1 request | 1 request | Hasta invalidación |
| **Context-aware** | ❌ No | ✅ Sí | Configurable |
| **Request-aware** | ❌ No | ✅ Sí | Configurable |
| **Compartido entre instancias** | ❌ No | ❌ No | ✅ Sí (mismo Zope) |
| **Compartido entre Zopes** | ❌ No | ❌ No | ❌ No |
| **Overhead** | Muy bajo | Bajo | Medio |
| **Configuración requerida** | No | No | Sí (cache key) |
| **Invalidación manual** | ❌ No | ❌ No | ✅ Sí |
| **Uso de memoria** | Bajo | Bajo | Alto |
| **Riesgo de stale data** | ❌ Ninguno | ❌ Ninguno | ⚠️ Alto |

### 🎯 Árbol de Decisión

```
¿Tu método depende del contexto (self.context)?
├─ SÍ → ¿Es una BrowserView?
│        ├─ SÍ → @view.memoize ✓
│        └─ NO → @instance.memoize + pasar contexto como argumento
│
└─ NO → ¿Necesitas caché más allá del request?
         ├─ SÍ → @ram.cache (con precaución en multi-Zope)
         └─ NO → @instance.memoize ✓
```

### 📝 Ejemplos de Selección

```python
from plone.memoize import instance, view, ram
from Products.Five.browser import BrowserView

class ExampleView(BrowserView):

    # ✓ CORRECTO: Método global, independiente del contexto
    @instance.memoize
    def get_site_logo(self):
        """Logo del sitio (igual en todo el sitio)."""
        return api.portal.get().logo

    # ✓ CORRECTO: Depende del contexto actual
    @view.memoize
    def get_breadcrumbs(self):
        """Breadcrumbs específicos del objeto actual."""
        return self.context.aq_chain

    # ✓ CORRECTO: Combina ambos enfoques
    @instance.memoize
    def get_portal_title(self):
        """Título del portal (global)."""
        return api.portal.get().Title()

    @view.memoize
    def get_full_title(self):
        """Título completo: portal + contexto."""
        portal_title = self.get_portal_title()  # Usa caché global
        return f"{portal_title} - {self.context.Title()}"
```

---

## 5. Casos de Uso

### 🎨 Caso 1: Portlet con Lista de Órganos

**Problema:** El portlet se renderiza 3 veces por página (viewlet manager lo llama varias veces).

```python
# ❌ SIN CACHÉ - 3 queries al catálogo por request
class OrgansPortlet(base.Renderer):
    def getOwnOrgans(self):
        catalog = api.portal.get_tool('portal_catalog')
        return catalog.searchResults(
            portal_type='genweb.organs.organgovern',
            sort_on='sortable_title'
        )
```

```python
# ✓ CON CACHÉ - 1 query al catálogo por request
from plone.memoize import instance

class OrgansPortlet(base.Renderer):
    @instance.memoize
    def getOwnOrgans(self):
        catalog = api.portal.get_tool('portal_catalog')
        return catalog.searchResults(
            portal_type='genweb.organs.organgovern',
            sort_on='sortable_title'
        )
```

**Resultado:**
- Queries: 3 → 1 (67% reducción)
- Tiempo: 1.5s → 0.5s (67% mejora)

### 🎨 Caso 2: Vista de Sesión con Múltiples Cálculos

**Problema:** Template llama al mismo método 10+ veces para verificaciones.

```python
# ❌ SIN CACHÉ - getUserRoles() llamado 10 veces
class SessionView(BrowserView):
    def can_modify(self):
        roles = getUserRoles(self.context, self.request)
        return 'OG1-Secretari' in roles

# Template ZPT llama can_modify() múltiples veces
```

```python
# ✓ CON CACHÉ - getUserRoles() llamado 1 vez
from plone.memoize import instance

class SessionView(BrowserView):
    @instance.memoize
    def get_user_roles(self):
        return getUserRoles(self.context, self.request)

    def can_modify(self):
        roles = self.get_user_roles()  # Usa caché
        return 'OG1-Secretari' in roles
```

**Resultado:**
- Llamadas: 10 → 1 (90% reducción)
- Tiempo: 0.5s → 0.05s (90% mejora)

### 🎨 Caso 3: Listado de Artículos con Metadatos

**Problema:** Cada artículo necesita calcular metadatos complejos.

```python
# ❌ SIN CACHÉ - Cálculo repetido para cada artículo
class ArticleView(BrowserView):
    def get_metadata(self):
        # Cálculo costoso: categorías, tags, autor, etc.
        categories = self.context.Subject()
        author = self.context.Creator()
        related_count = len(self.context.getRelatedItems())

        return {
            'categories': categories,
            'author': author,
            'related': related_count
        }

# Si se usa en un listing, cada artículo recalcula
```

```python
# ✓ CON CACHÉ - Cada artículo cachea sus metadatos
from plone.memoize import view

class ArticleView(BrowserView):
    @view.memoize  # ← Usa view.memoize porque depende del contexto
    def get_metadata(self):
        categories = self.context.Subject()
        author = self.context.Creator()
        related_count = len(self.context.getRelatedItems())

        return {
            'categories': categories,
            'author': author,
            'related': related_count
        }
```

**Resultado:**
- Con 20 artículos en un listing
- Sin caché: 20 cálculos
- Con caché: 20 cálculos (pero cada uno se cachea para llamadas posteriores del template)
- **Beneficio real:** Si el template llama `get_metadata()` 3 veces por artículo:
  - Sin caché: 60 cálculos
  - Con caché: 20 cálculos (67% reducción)

### 🎨 Caso 4: Pre-cálculo en Python vs Cálculo en Template

**Problema:** Template hace cálculos repetitivos con `python:`.

```html
<!-- ❌ MALO: canModify() llamado 50 veces desde template -->
<tal:block tal:repeat="item items">
    <td tal:condition="python: view.canModify(item)">
        <a href="#">Editar</a>
    </td>
    <td tal:condition="python: view.canModify(item)">
        <a href="#">Eliminar</a>
    </td>
    <td tal:condition="python: view.canModify(item)">
        <span>Modificable</span>
    </td>
</tal:block>
```

```python
# ✓ SOLUCIÓN: Pre-calcular en Python
class SessionView(BrowserView):
    def get_points(self):
        points = []
        for item in self._get_raw_points():
            # Pre-calcular canModify UNA VEZ
            can_modify = self.canModify(item)

            points.append({
                'title': item.Title(),
                'url': item.absolute_url(),
                'can_modify': can_modify,  # ← Pre-calculado
            })
        return points
```

```html
<!-- ✓ BUENO: Usar valor pre-calculado -->
<tal:block tal:repeat="item view/get_points">
    <td tal:condition="item/can_modify">
        <a href="#">Editar</a>
    </td>
    <td tal:condition="item/can_modify">
        <a href="#">Eliminar</a>
    </td>
    <td tal:condition="item/can_modify">
        <span>Modificable</span>
    </td>
</tal:block>
```

**Resultado:**
- Con 50 items
- Sin pre-cálculo: 150 llamadas a `canModify()` (3 por item)
- Con pre-cálculo: 50 llamadas (1 por item)
- **Mejora: 67% reducción**

---

## 6. Ejemplos Prácticos

### 📝 Ejemplo Real: Optimización de Sessio.pt

**Antes:**

```python
# sessio.py
class SessionView(BrowserView):
    def PuntsInside(self):
        results = []
        for item in self._get_items():
            results.append({
                'title': item.Title(),
                'url': item.absolute_url(),
                # NO pre-calculado
            })
        return results

    def canModifyPunt(self, item_dict):
        """Verifica permisos - llamado múltiples veces."""
        roles = getUserRoles(self.context, self.request)
        return 'OG1-Secretari' in roles
```

```html
<!-- sessio.pt -->
<tal:block tal:repeat="item view/PuntsInside">
    <!-- canModifyPunt() llamado 3 veces por item -->
    <td tal:condition="python: view.canModifyPunt(item)">Editar</td>
    <td tal:condition="python: view.canModifyPunt(item)">Eliminar</td>
    <td tal:condition="python: view.canModifyPunt(item)">Mover</td>
</tal:block>
```

**Después:**

```python
# sessio.py - OPTIMIZADO
from plone.memoize import instance

class SessionView(BrowserView):
    def PuntsInside(self):
        results = []
        for item in self._get_items():
            item_dict = {
                'title': item.Title(),
                'url': item.absolute_url(),
            }
            # PRE-CALCULAR canModify
            item_dict['can_modify'] = self.canModifyPunt(item_dict)
            results.append(item_dict)
        return results

    @instance.memoize
    def get_user_roles(self):
        """Cache de roles del usuario."""
        return getUserRoles(self.context, self.request)

    def canModifyPunt(self, item_dict):
        """Verifica permisos - usa roles cacheados."""
        roles = self.get_user_roles()  # ← Usa caché
        return 'OG1-Secretari' in roles
```

```html
<!-- sessio.pt - OPTIMIZADO -->
<tal:block tal:repeat="item view/PuntsInside">
    <!-- Usa valor pre-calculado (sin llamadas a Python) -->
    <td tal:condition="item/can_modify">Editar</td>
    <td tal:condition="item/can_modify">Eliminar</td>
    <td tal:condition="item/can_modify">Mover</td>
</tal:block>
```

**Resultados Medidos:**

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Tiempo de renderizado | 5.435s | 0.538s | **90% ⬇️** |
| Llamadas a `canModifyPunt()` | 34 | 8 | **76% ⬇️** |
| Queries al catálogo | 3 | 1 | **67% ⬇️** |

---

## 7. Casos Donde NO Funciona: Lecciones Aprendidas

### 🚫 Caso Crítico: Objetos de Autenticación (LDAP)

Durante la optimización de `genweb6.organs`, se intentó aplicar `@instance.memoize` a funciones LDAP. **Todos los intentos fallaron** por razones de seguridad.

#### ⚠️ Intento 1: Cachear `getUserByAttr` con @instance.memoize

```python
# ❌ INTENTO FALLIDO en genweb6.core/patches.py
from plone.memoize import instance

@instance.memoize
def getUserByAttr(self, name, value, pwd=None, cache=0):
    """Get a user based on a name/value pair representing an
       LDAP attribute provided to the user.
    """
    # ... código LDAP ...
    return user_obj  # Objeto LDAPUser
```

**Resultado:** ❌ Error de seguridad en el navegador

```
⚠️ Alerta de Seguridad
Podría ser que algú us haguéis introduït un programa maliciós
mitjançant un exploit. Confirmeu que heu executat l'acció
directament en aquest portal.
```

**Diagnóstico:**
- Plone detectó bypass de verificaciones de seguridad
- El objeto `LDAPUser` contiene contexto de autenticación
- Acquisition chain roto por el caché
- CSRF tokens invalidados

---

#### ⚠️ Intento 2: Caché Manual con Request Annotations

```python
# ❌ INTENTO FALLIDO - Caché manual en REQUEST
def getUserByAttr(self, name, value, pwd=None, cache=0):
    """Request-level cache usando annotations."""

    # Intentar cachear en request
    request = getattr(self, 'REQUEST', None)
    if request is not None:
        pwd_hash = sha1((pwd or "").encode()).hexdigest()
        cache_key = f'_ldap_getUserByAttr_{name}_{value}_{pwd_hash}'
        annotations = getattr(request, '__annotations__', None)

        if annotations is not None:
            if cache_key in annotations:
                return annotations[cache_key]  # Devolver objeto cacheado

    # ... código LDAP ...
    user_obj = LDAPUser(...)

    # Guardar en request annotations
    if request is not None and annotations is not None:
        annotations[cache_key] = user_obj  # ❌ PROBLEMA

    return user_obj
```

**Resultado:** ❌ Mismo error de seguridad

**Profiling mostró mejora (engañosa):**
```
getUserByAttr: 2414 llamadas → 0.736s (vs 3.275s antes)
Solo 11 consultas LDAP reales (vs 6021 antes)
Mejora aparente: 78%
```

**PERO:** El sitio era inutilizable por errores de seguridad.

---

#### ⚠️ Intento 3: Cachear `getGroups` con @instance.memoize

```python
# ❌ INTENTO FALLIDO
from plone.memoize import instance

@instance.memoize
def getGroups(self, dn='*', attr=None, pwd=''):
    """Returns a list of possible groups from the ldap tree."""
    # ... código LDAP ...
    return group_list  # Lista de grupos LDAP del usuario
```

**Resultado:** ❌ Mismo error de seguridad

Aunque `getGroups` devuelve una lista (no un objeto complejo), también falló porque contiene **información sensible de pertenencia a grupos**.

---

### 🔍 ¿Por Qué Fallan Estos Cachés?

#### 1. **Violation del Security Manager de Zope**

```python
# El objeto LDAPUser contiene:
class LDAPUser:
    def __init__(self, uid, login_name, pwd, roles, ...):
        self._pwd = pwd              # ← Hash de contraseña
        self._roles = roles          # ← Roles asignados
        self._dn = user_dn           # ← Distinguished Name LDAP
        self._user_attrs = attrs     # ← Atributos sensibles
```

Cuando lo cacheas:
- ✗ El contexto de seguridad se rompe
- ✗ Acquisition chain se pierde
- ✗ CSRF tokens no coinciden
- ✗ Security Manager no puede verificar permisos

#### 2. **Incompatibilidad con Monkey Patching**

```xml
<!-- patches.zcml -->
<monkey:patch
    class="Products.LDAPUserFolder.LDAPUserFolder.LDAPUserFolder"
    original="getUserByAttr"
    replacement=".patches.getUserByAttr"
    />
```

**Problema:** `collective.monkeypatcher` espera una función "pura", pero `@instance.memoize` la envuelve:

```python
# Lo que ve collective.monkeypatcher:
<function memoize.<locals>.memogetter at 0x...>  # ← Wrapper
# En lugar de:
<function getUserByAttr at 0x...>  # ← Función original
```

**Resultado:**
- La firma del método se rompe
- Los decoradores de seguridad no se aplican correctamente
- Zope no reconoce el método como válido

#### 3. **Datos Sensibles Compartidos Incorrectamente**

```python
# Escenario peligroso:
# Usuario A hace login
user_a = getUserByAttr('uid', 'usuaria', pwd='password123')
# → Se cachea en request.__annotations__

# En el mismo request (hipotéticamente), código malicioso:
cached = request.__annotations__['_ldap_getUserByAttr_uid_usuaria_...']
# → Acceso a objeto con credenciales y roles de usuaria ❌
```

Aunque Plone previene esto, **el intento de hacerlo ya viola las políticas de seguridad**.

---

### ✅ Solución Real: Cache Nativo de LDAP

En lugar de intentar cachear a nivel de Python, **configurar el caché interno** de `LDAPUserFolder`:

```python
# setuphandlers.py
def configure_ldap_cache(portal, logger):
    """Configurar timeouts de caché LDAP."""
    acl_users = portal.acl_users

    for plugin_id in acl_users.objectIds():
        plugin = getattr(acl_users, plugin_id)

        if hasattr(plugin, '_authenticated_timeout'):
            # Aumentar de 600s (10 min) a 3600s (1 hora)
            plugin._authenticated_timeout = 3600
            plugin._anonymous_timeout = 3600
            logger.info(f'LDAP cache configured: {plugin_id} → 3600s')
```

**Por qué funciona:**
- ✅ El caché está en `LDAPUserFolder` (diseñado para esto)
- ✅ Respeta el contexto de seguridad
- ✅ Gestiona correctamente usuarios autenticados/anónimos
- ✅ Cache negativo para usuarios inexistentes
- ✅ No interfiere con monkey patches

**Resultados:**
```
Primera visita: 61 consultas LDAP → 4.102s
Visitas posteriores (en 1h): 5 consultas LDAP → 0.5s
Mejora real: 87% sin comprometer seguridad
```

---

### 📋 Tipos de Objetos que NO Debes Cachear

| Tipo de Objeto | Por qué NO cachear | Alternativa |
|----------------|-------------------|-------------|
| **LDAPUser** | Contiene credenciales y contexto de seguridad | Cache interno LDAP |
| **Usuarios PAS** | Security Manager requiere verificación por request | Cache interno PAS |
| **Grupos LDAP** | Información sensible de pertenencia | Cache interno LDAP |
| **Objetos con Acquisition** | Rompe el chain, causa errores de contexto | Cachear datos, no objetos |
| **Request/Response** | Estado mutable, específico del request | No cachear |
| **Transaction objects** | Estado de transacción ZODB | No cachear |
| **Portal tools** | Ya están cacheados por Zope | No necesario |

---

### 🎯 Reglas de Oro para Caché con Objetos de Seguridad

#### ✅ Puedes Cachear:

```python
# ✓ Resultados de queries (brains)
@instance.memoize
def get_documents(self):
    return catalog.searchResults(portal_type='Document')

# ✓ Datos extraídos de objetos
@instance.memoize
def get_user_info(self, username):
    user = api.user.get(username=username)
    return {
        'id': user.getId(),
        'email': user.getProperty('email'),
        'fullname': user.getProperty('fullname')
    }

# ✓ Roles (listas simples)
@instance.memoize
def get_user_roles(self, username, context_path):
    context = api.content.get(path=context_path)
    return api.user.get_roles(username=username, obj=context)
```

#### ❌ NO Cachees:

```python
# ✗ Objetos de usuario completos
@instance.memoize
def get_user_object(self, username):
    return api.user.get(username=username)  # ← Objeto complejo

# ✗ Objetos LDAP
@instance.memoize
def get_ldap_user(self, uid):
    return ldap_plugin.getUserByAttr('uid', uid)  # ← LDAPUser

# ✗ Contextos con Acquisition
@instance.memoize
def get_parent(self):
    return self.context.aq_parent  # ← Rompe acquisition chain
```

---

### 📊 Comparativa de Intentos de Optimización LDAP

| Intento | Técnica | Mejora Aparente | Resultado Real | Viable |
|---------|---------|----------------|----------------|--------|
| 1 | `@instance.memoize` en `getUserByAttr` | 78% ⬆️ | Error seguridad ❌ | ❌ No |
| 2 | Cache manual en REQUEST | 78% ⬆️ | Error seguridad ❌ | ❌ No |
| 3 | `@instance.memoize` en `getGroups` | 65% ⬆️ | Error seguridad ❌ | ❌ No |
| 4 | **Aumentar cache interno LDAP** | 87% ⬆️ | Sin errores ✅ | ✅ **SÍ** |

---

### 💡 Lecciones Aprendidas

1. **No todo lo medible es optimizable**
   - El profiling mostraba mejoras del 78%
   - Pero el sitio era inutilizable
   - **La seguridad siempre es prioridad #1**

2. **Respetar las arquitecturas existentes**
   - LDAP ya tiene su propio sistema de caché
   - Intentar añadir otra capa rompe el diseño
   - **Usar las herramientas diseñadas para el propósito**

3. **Los objetos de seguridad son especiales**
   - No son simples datos
   - Tienen contexto, acquisition, permisos
   - **Cachear datos extraídos, no objetos completos**

4. **Monkey patching tiene limitaciones**
   - No todo decorador es compatible
   - `@instance.memoize` modifica la firma del método
   - **Mantener monkey patches simples**

5. **Profiling puede ser engañoso**
   - Mejora de performance ≠ Solución válida
   - Siempre probar funcionalidad después de optimizar
   - **Medir performance + seguridad + funcionalidad**

---

### 🔧 Alternativas Recomendadas

Si necesitas optimizar código con objetos de seguridad:

#### Opción A: Extraer Datos
```python
# En lugar de cachear el objeto usuario
@instance.memoize
def get_user_data(self, username):
    """Cachea datos, no el objeto."""
    user = api.user.get(username=username)
    if user:
        return {
            'id': user.getId(),
            'email': user.getProperty('email'),
            'roles': api.user.get_roles(username=username)
        }
    return None
```

#### Opción B: Configurar Cache Nativo
```python
# Aumentar timeouts del sistema de caché diseñado para esto
ldap_plugin._authenticated_timeout = 3600  # 1 hora
ldap_plugin._anonymous_timeout = 3600      # 1 hora
```

#### Opción C: Pre-calcular en Python
```python
# Pre-calcular verificaciones costosas
def get_items_with_permissions(self):
    items = []
    for brain in catalog.searchResults(...):
        obj = brain.getObject()

        # Pre-calcular una sola vez
        can_edit = api.user.has_permission('Modify portal content', obj=obj)

        items.append({
            'title': brain.Title,
            'can_edit': can_edit  # ← Pre-calculado
        })
    return items
```

---

## 8. Problemas Comunes

### ⚠️ Problema 1: Argumentos No-Hashables

```python
# ❌ ERROR: list no es hashable
@instance.memoize
def process_items(self, items_list):
    # TypeError: unhashable type: 'list'
    return sum(items_list)

# ✓ SOLUCIÓN 1: Convertir a tuple
@instance.memoize
def process_items(self, items_tuple):
    return sum(items_tuple)

# Llamar con: view.process_items(tuple(my_list))

# ✓ SOLUCIÓN 2: Serializar a JSON
import json

@instance.memoize
def process_items(self, items_json):
    items = json.loads(items_json)
    return sum(items)

# Llamar con: view.process_items(json.dumps(my_list))
```

### ⚠️ Problema 2: Contexto Dinámico con @instance.memoize

```python
# ❌ PROBLEMA: No considera el contexto
@instance.memoize
def get_parent_title(self):
    # Si se llama desde diferentes contextos, devuelve el del primero
    return self.context.aq_parent.Title()

# ✓ SOLUCIÓN 1: Usar @view.memoize
from plone.memoize import view

@view.memoize
def get_parent_title(self):
    return self.context.aq_parent.Title()

# ✓ SOLUCIÓN 2: Pasar contexto como argumento
@instance.memoize
def get_parent_title(self, context_path):
    # Ahora el context_path forma parte de la clave de caché
    parent = self.context.aq_parent
    return parent.Title()

# Llamar con: self.get_parent_title('/'.join(self.context.getPhysicalPath()))
```

### ⚠️ Problema 3: Mutación de Objetos Cacheados

```python
# ❌ PELIGRO: Mutación del objeto cacheado
@instance.memoize
def get_config(self):
    return {'debug': False, 'timeout': 30}

# En otro método
config = self.get_config()
config['debug'] = True  # ← MODIFICA LA CACHÉ!

# Próxima llamada devolverá {'debug': True, ...} 😱

# ✓ SOLUCIÓN: Retornar copia
@instance.memoize
def get_config(self):
    return {'debug': False, 'timeout': 30}

# En otro método
config = self.get_config().copy()  # ← Copia
config['debug'] = True  # Ahora es seguro
```

### ⚠️ Problema 4: Caché con @ram.cache en Multi-Zope

```python
# ⚠️ PROBLEMA: @ram.cache no se comparte entre Zopes
from plone.memoize import ram
import time

def cache_key(func, self):
    return time.time() // 60  # Cache por 1 minuto

@ram.cache(cache_key)
def get_total_users(self):
    # Esta caché es POR ZOPE, no compartida
    # Zope1 puede tener un valor, Zope2 otro diferente
    return len(api.user.get_users())

# ✓ SOLUCIÓN: Usar Redis/Memcached para caché distribuida
# (requiere configuración adicional y paquetes como `plone.memoize.memcached`)
```

### ⚠️ Problema 5: Debugging con Caché

```python
# ❌ PROBLEMA: Cambios no se reflejan porque está cacheado
@instance.memoize
def get_data(self):
    # Estás debuggeando y cambias esto
    return "nuevo valor"
    # Pero sigue devolviendo "valor viejo" en el mismo request

# ✓ SOLUCIÓN 1: Reiniciar instancia Zope
# ./bin/instance restart

# ✓ SOLUCIÓN 2: Decorador condicional para desarrollo
import os

ENABLE_CACHE = os.environ.get('ENABLE_CACHE', 'true') == 'true'

def conditional_memoize(func):
    if ENABLE_CACHE:
        return instance.memoize(func)
    return func

@conditional_memoize
def get_data(self):
    return "nuevo valor"

# En desarrollo: export ENABLE_CACHE=false
```

---

## 9. Referencias

### 📚 Documentación Oficial

- **plone.memoize**: https://github.com/plone/plone.memoize
- **Plone 6 Performance Guide**: https://6.docs.plone.org/
- **Plone Training - Performance**: https://training.plone.org/

### 🔗 Paquetes Relacionados

```python
# Instalación
[buildout]
eggs =
    plone.memoize           # Core memoization decorators
    plone.app.caching       # HTTP caching configuration
    plone.cachepurging      # Varnish integration
```

### 📖 API Reference

```python
# plone.memoize.instance
from plone.memoize import instance

@instance.memoize
def method(self, arg1, arg2):
    """Cache key: (method_name, arg1, arg2)"""
    pass

# plone.memoize.view
from plone.memoize import view

@view.memoize
def method(self, arg1):
    """Cache key: (method_name, arg1, context_id, request_hash)"""
    pass

# plone.memoize.ram
from plone.memoize import ram

def cache_key_func(method, self, arg1):
    """Define cómo generar la clave de caché."""
    return (arg1, time.time() // 300)  # Cache por 5 minutos

@ram.cache(cache_key_func)
def method(self, arg1):
    """Cache persistente en RAM del proceso Zope."""
    pass
```

### 🛠️ Herramientas de Análisis

1. **repoze.profile** - Profiling de requests
   ```ini
   [instance]
   eggs += repoze.profile
   ```

2. **collective.profiler** - Profiling visual
   ```ini
   [instance]
   eggs += collective.profiler
   ```

3. **plone.app.debugtoolbar** - Debugging en desarrollo
   ```ini
   [instance]
   eggs += plone.app.debugtoolbar
   ```

### 📊 Benchmarking

```python
# Medir impacto de la caché
import time
import logging

logger = logging.getLogger(__name__)

def benchmark(func):
    """Decorador para medir tiempo de ejecución."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

class MyView(BrowserView):
    @benchmark
    @instance.memoize
    def expensive_method(self):
        # Primera llamada: log muestra tiempo real
        # Siguientes llamadas: log muestra ~0.000s
        time.sleep(1)  # Simula operación costosa
        return "result"
```

---

## 📈 Resumen de Mejores Prácticas

### ✅ DO (Hacer)

1. ✓ Usar `@instance.memoize` para métodos independientes del contexto
2. ✓ Usar `@view.memoize` para métodos que dependen de `self.context`
3. ✓ Pre-calcular valores en Python antes de pasar al template
4. ✓ Documentar por qué se usa caché en cada método
5. ✓ Medir el impacto real con profiling antes y después
6. ✓ Combinar caché con optimización de queries al catálogo
7. ✓ Retornar copias de objetos mutables
8. ✓ Usar argumentos hashables (str, int, tuple)
9. ✓ **Leer la sección 7 antes de cachear objetos de seguridad**

### ❌ DON'T (No hacer)

1. ✗ Usar `@ram.cache` en entornos multi-Zope sin Redis/Memcached
2. ✗ Mutar objetos devueltos por métodos cacheados
3. ✗ Usar argumentos no-hashables (list, dict, set)
4. ✗ Cachear métodos con side-effects (escritura DB, envío emails)
5. ✗ Abusar de la caché en métodos rápidos (<0.01s)
6. ✗ Olvidar documentar la estrategia de caché
7. ✗ Usar `@view.memoize` cuando no depende del contexto
8. ✗ Confiar en caché para lógica de negocio crítica
9. ✗ **Cachear objetos LDAPUser, usuarios PAS, o grupos de seguridad**
10. ✗ **Aplicar `@instance.memoize` a monkey patches de funciones LDAP**

---

## 🎓 Conclusión

Los decoradores de memoización son herramientas **poderosas** para optimizar el rendimiento en Plone 6:

- **`@instance.memoize`**: La opción más común y segura para la mayoría de casos
- **`@view.memoize`**: Para BrowserViews context-aware
- **`@ram.cache`**: Solo con Redis/Memcached en multi-Zope

**⚠️ IMPORTANTE: No todo se puede cachear**
- Objetos de autenticación (LDAP, PAS) → **NO cachear**
- Grupos de seguridad → **NO cachear**
- Objetos con Acquisition → **NO cachear**
- Ver **Sección 7** para casos donde NO funciona

**Recuerda:**
- 🎯 Mide primero, optimiza después (profiling con `repoze.profile`)
- 🧪 Verifica que los tests siguen pasando **y que no hay errores de seguridad**
- 📝 Documenta la estrategia de caché
- 🔍 Monitorea el impacto en producción
- ⚠️ **La seguridad siempre es prioridad #1** sobre la performance

**Mejoras reales en genweb6.organs:**
- Vista Sessio: **90% más rápida** (5.4s → 0.5s)
- Portlet LaVinculacio: **71% más rápido** (1.0s → 0.3s)
- Queries al catálogo: **67-80% reducción**

**Intentos fallidos documentados:**
- Cache LDAP con `@instance.memoize`: ❌ Error de seguridad
- Cache LDAP manual con REQUEST: ❌ Error de seguridad
- **Solución real:** Configurar cache interno LDAP → ✅ 87% mejora sin errores

---

**Documento generado el:** 2025-11-24
**Versión:** 2.0
**Proyecto:** genweb6.organs - Optimización de Rendimiento
**Autor:** Sistema de Optimización Plone 6

**Changelog:**
- **v2.0 (2025-11-24):** Añadida sección 7 "Casos Donde NO Funciona" con lecciones aprendidas de intentos fallidos de optimización LDAP
- **v1.0 (2025-11-20):** Versión inicial con guía completa de memoización
