# 🚀 Migración CI/CD: CircleCI → GitHub Actions

## 📋 Resumen de cambios

Se ha migrado la configuración de CI/CD de CircleCI a GitHub Actions para aprovechar la integración nativa con GitHub y simplificar el proceso.

## ✅ Cambios realizados

### Archivos nuevos:
- ✅ `.github/workflows/test.yml` - Workflow principal de tests
- ✅ `.github/workflows/README.md` - Documentación del workflow
- ✅ `buildout-ci.cfg` - Configuración ligera de buildout para CI
- ✅ `requirements.txt` - Dependencias Python para CI
- ✅ `MIGRATION_CI.md` - Este documento

### Archivos modificados:
- ✅ `buildout.cfg` - Actualizado a Plone 6.0.15
- ✅ `README.md` - Badges actualizados (GitHub Actions, Python 3.11, Plone 6)

### Archivos eliminados:
- ❌ `.circleci/` - Configuración obsoleta de CircleCI

## 🎯 ¿Qué hace GitHub Actions?

Cuando hagas **push** o crees un **Pull Request** a `develop` o `master`:

1. ✅ Instala Python 3.11
2. ✅ Cachea buildout (builds más rápidos)
3. ✅ Instala dependencias del sistema
4. ✅ Ejecuta buildout con `buildout-ci.cfg` (configuración ligera)
5. ✅ Ejecuta tests de genweb6.organs
6. ✅ Genera reporte de coverage
7. ✅ Sube coverage como artifact descargable

### ¿Por qué buildout-ci.cfg?

Se usa una configuración simplificada para CI que solo incluye:
- `instance` - Instancia de Plone para tests
- `test` - Runner de tests
- `i18ndude` - Herramientas de internacionalización

Se excluyen partes que no son necesarias para tests:
- `releaser` - Solo para hacer releases (requiere cmarkgfm con cmake)
- `code-analysis` - Análisis de código (opcional)
- `createcoverage` - Ya usamos coverage directamente
- `omelette` - Solo para desarrollo local

## 📊 Ver resultados

### En GitHub Actions
https://github.com/UPCnet/genweb6.organs/actions

### En commits
https://github.com/UPCnet/genweb6.organs/commits/develop

Verás iconos junto a cada commit:
- ⏳ Amarillo = En progreso
- ✅ Verde = Éxito
- ❌ Rojo = Fallo

### Coverage report
En cualquier workflow completado → "Artifacts" → Descargar `coverage-report.zip`

## 🚀 Próximo paso: Hacer commit

```bash
cd /Users/pilarmarinas/Development/Plone/organs6.buildout/src/genweb6.organs

# Ver cambios
git status

# Añadir todo
git add .
git add .circleci  # Para confirmar la eliminación

# Commit
git commit -m "chore(ci): migrar de CircleCI a GitHub Actions

- Actualizar buildout.cfg a Plone 6.0.15
- Crear workflow de GitHub Actions con Python 3.11
- Eliminar configuración obsoleta de CircleCI
- Actualizar badges en README
- Añadir cache de buildout para builds más rápidos
- Configurar artifacts de coverage"

# Push
git push origin develop
```

## ⚡ Primera ejecución

Una vez hagas push:

1. Ve a: https://github.com/UPCnet/genweb6.organs/actions
2. Verás el workflow ejecutándose automáticamente
3. Tiempo estimado: **10-15 minutos** (primera vez sin cache)
4. Siguientes builds: **3-5 minutos** (con cache)

## 🔍 Troubleshooting

### Si el workflow falla
1. Click en el workflow fallido
2. Expande el step que falló
3. Lee los logs
4. Corrige localmente
5. Push de nuevo

### Probar localmente antes
```bash
cd /Users/pilarmarinas/Development/Plone/organs6.buildout/src/genweb6.organs

python3.11 -m venv test-venv
source test-venv/bin/activate
pip install -r requirements.txt
buildout -N
buildout -N
bin/test
```

## 📈 Ventajas de GitHub Actions

✅ **Gratis** para repos públicos
✅ **Sin configuración externa** (se activa solo)
✅ **Integración nativa** con GitHub
✅ **Cache inteligente** de buildout
✅ **Artifacts** disponibles 30 días
✅ **Logs en tiempo real**
✅ **Badges automáticos**

## 🎨 Badges en README

Se han añadido 3 badges:
- ![Tests](https://github.com/UPCnet/genweb6.organs/actions/workflows/test.yml/badge.svg?branch=develop) - Estado de tests
- ![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg) - Versión Python
- ![Plone 6.0.15](https://img.shields.io/badge/plone-6.0.15-blue.svg) - Versión Plone

## 📚 Documentación adicional

- Workflow: `.github/workflows/README.md`
- GitHub Actions docs: https://docs.github.com/en/actions
- Testing local: Ver sección Troubleshooting arriba

---

**Fecha de migración**: 21 Octubre 2025
**Versiones**: Python 3.11 | Plone 6.0.15
**Branch**: develop
