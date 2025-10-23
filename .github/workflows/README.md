# GitHub Actions - CI/CD para genweb6.organs

## 📋 Descripción

Este workflow ejecuta automáticamente los tests de `genweb6.organs` en cada commit o pull request a las branches `develop` y `master`.

## 🚀 ¿Qué hace?

Cuando haces push o creas un PR:

1. **Checkout del código**
2. **Instala Python 3.11**
3. **Cachea buildout** (para builds más rápidos)
4. **Instala dependencias del sistema** (LDAP, SSL, XML, etc.)
5. **Instala dependencias Python** (desde requirements.txt)
6. **Ejecuta buildout** dos veces (como bootstrap local)
7. **Ejecuta tests** del paquete
8. **Genera coverage** y lo guarda como artifact
9. **Sube coverage** como artifact descargable

## 📊 Ver resultados

### En GitHub
1. Ve a: https://github.com/UPCnet/genweb6.organs/actions
2. Verás todos los workflows ejecutados
3. Click en cualquiera para ver detalles

### En commits
1. Ve a: https://github.com/UPCnet/genweb6.organs/commits/develop
2. Verás iconos junto a cada commit:
   - ⏳ **Amarillo** = En progreso
   - ✅ **Verde** = Éxito
   - ❌ **Rojo** = Fallo

### Coverage report
1. En el workflow completado, ve a "Artifacts"
2. Descarga `coverage-report.zip`
3. Descomprime y abre `index.html`

## ⚡ Ventajas sobre CircleCI

- ✅ **Gratis** para repos públicos
- ✅ **Sin configuración externa** (se activa automáticamente)
- ✅ **Integración nativa** con GitHub
- ✅ **Cache inteligente** de buildout
- ✅ **Visible en GitHub** sin salir de la plataforma
- ✅ **Artifacts** disponibles 30 días

## 🔧 Configuración

El workflow se ejecuta en:
- **Push** a `develop` o `master`
- **Pull Requests** a `develop` o `master`

Para modificar, edita: `.github/workflows/test.yml`

## 📦 Cache

El workflow cachea:
- `eggs/` - Paquetes Python de buildout
- `parts/` - Parts generados por buildout
- `.installed.cfg` - Estado de buildout

Esto reduce el tiempo de build de ~10-15 min a ~3-5 min en builds subsiguientes.

## 🧪 Probar localmente

Para replicar el mismo ambiente del CI:

```bash
cd /path/to/genweb6.organs

# Crear venv limpio
python3.11 -m venv test-venv
source test-venv/bin/activate

# Instalar y ejecutar (como GitHub Actions)
pip install -r requirements.txt
buildout -N
buildout -N
bin/test
```

## 🔍 Troubleshooting

### Build falla en buildout
- Verificar que `buildout.cfg` es válido
- Comprobar versiones en `requirements.txt`
- Limpiar cache: re-ejecutar workflow

### Tests fallan
- Ejecutar localmente: `bin/test -s genweb6.organs`
- Verificar que todos los tests pasan en local
- Revisar logs del workflow en GitHub

### Cache desactualizado
- El cache se invalida automáticamente si cambian:
  - `buildout.cfg`
  - `requirements.txt`
- Para forzar limpieza: editar el `key:` en test.yml

## 📝 Badges

Añade este badge al README.md para mostrar el estado:

```markdown
[![Tests](https://github.com/UPCnet/genweb6.organs/actions/workflows/test.yml/badge.svg?branch=develop)](https://github.com/UPCnet/genweb6.organs/actions/workflows/test.yml)
```

Se verá así: ![Tests](https://github.com/UPCnet/genweb6.organs/actions/workflows/test.yml/badge.svg?branch=develop)

## 🎯 Próximos pasos

- [ ] Añadir badge al README
- [ ] Configurar notificaciones por email
- [ ] Añadir workflow para deployment (opcional)
- [ ] Integrar con code quality tools (opcional)
