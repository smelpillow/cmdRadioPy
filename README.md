# cmdRadioPy

```text
                       ______            ___       ______  __   
  _________ ___  ____/ / __ \____ _____/ (_)___  / __ \ \/ /   
 / ___/ __ `__ \/ __  / /_/ / __ `/ __  / / __ \/ /_/ /\  /    
/ /__/ / / / / / /_/ / _, _/ /_/ / /_/ / / /_/ / ____/ / /     
\___/_/ /_/ /_/\__,_/_/ |_|\__,_/\__,_/_/\____/_/     /_/      
```

Reproductor de radio online, principalmente se nutre de datos de listas .M3U, pero permite búsqueda online, reproducción aleatoria y continua, gestión de favoritos, historial de últimas escuchas, estadísticas de uso, descarga de playlists desde GitHub y búsqueda en repositorios remotos.

Escucha radio internacionales o temáticas, todo ello desde tu terminal, consumiendo menos de 15 Megas de memoria RAM.

## Requisitos

- mpv instalado y accesible en PATH
  - Windows: instalar `mpv` (por ejemplo con `choco install mpv`) y asegurarse que `mpv.exe` esté en PATH
  - Linux: `sudo apt install mpv` o el gestor de paquetes equivalente
  - macOS: `brew install mpv`
- Python 3.9+
- (Recomendado) Para iconos en la interfaz: `pip install charstyle` (si no está instalado, se usarán caracteres Unicode básicos)
- (Opcional) Para mejor soporte de colores en Windows: `pip install colorama`

### Instalación rápida de dependencias

```bash
pip install -r requirements.txt
```

## Uso rápido

1. Coloca tus listas M3U/M3U8 en la carpeta `playlists/` (puedes añadir muchas, se soporta paginación)
2. Ejecuta:

```bash
python main.py
```

3. Menú principal (organizado por secciones):

   **REPRODUCCIÓN**
   - 1. Mostrar canales (elige playlist y luego canal)
   - 2. Reproducción aleatoria (global) — atajo `r`
   - 3. Reproducir último canal — atajo `u`/`l`

   **BÚSQUEDA**
   - 4. Buscar en canales locales (búsqueda global en tus playlists) — atajo `/`
   - 5. Buscar online (Radio Browser) — atajo `b`
   - 6. Buscar en repositorio remoto — atajo `g`

   **GESTIÓN**
   - 7. Favoritos (incluye editar, exportar JSON/M3U, importar, validar URLs, buscar y aleatorio)
   - 8. Historial (incluye exportar/importar, limpiar, reproducir último y aleatorio)
   - 9. Estadísticas (top emisoras, resumen, fuentes más usadas) — atajo `s`

   **CONFIGURACIÓN Y DATOS**
   - 10. Descargar playlists desde GitHub — atajo `d`
   - 11. Configuración (incluye exportar/importar configuración completa) — atajo `c`

   - 0. Salir — atajo `q`

4. Durante la reproducción usa la interfaz nativa de mpv (pulsa `q` para salir, etc.).

5. mpv se lanza en modo solo audio desactivando el vídeo (`--no-video --vid=no`).

### Validación de URLs

Puedes activar la validación de URLs desde el menú de configuración (opción `v`). Cuando está activada, el programa comprobará si una URL está disponible antes de intentar reproducirla. Esto ayuda a evitar errores con emisoras que ya no están activas.

- **Activación**: Menú principal → 7 (Configuración) → `v`
- **Configuración**: Al activar, puedes establecer un timeout de validación (1-30 segundos, por defecto 5)
- **Funcionamiento**: Usa una petición HTTP ligera para verificar que la URL responde antes de iniciar la reproducción

### Iconos en la interfaz

La interfaz puede mostrar iconos visuales (emojis/Unicode) para mejorar la experiencia. Los iconos están habilitados por defecto y pueden activarse/desactivarse desde el menú de configuración (opción `i`).

## Atajos e interacción

- Listas paginadas (playlists, canales, historial):
  - Numeración global: los índices continúan entre páginas (11, 12, ...)
  - Vista en columnas: se adapta al ancho de la terminal
  - Truncado: nombres largos se acortan con elipsis (…)
  - `n` siguiente, `p` anterior, `g` ir a página #, `0`/`q` volver
  - `s` alterna orden A↔Z; `/` filtra
- Selección de canales: `r` aleatorio entre resultados; `f` añadir/eliminar favorito por número
- Favoritos:
  - `e` exportar JSON, `m` exportar M3U, `i` importar, `r` aleatorio
  - `v` validar todas las URLs, `/` buscar/filtrar
  - Editar favoritos desde el submenú (cambiar nombre/URL)
- Historial: `l` reproducir último canal, `c` limpiar historial completo, `r` aleatorio
- Aleatorio: se omiten emisoras en `blacklist` y si falla la reproducción se prueba otra automáticamente (hasta 3 intentos)
- La interfaz usa colores ANSI; en Windows se habilitan automáticamente si `colorama` está instalado.
- Los conteos de elementos se muestran en títulos y headers para mejor orientación.
- Estadísticas: muestra top emisoras, totales, fuentes más escuchadas y últimas reproducciones.
- Búsqueda mejorada: historial de búsquedas, sugerencias inteligentes basadas en favoritos e historial, y validación de longitud mínima.
- Limpieza automática del historial: configurable por días o número máximo de entradas.

