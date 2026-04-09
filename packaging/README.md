# Packaging scaffold

Este directorio contiene plantillas y scripts de trabajo para distribución.

## Estado

- `windows/`: scaffold inicial de build para generar `cmdradiopy.exe` + `cmdradiopy-win64.zip`.
- `scoop/`: manifiesto actualizado a `v1.2.6` con URL/hash reales de release.
- `chocolatey/`: nuspec + install script actualizados a `v1.2.6` con URL/hash reales de release.
- `debian/`: empaquetado .deb listo para build — `control`, `changelog` (v1.2.6-1), `rules`, `copyright`, `source/format`.

## Decisiones actuales

- Licencia: GPL-3.0
- Prioridad de distribución: Windows
- Artefacto objetivo Windows: zip con `cmdradiopy.exe`
- Las playlists iniciales deben viajar dentro del artefacto final

## Siguientes pasos

1. Confirmar instalación en Scoop/Chocolatey usando la URL pública de `v1.2.6`.
2. Validar ejecución limpia con playlists migradas en una máquina sin estado previo.
3. Actualizar Maintainer y email reales en `debian/control` y `debian/changelog` antes de publicar en repositorios oficiales.
4. Validar el workflow Linux haciendo push del siguiente tag.

## CI/CD

### Windows
- Workflow: `.github/workflows/release-windows.yml`
- Trigger: push de tags con formato `v*.*.*`
- Salidas: release assets `cmdradiopy-win64.zip` y `cmdradiopy-win64.sha256`

### Linux
- Workflow: `.github/workflows/release-linux-deb.yml`
- Trigger: push de tags con formato `v*.*.*`
- Runner: `ubuntu-latest`
- Herramienta: `dpkg-buildpackage -us -uc -b` + `lintian` (no bloqueante)
- Salidas: release assets `cmdradiopy_<version>_all.deb` y su `.sha256`

## Release actual (v1.2.6)

- Enlace: https://github.com/smelpillow/cmdRadioPy/releases/tag/v1.2.6

- `cmdradiopy-win64.zip`: `ff7785f39521902273120b4d5815dd1333f640bd46155cabe3e5b8611551f5e1`
- Hash del `.deb` publicado en `v1.2.6`: `9aed05d565d827dc625e83e4e65c2c65d4cc0025a48b53b7de45d87c39d85d89`
