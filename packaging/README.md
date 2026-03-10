# Packaging scaffold

Este directorio contiene plantillas y scripts de trabajo para distribución.

## Estado

- `windows/`: scaffold inicial de build para generar `cmdradiopy.exe` + `cmdradiopy-win64.zip`.
- `scoop/`: manifiesto base para bucket Scoop, pendiente de URL/hash definitivos.
- `chocolatey/`: nuspec + install script base, pendiente de URL/hash definitivos.
- `debian/`: plantilla inicial de empaquetado .deb.

## Decisiones actuales

- Licencia: GPL-3.0
- Prioridad de distribución: Windows
- Artefacto objetivo Windows: zip con `cmdradiopy.exe`
- Las playlists iniciales deben viajar dentro del artefacto final

## Siguientes pasos

1. Publicar tag `v1.2.1` (o `vX.Y.Z`) para disparar CI/CD y publicar automáticamente `cmdradiopy-win64.zip` + `cmdradiopy-win64.sha256`.
2. Confirmar instalación en Scoop/Chocolatey usando la URL pública del release publicado.
3. Validar ejecución limpia con playlists migradas en una máquina sin estado previo.
4. Completar metadatos Debian reales (Maintainer, email, descripción larga, copyright).

## CI/CD

- Workflow: `.github/workflows/release-windows.yml`
- Trigger: push de tags con formato `v*.*.*`
- Salidas: release assets `cmdradiopy-win64.zip` y `cmdradiopy-win64.sha256`

## Hash actual (v1.2.1)

- `cmdradiopy-win64.zip`: `fbf23651a4f9fadda0e2f37e122f50ecfc2ef70b6963da82a862c946c7538ac7`
