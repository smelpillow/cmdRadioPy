# Packaging scaffold

Este directorio contiene plantillas iniciales para distribución en gestores de paquetes.

## Estado

- `scoop/`: manifiesto base para bucket Scoop.
- `chocolatey/`: nuspec + install script base.
- `debian/`: plantilla inicial de empaquetado .deb.

## Siguientes pasos

1. Generar artefactos release por versión (zip/binario y hashes SHA256).
2. Reemplazar `REPLACE_WITH_SHA256` y URLs en plantillas Windows.
3. Definir licencia del proyecto y actualizar metadatos de cada canal.
4. Completar metadatos Debian reales (Maintainer, email, descripción larga, copyright).
5. Automatizar publicación con CI/CD por tag (`vX.Y.Z`).
