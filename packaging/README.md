# Packaging scaffold

Este directorio contiene plantillas y scripts de trabajo para distribución.

## Estado

- `windows/`: scaffold inicial de build para generar `cmdradiopy.exe` + `cmdradiopy-win64.zip`.
- `scoop/`: manifiesto actualizado a `v1.2.7` con URL/hash reales de release.
- `chocolatey/`: nuspec + install script actualizados a `v1.2.7` con URL/hash reales de release.
- `debian/`: empaquetado .deb listo para build — `control`, `changelog` (v1.2.7-1), `rules`, `copyright`, `source/format`.

## Decisiones actuales

- Licencia: GPL-3.0
- Prioridad de distribución: Windows
- Artefacto objetivo Windows: zip con `cmdradiopy.exe`
- Las playlists iniciales deben viajar dentro del artefacto final

## Siguientes pasos

1. Confirmar instalación en Scoop/Chocolatey usando la URL pública de `v1.2.7`.
2. Validar ejecución limpia con playlists migradas en una máquina sin estado previo.
3. Actualizar Maintainer y email reales en `debian/control` y `debian/changelog` antes de publicar en repositorios oficiales.
4. Validar ambos workflows en cada nuevo tag `vX.Y.Z`.

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

## Estado de release

- Última release publicada: <https://github.com/smelpillow/cmdRadioPy/releases/tag/v1.2.7>

- `cmdradiopy-win64.zip`: `7d6643dddacbb629ac4d04e9b0908763d0142cd04700bf0ec576b29b845da7c5`
- `cmdradiopy_1.2.7-1_all.deb`: `623949545f7f6ab5b486c85aec94cff3770dc6d8464505fbb01565f6da22ab4f`