## Búsqueda online


### Radio Browser

- Endpoints con fallback; se respeta `user_agent` y `proxy` de `config.json`.
- Filtros opcionales: país, idioma y bitrate mínimo.
- Tras la búsqueda, puedes listar resultados, reproducir aleatorio, añadir a favoritos y queda en `history.json`.

### Repositorio remoto (GitHub)

- Búsqueda en tiempo real en el repositorio [junguler/m3u-radio-music-playlists](https://github.com/junguler/m3u-radio-music-playlists) sin descargar archivos.
- Opciones de búsqueda:
  - Todas las categorías disponibles (23+ categorías)
  - Solo estilos más populares (12 categorías)
  - Selección personalizada de categorías
- Los resultados se pueden reproducir directamente o descargar las categorías completas.
- No ocupa espacio en disco: busca sin descargar archivos.

## Descarga de playlists desde GitHub

El programa permite descargar playlists directamente desde el repositorio [junguler/m3u-radio-music-playlists](https://github.com/junguler/m3u-radio-music-playlists), que contiene una extensa colección de listas M3U categorizadas por género musical.

### Opciones disponibles

- **Lista completa**: Descarga `everything-full.m3u` con todas las emisoras disponibles
- **Una categoría**: Descarga una categoría específica (Rock, Pop, Jazz, etc.)
- **Múltiples categorías**: Selección personalizada con checkboxes para descargar varias categorías a la vez
- **Estilos más populares**: Descarga rápida de los 12 estilos más populares con un solo clic

### Categorías disponibles

Rock, Pop, Electronic, Hip Hop, Jazz, Classical, Country, Reggae, Metal, Dance, Techno, House, Trance, Latin, Funk, Blues, Alternative, Indie, Hard Rock, Acid Jazz, Smooth Jazz, Eurodance, J-Pop y más.

> **Agradecimiento**: Este proyecto utiliza y agradece el excelente trabajo del repositorio [junguler/m3u-radio-music-playlists](https://github.com/junguler/m3u-radio-music-playlists) de [@junguler](https://github.com/junguler), que proporciona una extensa colección de listas M3U categorizadas y actualizadas regularmente. ¡Gracias por compartir este valioso recurso con la comunidad!

## Configuración (`config.json`)

Archivo opcional ubicado en el directorio de datos del usuario:
- **Windows**: `%APPDATA%\cmdRadioPy\config.json`
- **Linux/Mac**: `~/.config/cmdRadioPy/config.json` (o `$XDG_CONFIG_HOME/cmdRadioPy/config.json`)

### Exportar/Importar configuración completa

Desde el menú de configuración (opción 7), puedes:
- **Exportar (e)**: Guarda en un archivo JSON toda tu configuración, favoritos e historial. Útil para hacer backups o transferir a otro sistema.
- **Importar (i)**: Restaura configuración, favoritos e historial desde un archivo de exportación. Permite elegir qué importar y muestra un resumen antes de confirmar.

Campos soportados:

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
- `validate_urls`: boolean, activa validación de URLs antes de reproducir (por defecto `false`)
- `url_validation_timeout`: segundos de timeout para validación (1-30, por defecto 5)
- `show_icons`: boolean, mostrar iconos en la interfaz (por defecto `true`)
- `min_search_length`: número mínimo de caracteres para búsquedas (por defecto 3)
- `history_cleanup_mode`: modo de limpieza automática del historial: "none", "days" o "count"
- `history_cleanup_days`: días de antigüedad para limpiar (si mode es "days")
- `history_cleanup_max_entries`: número máximo de entradas en historial (si mode es "count")

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
  "blacklist": ["demo", "prueba"],
  "validate_urls": false,
  "url_validation_timeout": 5,
  "show_icons": true,
  "min_search_length": 3,
  "history_cleanup_mode": "none",
  "history_cleanup_days": 30,
  "history_cleanup_max_entries": 500
}
```

## Estructura

### Archivos del proyecto
- `main.py`: CLI con paginación, columnas, colores, búsqueda, favoritos (export/import/aleatorio), configuración, historial (export/import/aleatorio) y búsqueda online con filtros
- `m3u_parser.py`: parser de playlists `.m3u/.m3u8`
- `player.py`: integración con `mpv` en modo audio (sin vídeo)
- `playlists/`: tus listas M3U/M3U8 (dentro del proyecto)

### Archivos de usuario (directorio de datos)
Los siguientes archivos se guardan automáticamente en el directorio de datos del usuario:
- **Windows**: `%APPDATA%\cmdRadioPy\`
- **Linux/Mac**: `~/.config/cmdRadioPy/`
  - `config.json`: configuración de red, reintentos, densidad UI, volumen, temporizador, blacklist, validación de URLs, iconos, búsqueda e historial
  - `favorites.json`: favoritos persistentes
  - `history.json`: historial de reproducciones (con limpieza automática opcional)
  - `search_history.json`: historial de búsquedas para sugerencias

## Notas

- Si `mpv` no está en PATH, el programa mostrará instrucciones de instalación.
- El modo "aleatorio global" selecciona una playlist aleatoria y luego un canal aleatorio dentro (no uniformemente por número de canales).
