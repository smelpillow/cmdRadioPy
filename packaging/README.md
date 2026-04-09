# Packaging scaffold

Este directorio contiene plantillas y scripts de trabajo para distribución.

## Estado

- `windows/`: scaffold inicial de build para generar `cmdradiopy.exe` + `cmdradiopy-win64.zip`.
- `scoop/`: manifiesto actualizado a `v1.2.2` con URL/hash reales de release.
- `chocolatey/`: nuspec + install script actualizados a `v1.2.2` con URL/hash reales de release.
- `debian/`: empaquetado .deb listo para build — `control`, `changelog` (v1.2.2-1), `rules`, `copyright`, `source/format`.

## Decisiones actuales

- Licencia: GPL-3.0
- Prioridad de distribución: Windows
- Artefacto objetivo Windows: zip con `cmdradiopy.exe`
- Las playlists iniciales deben viajar dentro del artefacto final

## Siguientes pasos

1. Confirmar instalación en Scoop/Chocolatey usando la URL pública de `v1.2.2`.
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

## Hash actual (v1.2.2)

- `cmdradiopy-win64.zip`: `dd4f84fb17fac83d723a6fd337ded6b9f90d19ae6f0bf82d8b98f87ef06a2f22`
