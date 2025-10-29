# cmdRadioPy

Reproductor de listas M3U para terminal usando mpv.

## Requisitos

- mpv instalado y accesible en PATH
  - Windows: instalar `mpv` (por ejemplo con `choco install mpv`) y asegurarse que `mpv.exe` esté en PATH
  - Linux: `sudo apt install mpv` o el gestor de paquetes equivalente
  - macOS: `brew install mpv`
- Python 3.9+
- (Opcional) Para mejor soporte de colores en Windows: `pip install colorama`

## Uso rápido

1. Coloca tus listas M3U/M3U8 en la carpeta `playlists/` (puedes añadir muchas, se soporta paginación)
2. Ejecuta:

```bash
python main.py
```

3. Menú principal:
   - 1. Mostrar canales (elige playlist y luego canal)
   - 2. Buscar en canales (búsqueda global en tus playlists) — atajo `/`
   - 3. Reproducción aleatoria (global) — atajo `r`
   - 4. Buscar online (Radio Browser) — atajo `b`
   - 5. Favoritos (incluye exportar/importar y aleatorio)
   - 6. Historial (incluye exportar/importar y aleatorio)
   - 7 / Q. Salir

4. Durante la reproducción usa la interfaz nativa de mpv (pulsa `q` para salir, etc.).

5. mpv se lanza en modo solo audio desactivando el vídeo (`--no-video --vid=no`).

## Atajos e interacción

- Listas paginadas (playlists, canales, historial):
  - Numeración global: los índices continúan entre páginas (11, 12, ...)
  - Vista en columnas: se adapta al ancho de la terminal
  - Truncado: nombres largos se acortan con elipsis (…)
  - `n` siguiente, `p` anterior, `g` ir a página #, `0`/`q` volver
  - `s` alterna orden A↔Z; `/` filtra
- Selección de canales: `r` aleatorio entre resultados; `f` añadir/eliminar favorito por número
- Favoritos e Historial: opción `r` para reproducción aleatoria con repetición opcional
- Aleatorio: se omiten emisoras en `blacklist` y si falla la reproducción se prueba otra automáticamente (hasta 3 intentos)
- La interfaz usa colores ANSI; en Windows se habilitan automáticamente si `colorama` está instalado.

## Búsqueda online (Radio Browser)

- Endpoints con fallback; se respeta `user_agent` y `proxy` de `config.json`.
- Filtros opcionales: país, idioma y bitrate mínimo.
- Tras la búsqueda, puedes listar resultados, reproducir aleatorio, añadir a favoritos y queda en `history.json`.

## Configuración (`config.json`)

Archivo opcional en la raíz del proyecto. Campos soportados:

- `user_agent`: string (ej. "Mozilla/5.0 ...")
- `proxy`: string (ej. "http://127.0.0.1:8080")
- `retries`: número de reintentos si falla la reproducción (0-5)
- `retry_delay_sec`: segundos entre reintentos (0-10)
- `ui_spacing`: "comfortable" (más aire) o "compact" (más denso)
- `page_size`: tamaño de página para listas (5-100)
- `sort_playlists`: "asc" o "desc"
- `sort_channels`: "asc" o "desc"
- `volume`: volumen por defecto de mpv (0-130), por defecto 40
- `shutdown_minutes`: tiempo de apagado automático (0 para desactivar)
- `blacklist`: array de palabras/fragmentos a excluir en aleatorio (coincidencia por texto en nombre/URL)

Ejemplo:

```json
{
  "user_agent": "Mozilla/5.0",
  "proxy": "http://127.0.0.1:8080",
  "retries": 2,
  "retry_delay_sec": 2,
  "ui_spacing": "comfortable",
  "page_size": 20,
  "sort_playlists": "asc",
  "sort_channels": "asc",
  "volume": 40,
  "shutdown_minutes": 0,
  "blacklist": ["demo", "prueba"]
}
```

## Estructura

- `main.py`: CLI con paginación, columnas, colores, búsqueda, favoritos (export/import/aleatorio), configuración, historial (export/import/aleatorio) y búsqueda online con filtros
- `m3u_parser.py`: parser de playlists `.m3u/.m3u8`
- `player.py`: integración con `mpv` en modo audio (sin vídeo)
- `playlists/`: tus listas
- `favorites.json`: favoritos persistentes
- `history.json`: historial de reproducciones (recientes)
- `config.json`: configuración de red, reintentos, densidad UI, volumen, temporizador y blacklist

## Notas

- Si `mpv` no está en PATH, el programa mostrará instrucciones de instalación.
- El modo "aleatorio global" selecciona una playlist aleatoria y luego un canal aleatorio dentro (no uniformemente por número de canales).
