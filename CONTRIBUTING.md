# Guía de Contribución

¡Gracias por tu interés en contribuir a `cmdRadioPy`! 🎉

Esta guía te ayudará a entender cómo puedes colaborar en el proyecto.

## Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [Cómo Empezar](#cómo-empezar)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Contribución](#proceso-de-contribución)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Mejoras](#sugerir-mejoras)
- [Pull Requests](#pull-requests)

## Código de Conducta

Este proyecto se compromete a proporcionar un ambiente acogedor y respetuoso para todos los colaboradores. Al participar, se espera que mantengas un comportamiento profesional y respetuoso.

## Cómo Empezar

### 1. Fork y Clonar el Repositorio

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU_USUARIO/cmdRadioPy.git
cd cmdRadioPy
```

### 2. Configurar el Entorno de Desarrollo

Asegúrate de tener:

- **Python 3.9 o superior**
- **mpv** instalado y en PATH
  - Windows: `choco install mpv` o descarga desde [mpv.io](https://mpv.io/)
  - Linux: `sudo apt install mpv` (o equivalente)
  - macOS: `brew install mpv`

### 3. Instalar Dependencias

```bash
# Instalar dependencias opcionales (recomendado)
pip install -r requirements.txt
```

### 4. Crear una Rama para tu Contribución

```bash
git checkout -b feature/nombre-de-tu-feature
# o
git checkout -b fix/descripcion-del-bug
```

## Estructura del Proyecto

```
cmdRadioPy/
├── main.py              # Aplicación principal (CLI, menús, lógica de negocio)
├── m3u_parser.py        # Parser de archivos M3U/M3U8
├── player.py            # Integración con mpv (reproducción)
├── playlists/           # Listas M3U de ejemplo (no incluir en commits grandes)
├── requirements.txt     # Dependencias opcionales
├── README.md            # Documentación principal
└── CONTRIBUTING.md      # Esta guía
```

### Archivos de Usuario (no se incluyen en el repo)

Los siguientes archivos se crean automáticamente en el directorio de datos del usuario:
- `config.json` - Configuración del usuario
- `favorites.json` - Favoritos
- `history.json` - Historial de reproducciones
- `search_history.json` - Historial de búsquedas

## Estándares de Código

### Estilo de Código

- **Indentación**: Usa **tabs** (no espacios) para la indentación
- **Longitud de líneas**: Intenta mantener las líneas bajo 100-120 caracteres cuando sea posible
- **Nombres**: Usa nombres descriptivos en inglés
  - Funciones: `snake_case`
  - Constantes: `UPPER_SNAKE_CASE`
  - Variables: `snake_case`

### Convenciones Específicas

- **Manejo de errores**: Usa `try-except` con mensajes informativos
- **Colores ANSI**: Usa la función `c()` y la clase `Colors` para colores consistentes
- **Iconos**: Usa la función `icon()` con fallback a Unicode si `charstyle` no está disponible
- **Mensajes de usuario**: Usa español para mensajes al usuario, comentarios en inglés o español
- **Type hints**: Usa type hints cuando sea apropiado (ya presentes en el código)

### Ejemplo de Estilo

```python
def example_function(name: str, url: str) -> Optional[Dict]:
	"""Descripción breve de la función.
	
	Args:
		name: Nombre del canal
		url: URL del stream
		
	Returns:
		Dict con información del canal o None si hay error
	"""
	try:
		# Lógica aquí
		result = process_channel(name, url)
		print(c(f"Canal procesado: {name}", Colors.GREEN))
		return result
	except Exception as e:
		print(c(f"Error: {e}", Colors.RED))
		return None
```

## Proceso de Contribución

### 1. Antes de Empezar

- Revisa los [issues existentes](https://github.com/TU_USUARIO/cmdRadioPy/issues) para ver si alguien ya está trabajando en algo similar
- Si vas a hacer un cambio grande, abre un issue primero para discutirlo
- Asegúrate de que tu código esté actualizado con la rama `main`:

```bash
git checkout main
git pull upstream main  # o origin main si no tienes upstream configurado
git checkout tu-rama
git rebase main  # o merge main
```

### 2. Hacer Cambios

- **Haz commits pequeños y frecuentes** con mensajes descriptivos
- **Prueba tus cambios** antes de hacer commit
- **Mantén el código consistente** con el estilo existente
- **Añade comentarios** cuando la lógica sea compleja

### 3. Mensajes de Commit

Usa mensajes descriptivos en español o inglés:

```
feat: añadir validación de longitud mínima en búsquedas
fix: corregir error al importar favoritos duplicados
docs: actualizar README con información de iconos
refactor: simplificar lógica de paginación
style: corregir formato de código
```

### 4. Testing

Antes de hacer commit, prueba:

- ✅ El código se ejecuta sin errores
- ✅ Los menús funcionan correctamente
- ✅ No rompes funcionalidades existentes
- ✅ La interfaz se ve bien en diferentes tamaños de terminal
- ✅ Los archivos de usuario se crean/actualizan correctamente

## Reportar Bugs

Si encuentras un bug, por favor:

1. **Verifica que no haya un issue abierto** sobre el mismo problema
2. **Abre un nuevo issue** con:
   - **Título claro y descriptivo**
   - **Descripción del problema** (qué esperabas vs qué pasó)
   - **Pasos para reproducir** el bug
   - **Comportamiento esperado**
   - **Comportamiento actual**
   - **Información del entorno**:
     - Sistema operativo
     - Versión de Python
     - Versión de mpv
     - Si tienes `charstyle` o `colorama` instalados
   - **Logs o mensajes de error** (si aplica)

Ejemplo de buen reporte de bug:

```
Título: Error al validar URL con caracteres especiales

Descripción:
Al intentar validar una URL que contiene caracteres especiales (como "ñ" o "&"), 
la validación falla incorrectamente.

Pasos para reproducir:
1. Ir a Configuración → Validar URLs (v)
2. Añadir favorito con URL: http://example.com/radio?nombre=español&tipo=rock
3. Intentar validar

Comportamiento esperado:
La URL debería validarse correctamente

Comportamiento actual:
Error: "Invalid URL"

Entorno:
- Windows 10
- Python 3.11
- mpv 0.36.0
- charstyle instalado
```

## Sugerir Mejoras

Las mejoras son bienvenidas. Para sugerir una:

1. **Abre un issue** con la etiqueta "enhancement"
2. **Describe claramente**:
   - Qué problema resuelve o qué funcionalidad añade
   - Por qué sería útil
   - Si tienes ideas sobre cómo implementarlo (opcional)

## Pull Requests

### Antes de Enviar un PR

- [ ] Tu código sigue los estándares del proyecto
- [ ] Has probado los cambios localmente
- [ ] Has actualizado la documentación si es necesario
- [ ] Has actualizado el README si añades nuevas funcionalidades
- [ ] Tus commits tienen mensajes descriptivos
- [ ] No hay conflictos con la rama `main`

### Proceso de PR

1. **Asegúrate de que tu fork esté actualizado**:

```bash
git checkout main
git pull upstream main
git checkout tu-rama
git rebase main  # o merge main
```

2. **Push a tu fork**:

```bash
git push origin tu-rama
```

3. **Abre un Pull Request en GitHub**:
   - Título descriptivo
   - Descripción clara de los cambios
   - Menciona si resuelve algún issue (ej: "Fixes #123")
   - Incluye capturas de pantalla si cambias la interfaz

4. **Espera feedback**:
   - El mantenedor revisará tu PR
   - Puede haber sugerencias de cambios
   - Responde a los comentarios y haz los cambios necesarios

### Áreas donde Necesitamos Ayuda

- 🐛 **Bugs**: Corrección de errores
- ✨ **Nuevas funcionalidades**: Ideas del roadmap o nuevas características
- 📚 **Documentación**: Mejorar README, añadir ejemplos, comentarios
- 🎨 **UI/UX**: Mejoras en la interfaz de usuario
- 🌍 **Internacionalización**: Soporte para otros idiomas
- ⚡ **Rendimiento**: Optimizaciones
- 🧪 **Testing**: Añadir tests automatizados (si decides implementarlos)

## Preguntas

Si tienes preguntas sobre cómo contribuir, puedes:

- Abrir un issue con la etiqueta "question"
- Revisar los issues existentes
- Contactar al mantenedor

## Agradecimientos

¡Gracias por contribuir a `cmdRadioPy`! Tu ayuda hace que este proyecto sea mejor para todos. 🎉

---

**Nota**: Esta guía puede evolucionar. Si tienes sugerencias para mejorarla, ¡házselo saber al mantenedor!

