from __future__ import annotations
import os
import sys
import random
import shutil
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

try:
	from charstyle import Icon
	CHARSTYLE_AVAILABLE = True
except ImportError:
	CHARSTYLE_AVAILABLE = False
	# Fallback a caracteres Unicode básicos si charstyle no está disponible
	class Icon:
		MUSIC = "♪"
		RADIO = "📻"
		PLAYLIST = "📋"
		SEARCH = "🔍"
		RANDOM = "🎲"
		ONLINE = "🌐"
		FAVORITE = "⭐"
		HISTORY = "📜"
		CONFIG = "⚙️"
		EXIT = "🚪"
		PLAY = "▶"
		PAUSE = "⏸"
		STOP = "⏹"
		CHECK = "✓"
		CROSS = "✗"
		WARNING = "⚠"
		ARROW_RIGHT = "→"
		ARROW_LEFT = "←"
		EDIT = "✎"
		EXPORT = "📤"
		IMPORT = "📥"
		TRASH = "🗑"
		STAR = "★"
		VOLUME = "🔊"
		STATS = "📊"
		LAST = "⏮"
		FILTER = "🔎"

from m3u_parser import parse_m3u_file
from player import play_url, play_url_with_custom_osd, MpvNotFoundError


BASE_DIR = os.path.dirname(__file__)
PLAYLISTS_DIR = os.path.join(BASE_DIR, 'playlists')

# Directorio de datos del usuario
def get_user_data_dir() -> str:
	"""Retorna el directorio de datos del usuario según el SO."""
	if os.name == 'nt':  # Windows
		appdata = os.getenv('APPDATA') or os.path.expanduser('~')
		data_dir = os.path.join(appdata, 'cmdRadioPy')
	else:  # Linux/Mac
		config_home = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
		data_dir = os.path.join(config_home, 'cmdRadioPy')
	# Asegurar que el directorio existe
	os.makedirs(data_dir, exist_ok=True)
	return data_dir

USER_DATA_DIR = get_user_data_dir()
FAVORITES_FILE = os.path.join(USER_DATA_DIR, 'favorites.json')
HISTORY_FILE = os.path.join(USER_DATA_DIR, 'history.json')
CONFIG_FILE = os.path.join(USER_DATA_DIR, 'config.json')
SEARCH_HISTORY_FILE = os.path.join(USER_DATA_DIR, 'search_history.json')

# Estado de configuración (editable en tiempo de ejecución)
CURRENT_PAGE_SIZE = 20
SORT_PLAYLISTS_ASC = True
SORT_CHANNELS_ASC = True
CONFIG: Dict[str, Optional[str]] = {}

# Longitud mínima para búsquedas (por defecto 3 caracteres)
MIN_SEARCH_LENGTH = 3


# --- Colores y estilos ---
class Colors:
	RESET = "\033[0m"
	BOLD = "\033[1m"
	DIM = "\033[2m"
	UNDERLINE = "\033[4m"
	RED = "\033[31m"
	GREEN = "\033[32m"
	YELLOW = "\033[33m"
	BLUE = "\033[34m"
	MAGENTA = "\033[35m"
	CYAN = "\033[36m"
	WHITE = "\033[37m"


# --- Iconos ---
# Mapeo de nuestros nombres de iconos a charstyle
ICON_MAP = {
	'MUSIC': Icon.MUSIC if hasattr(Icon, 'MUSIC') else '♪',
	'RADIO': Icon.RADIO if hasattr(Icon, 'RADIO') else '📻',
	'PLAYLIST': Icon.LIST if hasattr(Icon, 'LIST') else Icon.FOLDER if hasattr(Icon, 'FOLDER') else '📋',
	'SEARCH': Icon.SEARCH if hasattr(Icon, 'SEARCH') else '🔍',
	'RANDOM': Icon.DICE if hasattr(Icon, 'DICE') else '🎲',
	'ONLINE': Icon.GLOBE if hasattr(Icon, 'GLOBE') else Icon.WEB if hasattr(Icon, 'WEB') else '🌐',
	'FAVORITE': Icon.STAR if hasattr(Icon, 'STAR') else '⭐',
	'HISTORY': Icon.CLOCK if hasattr(Icon, 'CLOCK') else Icon.TIME if hasattr(Icon, 'TIME') else '📜',
	'CONFIG': Icon.GEAR if hasattr(Icon, 'GEAR') else Icon.SETTINGS if hasattr(Icon, 'SETTINGS') else '⚙️',
	'EXIT': Icon.EXIT if hasattr(Icon, 'EXIT') else Icon.DOOR if hasattr(Icon, 'DOOR') else '🚪',
	'PLAY': Icon.PLAY if hasattr(Icon, 'PLAY') else '▶',
	'PAUSE': Icon.PAUSE if hasattr(Icon, 'PAUSE') else '⏸',
	'STOP': Icon.STOP if hasattr(Icon, 'STOP') else '⏹',
	'CHECK': Icon.CHECK if hasattr(Icon, 'CHECK') else Icon.TICK if hasattr(Icon, 'TICK') else '✓',
	'CROSS': Icon.CROSS if hasattr(Icon, 'CROSS') else Icon.X if hasattr(Icon, 'X') else '✗',
	'WARNING': Icon.WARNING if hasattr(Icon, 'WARNING') else Icon.ALERT if hasattr(Icon, 'ALERT') else '⚠',
	'INFO': Icon.INFO if hasattr(Icon, 'INFO') else 'ℹ',
	'ARROW_RIGHT': Icon.ARROW_RIGHT if hasattr(Icon, 'ARROW_RIGHT') else '→',
	'ARROW_LEFT': Icon.ARROW_LEFT if hasattr(Icon, 'ARROW_LEFT') else '←',
	'EDIT': Icon.EDIT if hasattr(Icon, 'EDIT') else Icon.PENCIL if hasattr(Icon, 'PENCIL') else '✎',
	'EXPORT': Icon.UPLOAD if hasattr(Icon, 'UPLOAD') else Icon.EXPORT if hasattr(Icon, 'EXPORT') else '📤',
	'IMPORT': Icon.DOWNLOAD if hasattr(Icon, 'DOWNLOAD') else Icon.IMPORT if hasattr(Icon, 'IMPORT') else '📥',
	'TRASH': Icon.TRASH if hasattr(Icon, 'TRASH') else Icon.DELETE if hasattr(Icon, 'DELETE') else '🗑',
	'STAR': Icon.STAR if hasattr(Icon, 'STAR') else '★',
	'VOLUME': Icon.VOLUME if hasattr(Icon, 'VOLUME') else Icon.SOUND if hasattr(Icon, 'SOUND') else '🔊',
	'STATS': Icon.CHART if hasattr(Icon, 'CHART') else Icon.STATS if hasattr(Icon, 'STATS') else '📊',
	'LAST': Icon.PREV if hasattr(Icon, 'PREV') else Icon.REWIND if hasattr(Icon, 'REWIND') else '⏮',
	'FILTER': Icon.FILTER if hasattr(Icon, 'FILTER') else Icon.SEARCH if hasattr(Icon, 'SEARCH') else '🔎',
	'VALIDATE': Icon.CHECK if hasattr(Icon, 'CHECK') else Icon.TICK if hasattr(Icon, 'TICK') else '✓',
	'CLOCK': Icon.CLOCK if hasattr(Icon, 'CLOCK') else Icon.TIME if hasattr(Icon, 'TIME') else '🕐',
	'LIST': Icon.LIST if hasattr(Icon, 'LIST') else '📑',
}


class Icons:
	"""Wrapper para iconos usando charstyle si está disponible."""
	@staticmethod
	def get_icon(name: str) -> str:
		"""Obtiene un icono por nombre."""
		return ICON_MAP.get(name.upper(), "")


def enable_colors_on_windows() -> None:
	# En Windows activamos colores si colorama está disponible
	try:
		import colorama  # type: ignore
		colorama.just_fix_windows_console()
	except Exception:
		pass


def clear_screen() -> None:
	# Limpia la terminal según el SO
	try:
		os.system('cls' if os.name == 'nt' else 'clear')
	except Exception:
		print('\n' * 2)


def c(text: str, color: str) -> str:
	return f"{color}{text}{Colors.RESET}"


def bold(text: str) -> str:
	return f"{Colors.BOLD}{text}{Colors.RESET}"


def dim(text: str) -> str:
	return f"{Colors.DIM}{text}{Colors.RESET}"


def term_width(default: int = 80) -> int:
	try:
		return max(40, shutil.get_terminal_size((default, 20)).columns)
	except Exception:
		return default


def line(char: str = '─') -> str:
	return char * (term_width() - 0)


def header(title: str) -> None:
	clear_screen()
	print(c(line(), Colors.BLUE))
	print(bold(c(f"  {title}", Colors.CYAN)))
	print(c(line(), Colors.BLUE))
	if is_ui_comfortable():
		print()


def prompt_yes_no(message: str, default_yes: bool = True) -> Optional[bool]:
	"""Devuelve True si la respuesta es afirmativa, None si se cancela con 'q'."""
	default_hint = 'S/n' if default_yes else 's/N'
	while True:
		resp = input(c(f"{message} ({default_hint}, q para salir): ", Colors.CYAN)).strip().lower()
		if not resp:
			return default_yes
		if resp in ('q', 'quit', 'salir'):
			return None  # Cancelar/salir
		if resp in ('s', 'si', 'sí', 'y', 'yes'):
			return True
		if resp in ('n', 'no'):
			return False
		print(c("Entrada no válida. Responde con s/n o q para salir.", Colors.RED))


def ensure_playlists_dir() -> None:
	if not os.path.isdir(PLAYLISTS_DIR):
		os.makedirs(PLAYLISTS_DIR, exist_ok=True)


def load_config() -> Dict[str, Optional[str]]:
	# Valores por defecto
	cfg: Dict[str, Optional[str]] = {
		'user_agent': None,
		'proxy': None,
		'retries': 0,
		'retry_delay_sec': 2,
		'ui_spacing': 'comfortable',  # 'comfortable' o 'compact'
		'page_size': 20,
		'sort_playlists': 'asc',
		'sort_channels': 'asc',
		'volume': 40,
		'shutdown_minutes': 0,
		'blacklist': [],  # lista de patrones (strings) para excluir en aleatorio
		'validate_urls': False,  # validar URLs antes de reproducir
		'url_validation_timeout': 5,  # timeout en segundos para validación
		'show_icons': True,  # mostrar iconos en la interfaz
		'use_custom_osd': False,  # OSD propia en terminal (logo, barra, botones) en lugar de depender de mpv
	}
	if os.path.isfile(CONFIG_FILE):
		try:
			with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
				data = json.load(f)
				if isinstance(data, dict):
					cfg.update(data)
		except Exception:
			pass
	return cfg


def save_config() -> None:
	try:
		with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
			json.dump(CONFIG, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


def is_ui_comfortable() -> bool:
	mode = (CONFIG.get('ui_spacing') or 'comfortable').lower()
	return mode != 'compact'


def icons_enabled() -> bool:
	"""Retorna True si los iconos están habilitados."""
	return CONFIG.get('show_icons') is not False  # Por defecto True


def icon(name: str) -> str:
	"""Retorna un icono si están habilitados."""
	if not icons_enabled():
		return ""
	icon_char = Icons.get_icon(name.upper())
	return f"{icon_char} " if icon_char else ""


def build_mpv_args_from_config() -> List[str]:
	args: List[str] = []
	ua = CONFIG.get('user_agent')
	if ua:
		args.append(f"--user-agent={ua}")
	proxy = CONFIG.get('proxy')
	if proxy:
		args.append(f"--http-proxy={proxy}")
	# Volumen (0-130 aprox en mpv)
	try:
		vol = int(CONFIG.get('volume') or 40)
	except Exception:
		vol = 40
	vol = max(0, min(130, vol))
	args.append(f"--volume={vol}")
	# Temporizador de apagado (en minutos) usando --length en segundos
	try:
		mins = int(CONFIG.get('shutdown_minutes') or 0)
	except Exception:
		mins = 0
	if mins > 0:
		args.append(f"--length={mins * 60}")
	return args

# --- HTTP helper para búsqueda online ---

def build_opener_from_config():
	import urllib.request
	handlers: List = []
	proxy = CONFIG.get('proxy')
	if proxy:
		handlers.append(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
	opener = urllib.request.build_opener(*handlers) if handlers else urllib.request.build_opener()
	ua = CONFIG.get('user_agent') or 'cmdRadioPy/1.0'
	opener.addheaders = [('User-Agent', ua), ('Accept', 'application/json')]
	return opener


def http_get_json(url: str, timeout: int = 8):
	import urllib.request
	import urllib.error
	opener = build_opener_from_config()
	try:
		with opener.open(url, timeout=timeout) as resp:
			data = resp.read()
			return json.loads(data.decode('utf-8', errors='ignore'))
	except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
		return None


def http_download_file(url: str, dest_path: str, timeout: int = 30):
	"""Descarga un archivo desde una URL y lo guarda en dest_path.
	
	Returns:
		Tupla (success, error_message) donde success es True si la descarga fue exitosa,
		y error_message contiene el mensaje de error si falló, o None si fue exitosa.
	"""
	import urllib.request
	import urllib.error
	opener = build_opener_from_config()
	try:
		with opener.open(url, timeout=timeout) as resp:
			# Verificar código de estado HTTP
			if hasattr(resp, 'status'):
				if resp.status != 200:
					return False, f"HTTP {resp.status}: {resp.reason}"
			data = resp.read()
			# Asegurar que el directorio destino existe
			dest_dir = os.path.dirname(dest_path)
			if dest_dir:
				os.makedirs(dest_dir, exist_ok=True)
			with open(dest_path, 'wb') as f:
				f.write(data)
			return True, None
	except urllib.error.HTTPError as e:
		return False, f"HTTP {e.code}: {e.reason}"
	except urllib.error.URLError as e:
		return False, f"Error de URL: {str(e)}"
	except TimeoutError:
		return False, "Timeout: La descarga tardó demasiado"
	except OSError as e:
		return False, f"Error de sistema: {str(e)}"
	except Exception as e:
		return False, f"Error inesperado: {str(e)}"


def http_fetch_content(url: str, timeout: int = 30):
	"""Descarga el contenido de una URL y lo retorna como string.
	
	Returns:
		Tupla (content, error_message) donde content es el contenido si fue exitoso,
		y error_message contiene el mensaje de error si falló, o None si fue exitoso.
	"""
	import urllib.request
	import urllib.error
	opener = build_opener_from_config()
	try:
		with opener.open(url, timeout=timeout) as resp:
			# Verificar código de estado HTTP
			if hasattr(resp, 'status'):
				if resp.status != 200:
					return None, f"HTTP {resp.status}: {resp.reason}"
			data = resp.read()
			# Intentar decodificar como UTF-8
			try:
				content = data.decode('utf-8')
			except UnicodeDecodeError:
				# Si falla, intentar con latin-1 o ignorar errores
				content = data.decode('utf-8', errors='ignore')
			return content, None
	except urllib.error.HTTPError as e:
		return None, f"HTTP {e.code}: {e.reason}"
	except urllib.error.URLError as e:
		return None, f"Error de URL: {str(e)}"
	except TimeoutError:
		return None, "Timeout: La descarga tardó demasiado"
	except Exception as e:
		return None, f"Error inesperado: {str(e)}"


# --- Utilidades de blacklist ---

def get_blacklist() -> List[str]:
	bl = CONFIG.get('blacklist') or []
	if isinstance(bl, list):
		return [str(x).lower() for x in bl]
	return []


def is_blacklisted(name: str, url: str) -> bool:
	patterns = get_blacklist()
	text = f"{name} {url}".lower()
	return any(pat in text for pat in patterns if pat)


def filter_not_blacklisted(items: List[Dict]) -> List[Dict]:
	res: List[Dict] = []
	for it in items:
		name = it.get('name') or it.get('url') or ''
		url = it.get('url') or ''
		if not is_blacklisted(name, url):
			res.append(it)
	return res


def online_search_radio_browser() -> None:
	from urllib.parse import quote
	header("Búsqueda online (Radio Browser)")
	
	# Cargar historial de búsquedas y sugerencias
	search_history = load_search_history()
	favorites = load_favorites()
	play_history = load_history()
	
	# Mostrar búsquedas recientes si existen
	if search_history:
		print(c("Búsquedas recientes:", Colors.CYAN))
		for i, h in enumerate(search_history[:5], 1):
			print(f"  {c(str(i), Colors.YELLOW)}. {h}")
		print()
	
	# Obtener sugerencias
	suggestions = get_search_suggestions("", search_history, favorites, play_history)
	query = prompt_with_suggestions("Texto a buscar (nombre de emisora) o número de sugerencia: ", suggestions, search_history)
	
	if not query:
		print(c("Búsqueda vacía.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Validar longitud mínima de búsqueda
	min_length = CONFIG.get('min_search_length', MIN_SEARCH_LENGTH)
	try:
		min_length = int(min_length)
	except Exception:
		min_length = MIN_SEARCH_LENGTH
	
	if len(query) < min_length:
		print(c(f"⚠ Búsqueda muy corta ({len(query)} caracteres).", Colors.YELLOW))
		print(c(f"Se recomienda al menos {min_length} caracteres para evitar resultados excesivos.", Colors.YELLOW))
		if len(query) == 1:
			# Si es una sola letra, no permitir directamente
			result = prompt_yes_no(f"¿Realmente quieres buscar con solo '{query}'? (puede tardar mucho y generar miles de resultados)", default_yes=False)
			if result is None or not result:
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				return
		elif len(query) == 2:
			# Si son 2 letras, advertir
			result = prompt_yes_no(f"¿Continuar con la búsqueda '{query}'? (puede generar muchos resultados)", default_yes=False)
			if result is None or not result:
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				return
	
	# Añadir a historial de búsquedas
	add_to_search_history(query)
	
	country = input(c("Filtrar país (código o nombre, opcional): ", Colors.CYAN)).strip()
	language = input(c("Filtrar idioma (opcional): ", Colors.CYAN)).strip()
	bitrate = input(c("Bitrate mínimo (kbps, opcional): ", Colors.CYAN)).strip()
	
	print(c(f"Buscando '{query}' online...", Colors.CYAN))
	endpoints = [
		"https://fi1.api.radio-browser.info/json/stations/search?name=$searchTerm",
		"https://de2.api.radio-browser.info/json/stations/search?name=$searchTerm",
	]
	encoded = quote(query)
	extra = ''
	if country:
		extra += f"&country={quote(country)}"
	if language:
		extra += f"&language={quote(language)}"
	if bitrate and bitrate.isdigit():
		extra += f"&bitrate_min={bitrate}"
	results: List[Dict[str, str]] = []
	for ep in endpoints:
		base = ep.replace('$searchTerm', encoded) + extra
		data = http_get_json(base)
		if not data or not isinstance(data, list):
			continue
		for item in data:
			if not isinstance(item, dict):
				continue
			name = (item.get('name') or '').strip()
			stream = (item.get('url_resolved') or item.get('url') or '').strip()
			if not stream:
				continue
			country_val = (item.get('country') or '').strip()
			badge = f"[{country_val}]" if country_val else ''
			entry = {'name': name or stream, 'url': stream, 'source': f"online {badge}".strip()}
			if not is_blacklisted(entry['name'], entry['url']):
				results.append(entry)
		if len(results) >= 500:
			break
	if not results:
		print(c("Sin resultados online.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	# Interacción
	while True:
		labels = [f"{r['name']} {dim(r['source'])}" for r in results]
		print()
		header(f"Resultados online ({len(results)})")
		print(f"  {c('1.', Colors.YELLOW)} Aleatorio entre resultados (r)  |  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		sel = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if sel in ('0', 'q'):
			return
		if sel in ('1', 'r'):
			attempts = 0
			while True:
				pool = results
				if not pool:
					print(c("No hay resultados para aleatorio.", Colors.RED))
					return
				item = random.choice(pool)
				print(f"{c('Reproduciendo (online aleatorio):', Colors.GREEN)} {item['name']} {dim(item['source'])}")
				try:
					code = play_with_config(
						item['url'],
						item.get('name'),
						play_mode="Aleatorio (online)",
						source=item.get('source'),
					)
				except MpvNotFoundError as e:
					print(str(e))
					return
				if code != 0:
					attempts += 1
					if attempts <= 3:
						print(c("Fallo, probando otra emisora...", Colors.YELLOW))
						continue
					else:
						print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
						return
				# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
				append_history(item['name'], item['url'], 'online')
				offer_add_favorite(item['name'], item['url'], 'online')
				result = prompt_yes_no("¿Reproducir otra emisora aleatoria online?", default_yes=True)
				if result is None or not result:
					return
			continue
		idx = paginated_select(labels, "Resultados online")
		if idx in (0, -1):
			return
		item = results[idx - 1]
		print(f"{c('Reproduciendo:', Colors.GREEN)} {item['name']} {dim(item['source'])}")
		try:
			code = play_with_config(
				item['url'],
				item.get('name'),
				play_mode="Búsqueda online",
				source=item.get('source'),
			)
		except MpvNotFoundError as e:
			print(str(e))
			return
		# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
		if code == 0:
			append_history(item['name'], item['url'], 'online')
			offer_add_favorite(item['name'], item['url'], 'online')


def validate_url(url: str, timeout: int = 5) -> bool:
	"""
	Valida si una URL está activa haciendo una petición HEAD.
	Retorna True si la URL responde, False en caso contrario.
	"""
	import urllib.request
	import urllib.error
	
	# Algunos servidores de streaming no responden bien a HEAD, así que usamos GET con range
	try:
		req = urllib.request.Request(url, method='GET')
		req.add_header('Range', 'bytes=0-1')  # Solo pedir los primeros bytes
		req.add_header('User-Agent', CONFIG.get('user_agent') or 'cmdRadioPy/1.0')
		
		# Configurar proxy si existe
		if CONFIG.get('proxy'):
			proxy_handler = urllib.request.ProxyHandler({
				'http': CONFIG.get('proxy'),
				'https': CONFIG.get('proxy')
			})
			opener = urllib.request.build_opener(proxy_handler)
		else:
			opener = urllib.request.build_opener()
		
		with opener.open(req, timeout=timeout) as response:
			# Si obtenemos cualquier respuesta (incluso 206 Partial Content), la URL está activa
			return response.status in (200, 206, 301, 302, 303, 307, 308)
	except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
		return False
	except Exception:
		# En caso de cualquier otro error, asumimos que la URL no es válida
		return False


def _osd_log(message: str) -> None:
	"""Escribe una línea con timestamp en cmdradiopy.log (solo si OSD está activa)."""
	if not CONFIG.get('use_custom_osd'):
		return
	try:
		log_path = os.path.join(USER_DATA_DIR, "cmdradiopy.log")
		with open(log_path, "a", encoding="utf-8") as f:
			f.write(f"{datetime.now().isoformat()}  {message}\n")
	except Exception:
		pass


def play_with_config(
	url: str,
	station_name: Optional[str] = None,
	play_mode: Optional[str] = None,
	source: Optional[str] = None,
) -> int:
	# Validar URL si está activada la opción
	validate = CONFIG.get('validate_urls')
	if isinstance(validate, bool) and validate:
		timeout = 5
		try:
			timeout = int(CONFIG.get('url_validation_timeout') or 5)
		except Exception:
			pass
		
		icon_val = icon('VALIDATE')
		print(c(f"{icon_val}Validando URL...", Colors.CYAN), end='', flush=True)
		if not validate_url(url, timeout=timeout):
			cross_icon = Icons.get_icon('CROSS')
			print(c(f" {cross_icon} URL no disponible", Colors.RED))
			return 1  # Código de error
		check_icon = Icons.get_icon('CHECK')
		print(c(f" {check_icon} URL válida", Colors.GREEN))
	
	extra = build_mpv_args_from_config()
	retries = 0
	try:
		retries = int(CONFIG.get('retries') or 0)
	except Exception:
		retries = 0
	try:
		delay = int(CONFIG.get('retry_delay_sec') or 2)
	except Exception:
		delay = 2
	attempt = 0
	while True:
		if CONFIG.get('use_custom_osd'):
			print(c("OSD propia activada (logo, barra, botones). Conectando a mpv...", Colors.CYAN))
			_osd_log("OSD activada, iniciando reproducción con IPC")
			try:
				_osd_hide_cursor()
				code = play_url_with_custom_osd(
					url,
					station_name,
					play_mode=play_mode,
					source=source,
					extra_args=extra,
					draw_osd_cb=draw_custom_osd,
					log_cb=_osd_log,
				)
			except Exception as ex:
				print(c(f"Error al usar OSD propia: {ex}", Colors.RED))
				_osd_log(f"Error OSD: {ex}")
				code = play_url(url, extra_args=extra)
			finally:
				_osd_show_cursor()
				_osd_reset_state()
		else:
			code = play_url(url, extra_args=extra)
		if code == 0:
			return 0
		if attempt >= retries:
			return code
		print(c(f"Fallo de reproducción (código {code}). Reintentando...", Colors.YELLOW))
		attempt += 1
		time.sleep(max(0, delay))


def cleanup_history_auto() -> None:
	"""
	Limpia el historial automáticamente según la configuración.
	Puede limpiar por días o por número máximo de entradas.
	Esta función asume que el historial ya está guardado en el archivo.
	"""
	hist = load_history()
	if not hist:
		return
	
	# Verificar configuración de limpieza
	cleanup_mode = CONFIG.get('history_cleanup_mode', 'none')  # 'none', 'days', 'count'
	
	if cleanup_mode == 'days':
		# Limpiar por días
		days = CONFIG.get('history_cleanup_days', 30)
		try:
			days = int(days)
		except Exception:
			days = 30
		
		if days > 0:
			cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
			hist = [h for h in hist if h.get('ts', 0) >= cutoff_time]
	
	elif cleanup_mode == 'count':
		# Limpiar por número máximo de entradas
		max_entries = CONFIG.get('history_cleanup_max_entries', 200)
		try:
			max_entries = int(max_entries)
		except Exception:
			max_entries = 200
		
		if max_entries > 0 and len(hist) > max_entries:
			hist = hist[-max_entries:]
	
	# Guardar historial limpiado
	save_history(hist)


def append_history(name: str, url: str, source: Optional[str], duration: Optional[float] = None, attrs: Optional[Dict] = None) -> None:
	entry = {
		'name': name or url,
		'url': url,
		'source': source or '',
		'ts': int(time.time()),
	}
	if duration is not None:
		entry['duration'] = duration
	if attrs:
		entry['attrs'] = attrs
	hist: List[Dict[str, str]] = []
	if os.path.isfile(HISTORY_FILE):
		try:
			with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
				data = json.load(f)
				if isinstance(data, list):
					hist = data
		except Exception:
			pass
	hist.append(entry)
	
	# Limpiar automáticamente antes de guardar (solo si está configurado)
	cleanup_mode = CONFIG.get('history_cleanup_mode', 'none')
	if cleanup_mode != 'none':
		# Guardar primero con la nueva entrada
		try:
			with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
				json.dump(hist, f, ensure_ascii=False, indent=2)
		except Exception:
			pass
		# Luego limpiar
		cleanup_history_auto()
		return  # Ya se guardó en cleanup_history_auto
	
	# Si no hay limpieza automática, limitar a últimos 500 como máximo (fallback)
	if len(hist) > 500:
		hist = hist[-500:]
	
	try:
		with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
			json.dump(hist, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


def _matches_metadata_filter(channel: Dict, filters: Dict) -> bool:
	"""Verifica si un canal coincide con los filtros de metadatos."""
	attrs = channel.get('attrs', {})
	
	# Filtro por género
	if 'genre' in filters:
		genre_filter = filters['genre'].lower()
		group_title = (attrs.get('group-title') or '').lower()
		if genre_filter not in group_title:
			return False
	
	# Filtro por país
	if 'country' in filters:
		country_filter = filters['country'].lower()
		tvg_country = (attrs.get('tvg-country') or attrs.get('country') or '').lower()
		if country_filter not in tvg_country:
			return False
	
	# Filtro por idioma
	if 'language' in filters:
		lang_filter = filters['language'].lower()
		tvg_lang = (attrs.get('tvg-language') or attrs.get('language') or '').lower()
		if lang_filter not in tvg_lang:
			return False
	
	# Filtro por bitrate mínimo
	if 'min_bitrate' in filters:
		min_bitrate = filters['min_bitrate']
		audio_bitrate = attrs.get('audio-bitrate') or attrs.get('bitrate')
		if audio_bitrate:
			try:
				bitrate_val = int(audio_bitrate)
				if bitrate_val < min_bitrate:
					return False
			except ValueError:
				pass
		else:
			return False  # Si no tiene bitrate y se requiere, excluir
	
	return True


def format_channel_metadata(channel: Dict) -> str:
	"""Formatea los metadatos de un canal para mostrar."""
	attrs = channel.get('attrs', {})
	parts = []
	
	# Bitrate
	if 'audio-bitrate' in attrs:
		parts.append(f"Bitrate: {attrs['audio-bitrate']} kbps")
	elif 'bitrate' in attrs:
		parts.append(f"Bitrate: {attrs['bitrate']} kbps")
	
	# Género
	if 'group-title' in attrs:
		parts.append(f"Género: {attrs['group-title']}")
	
	# País
	if 'tvg-country' in attrs:
		parts.append(f"País: {attrs['tvg-country']}")
	elif 'country' in attrs:
		parts.append(f"País: {attrs['country']}")
	
	# Idioma
	if 'tvg-language' in attrs:
		parts.append(f"Idioma: {attrs['tvg-language']}")
	elif 'language' in attrs:
		parts.append(f"Idioma: {attrs['language']}")
	
	# URL type hint
	url = channel.get('url', '')
	if url.startswith('http'):
		if 'm3u8' in url.lower():
			parts.append("Formato: HLS")
		elif '.mp3' in url.lower():
			parts.append("Formato: MP3")
		elif '.aac' in url.lower():
			parts.append("Formato: AAC")
		else:
			parts.append("Formato: Stream")
	
	return " | ".join(parts) if parts else "Sin metadatos"


def show_channel_preview(channel: Dict, source: Optional[str] = None) -> None:
	"""Muestra una previsualización de información del canal antes de reproducir."""
	name = channel.get('name') or channel.get('url') or 'Unknown'
	url = channel.get('url') or ''
	attrs = channel.get('attrs', {})
	
	print()
	header(f"Información del canal")
	print(c(f"Nombre: {name}", Colors.CYAN))
	if source:
		print(c(f"Fuente: {source}", Colors.DIM))
	
	metadata = format_channel_metadata(channel)
	if metadata:
		print(c(f"Metadatos: {metadata}", Colors.DIM))
	
	if url:
		url_preview = url[:80] + '...' if len(url) > 80 else url
		print(c(f"URL: {url_preview}", Colors.DIM))
	print()


def load_history() -> List[Dict[str, str]]:
	if not os.path.isfile(HISTORY_FILE):
		return []
	try:
		with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			if isinstance(data, list):
				return [d for d in data if isinstance(d, dict) and 'url' in d]
	except Exception:
		pass
	return []


def save_history(entries: List[Dict[str, str]]) -> None:
	try:
		with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
			json.dump(entries, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


def list_playlists() -> List[str]:
	ensure_playlists_dir()
	all_files = os.listdir(PLAYLISTS_DIR)
	pls = [
		f for f in all_files
		if f.lower().endswith(('.m3u', '.m3u8')) and os.path.isfile(os.path.join(PLAYLISTS_DIR, f))
	]
	pls.sort(reverse=not SORT_PLAYLISTS_ASC)
	return pls


def strip_ansi_len(s: str) -> int:
	# Quita los códigos de color que usamos para calcular longitud visual aproximada
	for code in (Colors.RESET, Colors.BOLD, Colors.DIM, Colors.UNDERLINE,
				Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE,
				Colors.MAGENTA, Colors.CYAN, Colors.WHITE):
		s = s.replace(code, '')
	return len(s)


def truncate_label(label: str, max_len: int) -> str:
	if max_len <= 0:
		return ''
	if len(label) <= max_len:
		return label
	if max_len <= 1:
		return label[:max_len]
	# Elipsis Unicode
	return label[: max_len - 1] + '…'


def paginated_select(options: List[str], title: str, page_size: int = None, show_count: bool = True) -> int:
	if page_size is None:
		page_size = CURRENT_PAGE_SIZE
	if not options:
		return -1
	page = 0
	total = len(options)
	pages = max(1, (total + page_size - 1) // page_size)
	while True:
		start = page * page_size
		end = min(start + page_size, total)
		count_info = f" ({total})" if show_count and total > 0 else ""
		header(f"{title}{count_info}  {dim(f'(página {page + 1}/{pages})')}")

		# Preparar grid en columnas con numeración global y truncado
		visible = options[start:end]
		numbers = list(range(start + 1, end + 1))

		# Primero estimo un ancho razonable de columna según el contenido bruto
		term_w = term_width()
		# Longitud del número "NNN. " promedio (tomamos la máxima de la página)
		num_prefix_lens = [len(f"{n}. ") for n in numbers] or [3]
		max_num_prefix = max(num_prefix_lens)
		# Longitud máxima de label sin número
		max_label_len_page = max((len(lbl) for lbl in visible), default=0)
		# Estima col_w base y número de columnas
		col_w_base = max(20, min(max_num_prefix + 2 + max_label_len_page, term_w))
		cols = max(1, term_w // min(col_w_base, max(20, term_w // 2)))
		cols = min(cols, 4)  # evita demasiadas columnas estrechas
		rows = (len(visible) + cols - 1) // cols

		items: List[str] = []
		for n, label in zip(numbers, visible):
			# Calcular col_w según columnas decididas
			col_w = term_w // cols
			# Prefijo numérico coloreado y su longitud visual
			num_pref_plain = f"{n}. "
			num_pref_col = f"{c(str(n)+'.', Colors.YELLOW)} "
			# Espacio restante para el label en esta columna
			max_label = max(8, col_w - len(num_pref_plain) - 2)
			label_trunc = truncate_label(label, max_label)
			item = num_pref_col + label_trunc
			items.append(item)

		# Pintar en grid con padding basado en longitud visual aproximada
		for r in range(rows):
			row_parts: List[str] = []
			for c_idx in range(cols):
				idx = r + c_idx * rows
				if idx >= len(items):
					continue
				cell = items[idx]
				col_w = term_w // cols
				plain_len = strip_ansi_len(cell)
				pad = max(0, col_w - plain_len)
				row_parts.append(cell + (' ' * pad))
			print(''.join(row_parts))
			if is_ui_comfortable():
				print()

		print()
		print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
		if pages > 1:
			print(f"  {c('n', Colors.GREEN)} Siguiente página (n)    {c('p', Colors.GREEN)} Página anterior (p)    {c('g', Colors.GREEN)} Ir a página (g)")
		print(f"  {c('s', Colors.GREEN)} Alternar orden (A↔Z) (s)    {c('/', Colors.GREEN)} Filtrar (/)")
		print(c(line(), Colors.BLUE))
		choice = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if choice == 'q':
			return 0
		if choice == 'n' and page < pages - 1:
			page += 1
			continue
		if choice == 'p' and page > 0:
			page -= 1
			continue
		if choice == 'g' and pages > 1:
			val = input(c("Ir a página #: ", Colors.CYAN)).strip()
			if val.isdigit():
				pg = int(val)
				if 1 <= pg <= pages:
					page = pg - 1
					continue
			print(c("Número de página inválido.", Colors.RED))
			continue
		if choice == 's':
			return -2
		if choice == '/':
			return -3
		if choice.isdigit():
			num = int(choice)
			if num == 0:
				return 0
			if 1 <= num <= total:
				return num
		print(c("Entrada no válida. Intenta de nuevo.", Colors.RED))


def filter_channels(channels: List[Dict]) -> List[Dict]:
	print()
	header("Filtro de canales")
	query = input(c("Texto a filtrar (enter para mostrar todo): ", Colors.CYAN)).strip().lower()
	if not query:
		return channels
	return [c_ for c_ in channels if query in (c_.get('name') or '').lower()]


def load_search_history() -> List[str]:
	"""Carga el historial de búsquedas recientes."""
	if not os.path.isfile(SEARCH_HISTORY_FILE):
		return []
	try:
		with open(SEARCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			if isinstance(data, list):
				return [str(s) for s in data if s]
	except Exception:
		pass
	return []


def save_search_history(queries: List[str]) -> None:
	"""Guarda el historial de búsquedas (máximo 20)."""
	try:
		# Mantener solo las últimas 20 búsquedas únicas
		unique_queries = []
		seen = set()
		for q in reversed(queries):
			q_lower = q.lower().strip()
			if q_lower and q_lower not in seen:
				unique_queries.insert(0, q.strip())
				seen.add(q_lower)
				if len(unique_queries) >= 20:
					break
		
		with open(SEARCH_HISTORY_FILE, 'w', encoding='utf-8') as f:
			json.dump(unique_queries, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


def add_to_search_history(query: str) -> None:
	"""Añade una búsqueda al historial."""
	if not query or not query.strip():
		return
	history = load_search_history()
	# Añadir al final (se moverá al principio si está duplicada)
	history.append(query.strip())
	save_search_history(history)


def get_search_suggestions(query: str, history: List[str], favorites: List[Dict], play_history: List[Dict]) -> List[str]:
	"""
	Genera sugerencias de búsqueda basadas en:
	- Búsquedas recientes similares
	- Nombres de canales en favoritos
	- Nombres de canales en historial de reproducción
	"""
	suggestions = []
	query_lower = query.lower().strip()
	
	if not query_lower:
		# Si la búsqueda está vacía, mostrar búsquedas recientes
		return history[:5]
	
	# Buscar en historial de búsquedas
	for h in history:
		if query_lower in h.lower() and h.lower() != query_lower:
			suggestions.append(h)
	
	# Buscar en favoritos
	for fav in favorites:
		name = fav.get('name', '')
		if name and query_lower in name.lower() and name not in suggestions:
			suggestions.append(name)
	
	# Buscar en historial de reproducción
	for entry in play_history:
		name = entry.get('name', '')
		if name and query_lower in name.lower() and name not in suggestions:
			suggestions.append(name)
	
	# Limitar a 5 sugerencias
	return suggestions[:5]


def prompt_with_suggestions(prompt_text: str, suggestions: List[str], history: List[str]) -> Optional[str]:
	"""
	Muestra un prompt con sugerencias y permite seleccionar una.
	"""
	if suggestions:
		print()
		print(c("Sugerencias:", Colors.CYAN))
		for i, sug in enumerate(suggestions, 1):
			print(f"  {c(str(i), Colors.YELLOW)}. {sug}")
		if history and len(suggestions) < 5:
			print(f"  {c('h', Colors.YELLOW)}. Ver historial de búsquedas")
		print()
	
	user_input = input(c(prompt_text, Colors.CYAN)).strip()
	
	if not user_input:
		return None
	
	# Si el usuario presiona un número, seleccionar sugerencia
	if user_input.isdigit():
		idx = int(user_input)
		if 1 <= idx <= len(suggestions):
			return suggestions[idx - 1]
	
	# Si presiona 'h', mostrar historial completo
	if user_input.lower() == 'h' and history:
		print()
		print(c("Historial de búsquedas:", Colors.CYAN))
		for i, h in enumerate(history[:10], 1):
			print(f"  {c(str(i), Colors.YELLOW)}. {h}")
		print()
		hist_choice = input(c("Selecciona una búsqueda (número) o pulsa enter para continuar: ", Colors.CYAN)).strip()
		if hist_choice.isdigit():
			hist_idx = int(hist_choice)
			if 1 <= hist_idx <= min(10, len(history)):
				return history[hist_idx - 1]
	
	return user_input


def load_favorites() -> List[Dict[str, str]]:
	if not os.path.isfile(FAVORITES_FILE):
		return []
	try:
		with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			if isinstance(data, list):
				return [d for d in data if isinstance(d, dict) and 'url' in d]
	except Exception:
		pass
	return []


def save_favorites(favs: List[Dict[str, str]]) -> None:
	try:
		with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
			json.dump(favs, f, ensure_ascii=False, indent=2)
	except Exception as e:
		print(c(f"No se pudo guardar favoritos: {e}", Colors.RED))


def add_favorite(name: str, url: str, source: Optional[str]) -> None:
	# Normalizar
	name = (name or '').strip() or (url or '').strip()
	url = (url or '').strip()
	source = (source or '').strip()
	if not url:
		print(c("URL inválida, no se puede añadir a favoritos.", Colors.RED))
		return
	favs = load_favorites()
	# Evitar duplicados por URL
	if any((f.get('url') or '').strip() == url for f in favs):
		print(c("Ya está en favoritos.", Colors.YELLOW))
		return
	favs.append({'name': name, 'url': url, 'source': source})
	save_favorites(favs)
	print(c("Añadido a favoritos.", Colors.GREEN))


def offer_add_favorite(name: str, url: str, source: Optional[str]) -> None:
	result = prompt_yes_no("¿Añadir a favoritos?", default_yes=False)
	if result is True:
		add_favorite(name, url, source)


def favorites_menu() -> None:
	while True:
		favs = load_favorites()
		if not favs:
			header("Favoritos")
			print(c("No hay favoritos.", Colors.YELLOW))
			input(c("Pulsa enter para volver... ", Colors.CYAN))
			return
		# Evitar comillas anidadas en f-strings
		def fav_label(fav: Dict[str, str]) -> str:
			name = fav.get('name') or fav.get('url') or ''
			source = fav.get('source') or ''
			badge = dim(f"[{source}]") if source else ''
			return f"{name} {badge}"
		options = [fav_label(fav) for fav in favs]
		print()
		header(f"Favoritos ({len(favs)})")
		print(f"  {c('1.', Colors.YELLOW)} {icon('EXPORT')}Exportar JSON (e)  |  {c('2.', Colors.YELLOW)} {icon('EXPORT')}Exportar M3U (m)  |  {c('3.', Colors.YELLOW)} {icon('IMPORT')}Importar (i)  |  {c('4.', Colors.YELLOW)} {icon('RANDOM')}Aleatorio (r)  |  {c('5.', Colors.YELLOW)} {icon('VALIDATE')}Validar URLs (v)  |  {c('6.', Colors.YELLOW)} {icon('FILTER')}Buscar (/)  |  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		cmd = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if cmd in ('0', 'q'):
			return
		if cmd in ('6', '/'):
			# Buscar en favoritos
			query = input(c("Buscar en favoritos (nombre/URL): ", Colors.CYAN)).strip().lower()
			if query:
				filtered_favs = [f for f in favs if query in (f.get('name') or '').lower() or query in (f.get('url') or '').lower()]
				if filtered_favs:
					favs = filtered_favs
					options = [fav_label(fav) for fav in favs]
					continue
				else:
					print(c("No se encontraron favoritos.", Colors.YELLOW))
					input(c("Pulsa enter para continuar... ", Colors.CYAN))
					continue
			else:
				# Recargar lista completa
				favs = load_favorites()
				options = [fav_label(fav) for fav in favs]
				continue
		if cmd in ('1', 'e'):
			path = input(c("Ruta destino (ej. favorites_export.json): ", Colors.CYAN)).strip()
			if not path:
				print(c("Ruta inválida.", Colors.RED))
			else:
				# Asegurar extensión .json
				if not path.lower().endswith('.json'):
					path += '.json'
				try:
					with open(path, 'w', encoding='utf-8') as f:
						json.dump(favs, f, ensure_ascii=False, indent=2)
					print(c(f"Favoritos exportados a {path}.", Colors.GREEN))
				except Exception as e:
					print(c(f"Error exportando: {e}", Colors.RED))
			input(c("Pulsa enter para continuar... ", Colors.CYAN))
			continue
		if cmd in ('2', 'm'):
			# Exportar a formato M3U
			path = input(c("Ruta destino (ej. favorites.m3u): ", Colors.CYAN)).strip()
			if not path:
				print(c("Ruta inválida.", Colors.RED))
			else:
				# Asegurar extensión .m3u
				if not path.lower().endswith('.m3u'):
					path += '.m3u'
				try:
					with open(path, 'w', encoding='utf-8') as f:
						f.write('#EXTM3U\n')
						for fav in favs:
							name = fav.get('name') or fav.get('url') or 'Unknown'
							url = fav.get('url') or ''
							source = fav.get('source') or ''
							if url:
								# Formato: #EXTINF:-1 group-title="source",name
								if source:
									f.write(f'#EXTINF:-1 group-title="{source}",{name}\n')
								else:
									f.write(f'#EXTINF:-1,{name}\n')
								f.write(f'{url}\n')
					print(c(f"Favoritos exportados a formato M3U: {path}", Colors.GREEN))
					print(c(f"  - {len(favs)} emisoras exportadas", Colors.DIM))
				except Exception as e:
					print(c(f"Error exportando: {e}", Colors.RED))
			input(c("Pulsa enter para continuar... ", Colors.CYAN))
			continue
		if cmd in ('5', 'v'):
			# Validar URLs de favoritos
			if not favs:
				print(c("No hay favoritos para validar.", Colors.YELLOW))
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
				continue
			header("Validando URLs de favoritos")
			print(c(f"Validando {len(favs)} favoritos...", Colors.CYAN))
			validated = []
			invalid = []
			for i, fav in enumerate(favs, 1):
				name = fav.get('name') or fav.get('url') or ''
				url = fav.get('url') or ''
				print(c(f"[{i}/{len(favs)}] {name[:50]}...", Colors.DIM), end=' ', flush=True)
				if validate_url(url, timeout=5):
					print(c("✓", Colors.GREEN))
					validated.append(fav)
				else:
					print(c("✗", Colors.RED))
					invalid.append(fav)
			
			print()
			print(c(f"Resultados: {len(validated)} válidas, {len(invalid)} inválidas", Colors.CYAN))
			if invalid:
				print()
				print(c("Favoritos con URLs inválidas:", Colors.YELLOW))
				for fav in invalid:
					print(f"  - {fav.get('name') or fav.get('url')}")
				result = prompt_yes_no("¿Eliminar favoritos con URLs inválidas?", default_yes=False)
				if result is True:
					favs = validated
					save_favorites(favs)
					print(c(f"{len(invalid)} favoritos eliminados.", Colors.GREEN))
			input(c("Pulsa enter para continuar... ", Colors.CYAN))
			# Recargar lista actualizada
			favs = load_favorites()
			options = [fav_label(fav) for fav in favs]
			continue
		if cmd in ('3', 'i'):
			src = input(c("Ruta origen (archivo JSON de favoritos): ", Colors.CYAN)).strip()
			try:
				with open(src, 'r', encoding='utf-8') as f:
					data = json.load(f)
				if isinstance(data, list):
					save_favorites(data)
					print(c("Favoritos importados.", Colors.GREEN))
				else:
					print(c("Formato inválido.", Colors.RED))
			except Exception as e:
				print(c(f"Error importando: {e}", Colors.RED))
			continue
		if cmd in ('4', 'r'):
			attempts = 0
			while True:
				fav = random.choice(favs)
				name = fav.get('name') or fav.get('url') or ''
				print(f"{c('Reproduciendo (aleatorio favoritos):', Colors.GREEN)} {name}")
				try:
					code = play_with_config(
						fav.get('url') or '',
						name,
						play_mode="Aleatorio (favoritos)",
						source=fav.get('source'),
					)
				except MpvNotFoundError as e:
					print(str(e))
					break
				if code != 0:
					attempts += 1
					if attempts <= 3:
						print(c("Fallo, probando otro favorito...", Colors.YELLOW))
						continue
					else:
						print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
						break
				# Solo añadir al historial si la reproducción fue exitosa
				append_history(name, fav.get('url') or '', 'favoritos')
				result = prompt_yes_no("¿Reproducir otro favorito aleatorio?", default_yes=True)
				if result is None or not result:
					break
			continue
		idx = paginated_select(options, "Favoritos")
		if idx == 0 or idx == -1:
			return
		fav = favs[idx - 1]
		# Submenú del favorito
		while True:
			header(f"Favorito: {fav.get('name')}")
			print(f"  {c('1.', Colors.YELLOW)} {icon('PLAY')}Reproducir")
			print(f"  {c('2.', Colors.YELLOW)} {icon('EDIT')}Editar")
			print(f"  {c('3.', Colors.YELLOW)} {icon('TRASH')}Eliminar")
			print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
			print(c(line(), Colors.BLUE))
			opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
			if opt in ('0', 'q'):
				break
			elif opt == '1':
				try:
					play_with_config(
						fav.get('url') or '',
						fav.get('name'),
						play_mode="Favoritos",
						source=fav.get('source'),
					)
				except MpvNotFoundError as e:
					print(str(e))
			elif opt == '2':
				# Editar favorito
				print()
				header("Editar favorito")
				current_name = fav.get('name') or ''
				current_url = fav.get('url') or ''
				print(c(f"Nombre actual: {current_name}", Colors.DIM))
				new_name = input(c("Nuevo nombre (enter para mantener): ", Colors.CYAN)).strip()
				print(c(f"URL actual: {current_url}", Colors.DIM))
				new_url = input(c("Nueva URL (enter para mantener): ", Colors.CYAN)).strip()
				
				updated = False
				if new_name:
					fav['name'] = new_name
					updated = True
				if new_url:
					# Validar que no exista otra URL igual
					if any((f.get('url') or '').strip() == new_url.strip() and (f.get('url') or '').strip() != current_url for f in favs):
						print(c("Ya existe otro favorito con esa URL.", Colors.RED))
						input(c("Pulsa enter para continuar... ", Colors.CYAN))
						continue
					fav['url'] = new_url
					updated = True
				
				if updated:
					# Actualizar en la lista
					for i, f in enumerate(favs):
						if (f.get('url') or '').strip() == current_url:
							favs[i] = fav
							break
					save_favorites(favs)
					fav = fav  # Actualizar referencia local
					print(c("Favorito actualizado.", Colors.GREEN))
				else:
					print(c("No se realizaron cambios.", Colors.YELLOW))
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
			elif opt == '3':
				# Eliminar favorito
				result = prompt_yes_no("¿Eliminar este favorito?", default_yes=False)
				if result is True:
					favs = [x for x in favs if (x.get('url') or '').strip() != (fav.get('url') or '').strip()]
					save_favorites(favs)
					print(c("Eliminado de favoritos.", Colors.GREEN))
					break
				elif result is None:
					break  # Cancelar con 'q'
			else:
				print(c("Opción no válida.", Colors.RED))


def global_search(playlists: List[str]) -> None:
	header("Búsqueda global en playlists")
	
	# Cargar historial de búsquedas y sugerencias
	search_history = load_search_history()
	favorites = load_favorites()
	play_history = load_history()
	
	# Mostrar búsquedas recientes si existen
	if search_history:
		print(c("Búsquedas recientes:", Colors.CYAN))
		for i, h in enumerate(search_history[:5], 1):
			print(f"  {c(str(i), Colors.YELLOW)}. {h}")
		print()
	
	# Obtener sugerencias basadas en búsqueda vacía (mostrará recientes)
	suggestions = get_search_suggestions("", search_history, favorites, play_history)
	query = prompt_with_suggestions("Texto a buscar (en nombre/url) o número de sugerencia: ", suggestions, search_history)
	
	if not query:
		print(c("Búsqueda vacía.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Validar longitud mínima de búsqueda
	min_length = CONFIG.get('min_search_length', MIN_SEARCH_LENGTH)
	try:
		min_length = int(min_length)
	except Exception:
		min_length = MIN_SEARCH_LENGTH
	
	if len(query) < min_length:
		print(c(f"⚠ Búsqueda muy corta ({len(query)} caracteres).", Colors.YELLOW))
		print(c(f"Se recomienda al menos {min_length} caracteres para evitar resultados excesivos.", Colors.YELLOW))
		if len(query) == 1:
			# Si es una sola letra, no permitir directamente
			result = prompt_yes_no(f"¿Realmente quieres buscar con solo '{query}'? (puede tardar mucho)", default_yes=False)
			if result is None or not result:
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				return
		elif len(query) == 2:
			# Si son 2 letras, advertir
			result = prompt_yes_no(f"¿Continuar con la búsqueda '{query}'? (puede generar muchos resultados)", default_yes=False)
			if result is None or not result:
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				return
	
	# Añadir a historial de búsquedas
	add_to_search_history(query)
	
	query = query.lower()
	print(c(f"Buscando '{query}'...", Colors.CYAN))
	results: List[Dict] = []
	for pl in playlists:
		path = os.path.join(PLAYLISTS_DIR, pl)
		try:
			channels = parse_m3u_file(path)
		except Exception:
			continue
		for ch in channels:
			name = (ch.get('name') or '')
			url = (ch.get('url') or '')
			if query in name.lower() or query in url.lower():
				results.append({'name': name or url, 'url': url, 'source': pl})
	if not results:
		print(c("Sin resultados.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	# Interacción con resultados
	while True:
		# Evitar comillas anidadas
		labels = []
		for r in results:
			badge = dim(f"[{r['source']}]")
			labels.append(f"{r['name']} {badge}")
		print()
		header(f"Resultados ({len(results)})")
		print(f"  {c('1.', Colors.YELLOW)} Aleatorio entre resultados (r)  |  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		sel = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if sel in ('0', 'q'):
			return
		if sel in ('1', 'r'):
			# Bucle aleatorio sobre resultados + oferta favoritos
			attempts = 0
			while True:
				item = random.choice(results)
				print(f"{c('Reproduciendo (aleatorio):', Colors.GREEN)} {item['name']} {dim(f'[{item['source']}]')}")
				try:
					code = play_with_config(
						item['url'],
						item.get('name'),
						play_mode="Aleatorio (repo)",
						source=item.get('source'),
					)
				except MpvNotFoundError as e:
					print(str(e))
					return
				if code != 0:
					attempts += 1
					if attempts <= 3:
						print(c("Fallo, probando otra emisora...", Colors.YELLOW))
						continue
					else:
						print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
						return
				# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
				append_history(item['name'], item['url'], item['source'])
				offer_add_favorite(item['name'], item['url'], item['source'])
				result = prompt_yes_no("¿Reproducir otra emisora aleatoria de los resultados?", default_yes=True)
				if result is None or not result:
					return
			continue
		# Selección paginada
		idx = paginated_select(labels, "Resultados de búsqueda")
		if idx == 0 or idx == -1:
			return
		item = results[idx - 1]
		print(f"{c('Reproduciendo:', Colors.GREEN)} {item['name']} {dim(f'[{item['source']}]')}")
		try:
			play_with_config(
				item['url'],
				item.get('name'),
				play_mode="Búsqueda repositorio",
				source=item.get('source'),
			)
		except MpvNotFoundError as e:
			print(str(e))
		append_history(item['name'], item['url'], item['source'])
		# Ofrecer añadir a favoritos tras reproducir
		offer_add_favorite(item['name'], item['url'], item['source'])


def toggle_favorite_by_index(channels: List[Dict], idx: int, source: Optional[str]) -> None:
	if idx < 0 or idx >= len(channels):
		print(c("Índice fuera de rango.", Colors.RED))
		return
	ch = channels[idx]
	url = ch.get('url') or ''
	name = ch.get('name') or url
	favs = load_favorites()
	if any((f.get('url') or '') == url for f in favs):
		# eliminar
		favs = [f for f in favs if (f.get('url') or '') != url]
		save_favorites(favs)
		print(c("Eliminado de favoritos.", Colors.GREEN))
	else:
		add_favorite(name, url, source)


def select_and_play(channels: List[Dict], source: Optional[str] = None) -> None:
	global SORT_CHANNELS_ASC, CONFIG
	# Ordenar canales según configuración
	def sort_key(ch: Dict) -> str:
		name = (ch.get('name') or ch.get('url') or '').lower()
		return name
	channels = sorted(channels, key=sort_key, reverse=not SORT_CHANNELS_ASC)
	current_filter = ''
	while True:
		filtered = channels
		if current_filter:
			filtered = [c_ for c_ in channels if current_filter in (c_.get('name') or '').lower()]
		filtered = sorted(filtered, key=lambda ch: (ch.get('name') or ch.get('url') or '').lower(), reverse=not SORT_CHANNELS_ASC)
		filtered = filter_not_blacklisted(filtered)
		if not filtered:
			print(c("No hay canales para mostrar.", Colors.RED))
			return

		options = [c_.get('name') or c_.get('url') for c_ in filtered]
		print()
		header(f"Selección de canales ({len(filtered)} disponibles)")
		print(f"  {c('1.', Colors.YELLOW)} Aleatorio entre resultados (r)  |  {c('2.', Colors.YELLOW)} Favorito por número (f)  |  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		selection = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if selection in ('0', 'q'):
			return
		if selection in ('1', 'r'):
			attempts = 0
			while True:
				if not filtered:
					print(c("No hay resultados para aleatorio.", Colors.RED))
					return
				channel = random.choice(filtered)
				url = channel.get('url')
				name = channel.get('name') or url
				print(f"{c('Reproduciendo (aleatorio):', Colors.GREEN)} {name}")
				try:
					code = play_with_config(url, name, play_mode="Aleatorio", source=source)
				except MpvNotFoundError as e:
					print(str(e))
					return
				if code != 0:
					attempts += 1
					if attempts <= 3:
						print(c("Fallo, probando otro canal...", Colors.YELLOW))
						continue
					else:
						print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
						return
				# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
				append_history(name, url, source)
				offer_add_favorite(name, url, source)
				result = prompt_yes_no("¿Reproducir otra emisora aleatoria de los resultados?", default_yes=True)
				if result is None or not result:
					return
			continue
		elif selection == 'f':
			val = input(c("Número de elemento a (des)favorito: ", Colors.CYAN)).strip()
			if val.isdigit():
				index = int(val) - 1
				if 0 <= index < len(filtered):
					# Mapear al índice real en channels
					real_idx = channels.index(filtered[index])
					toggle_favorite_by_index(channels, real_idx, source)
				else:
					print(c("Índice inválido.", Colors.RED))
			else:
				print(c("Entrada no válida.", Colors.RED))
			continue

		while True:
			idx1 = paginated_select(options, "Canales disponibles")
			if idx1 == -2:
				SORT_CHANNELS_ASC = not SORT_CHANNELS_ASC
				CONFIG['sort_channels'] = 'asc' if SORT_CHANNELS_ASC else 'desc'
				save_config()
				filtered = sorted(filtered, key=lambda ch: (ch.get('name') or ch.get('url') or '').lower(), reverse=not SORT_CHANNELS_ASC)
				options = [c_.get('name') or c_.get('url') for c_ in filtered]
				continue
			if idx1 == -3:
				current_filter = input(c("Texto a filtrar: ", Colors.CYAN)).strip().lower()
				break
			break
		if idx1 == 0:
			return
		if idx1 == -1:
			print(c("No hay opciones disponibles.", Colors.RED))
			return
		channel = filtered[idx1 - 1]
		url = channel.get('url')
		name = channel.get('name') or url
		
		# Mostrar previsualización si está habilitada
		show_preview = CONFIG.get('show_channel_preview', True)
		if show_preview:
			show_channel_preview(channel, source)
			result = prompt_yes_no("¿Reproducir este canal?", default_yes=True)
			if result is None or not result:
				continue
		
		print(f"{c('Reproduciendo:', Colors.GREEN)} {name}")
		start_time = time.time()
		try:
			code = play_with_config(url, name, source=source)
		except MpvNotFoundError as e:
			print(str(e))
			return
		# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
		if code == 0:
			duration = time.time() - start_time
			attrs = channel.get('attrs', {})
			append_history(name, url, source, duration=duration, attrs=attrs)
		offer_add_favorite(name, url, source)


def random_channel_from_all(playlists: List[str]) -> None:
	if not playlists:
		print(c("No hay playlists disponibles.", Colors.RED))
		return
	# Bucle de aleatorio global con blacklist y auto-skip
	while True:
		pl = random.choice(playlists)
		path = os.path.join(PLAYLISTS_DIR, pl)
		try:
			channels = parse_m3u_file(path)
		except Exception as e:
			print(f"{c('Error leyendo la playlist:', Colors.RED)} {e}")
			return
		channels = filter_not_blacklisted(channels)
		if not channels:
			print(c("No hay canales disponibles en aleatorio global.", Colors.RED))
			return
		channel = random.choice(channels)
		name = channel.get('name') or channel.get('url')
		print(f"{c('Reproduciendo aleatorio global:', Colors.GREEN)} [{pl}] {name}")
		try:
			code = play_with_config(
				channel.get('url'),
				name,
				play_mode="Aleatorio (global)",
				source=pl,
			)
		except MpvNotFoundError as e:
			print(str(e))
			return
		if code != 0:
			print(c("Fallo, probando otra emisora...", Colors.YELLOW))
			continue
		# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
		append_history(name, channel.get('url'), pl)
		offer_add_favorite(name, channel.get('url'), pl)
		result = prompt_yes_no("¿Reproducir otra emisora aleatoria global?", default_yes=True)
		if result is None or not result:
			break

# Logo ASCII para menú y OSD de reproducción
OSD_LOGO_LINES = [
	"                       ______            ___       ______  __   ",
	r"  _________ ___  ____/ / __ \____ _____/ (_)___  / __ \ \/ /   ",
	r" / ___/ __ `__ \/ __  / /_/ / __ `/ __  / / __ \/ /_/ /\  /    ",
	"/ /__/ / / / / / /_/ / _, _/ /_/ / /_/ / / /_/ / ____/ / /     ",
	r"\___/_/ /_/ /_/\__,_/_/ |_|\__,_/\__,_/_/\____/_/     /_/      ",
]

def print_ascii_logo() -> None:
	# Logo ASCII art centrado
	w = term_width()
	max_logo_width = max(len(line) for line in OSD_LOGO_LINES)
	pad_left = max(0, (w - max_logo_width) // 2)
	for line in OSD_LOGO_LINES:
		print(" " * pad_left + c(line, Colors.CYAN))
	print()


def _format_time_hms(seconds: float) -> str:
	"""Formatea segundos como HH:MM:SS o MM:SS para la OSD."""
	if seconds < 0 or not isinstance(seconds, (int, float)):
		return "00:00"
	secs = int(seconds)
	mins, s = divmod(secs, 60)
	h, m = divmod(mins, 60)
	if h > 0:
		return f"{h:02d}:{m:02d}:{s:02d}"
	return f"{m:02d}:{s:02d}"


# Número de líneas que ocupa la OSD (logo 5 + blank + progreso + separador + modo + emisora + ahora suena + pausa + botones + espacios)
OSD_LINE_COUNT = 19

# Último estado mostrado en OSD (para no redibujar si no cambió)
_osd_last_state: Optional[dict] = None
_osd_cursor_hidden = False


def _osd_hide_cursor() -> None:
	"""Oculta el cursor del terminal durante la OSD propia."""
	global _osd_cursor_hidden
	if _osd_cursor_hidden:
		return
	try:
		sys.stdout.write("\033[?25l")
		sys.stdout.flush()
		_osd_cursor_hidden = True
	except Exception:
		pass


def _osd_show_cursor() -> None:
	"""Restaura el cursor del terminal al salir de la OSD propia."""
	global _osd_cursor_hidden
	if not _osd_cursor_hidden:
		return
	try:
		sys.stdout.write("\033[?25h")
		sys.stdout.flush()
	except Exception:
		pass
	_osd_cursor_hidden = False


def _osd_reset_state() -> None:
	"""Resetea el estado de OSD para la siguiente reproducción."""
	global _osd_last_state
	_osd_last_state = None


def _is_favorite(channel_url: str) -> bool:
	"""Verifica si una URL está en favoritos."""
	if not channel_url:
		return False
	favs = load_favorites()
	return any((f.get('url') or '').strip() == channel_url.strip() for f in favs)


def _toggle_favorite(channel_url: str, station_name: Optional[str]) -> bool:
	"""Toggle favorito para una URL. Retorna True si ahora está en favoritos."""
	if not channel_url:
		return False
	favs = load_favorites()
	if any((f.get('url') or '').strip() == channel_url.strip() for f in favs):
		# Eliminar
		favs = [f for f in favs if (f.get('url') or '').strip() != channel_url.strip()]
		save_favorites(favs)
		return False
	else:
		# Añadir
		add_favorite(station_name or 'Radio', channel_url, None)
		return True


def _osd_display_state(state: dict) -> dict:
	"""Estado reducido para comparación: evita parpadeo redibujando solo cuando cambia."""
	return {
		"play_mode": (state.get("play_mode") or "").strip(),
		"station_name": (state.get("station_name") or "").strip(),
		"media_title": (state.get("media_title") or "").strip(),
		"channel_url": (state.get("channel_url") or "").strip(),
		"source": (state.get("source") or "").strip(),
		"pause": bool(state.get("pause")),
		"mute": bool(state.get("mute")),
		"volume": state.get("volume") or 0,
		"duration": state.get("duration"),
		"time_pos_sec": int(state.get("time_pos") or 0),
		"audio_codec": state.get("audio_codec"),
		"audio_bitrate_kbps": state.get("audio_bitrate_kbps"),
		"samplerate_hz": state.get("samplerate_hz"),
	}


def draw_custom_osd(state: dict, first_time: bool, key: Optional[str] = None) -> None:
	"""
	Dibuja la OSD propia: logo ASCII, barra de progreso, emisora/título y botones.
	state: volume, mute, pause, media_title, time_pos, duration, station_name, play_mode, channel_url, source.
	key: tecla especial (ej. 'f' para toggle favorito).
	"""
	import sys
	global _osd_last_state
	
	# Si se presionó 'f', toggle favorito
	if key == "f" and state.get("channel_url"):
		try:
			_toggle_favorite(state.get("channel_url"), state.get("station_name"))
		except Exception:
			pass
	
	display = _osd_display_state(state)
	skipped = not first_time and _osd_last_state is not None and display == _osd_last_state
	if skipped:
		return
	_osd_last_state = display

	if first_time:
		sys.stdout.write("\033[2J\033[H")
		sys.stdout.flush()

	w = term_width()
	pad_logo = 0

	# Líneas a imprimir (sin ANSI de color en el conteo para cursor up)
	lines_out: List[str] = []
	for line in OSD_LOGO_LINES:
		lines_out.append(" " * pad_logo + c(line, Colors.CYAN))
	lines_out.append("")

	# Barra de progreso y tiempo
	time_pos = state.get("time_pos") or 0.0
	duration = state.get("duration")
	if duration is not None and duration > 0:
		total = int(duration)
		pos = int(time_pos)
		bar = draw_osd_progress_bar(pos, total, width=min(40, w - 25))
		time_str = f"  {_format_time_hms(time_pos)} / {_format_time_hms(duration)}"
		lines_out.append(c(bar + time_str, Colors.BLUE))
	else:
		# En directo: tiempo transcurrido + barra indeterminada
		elapsed = _format_time_hms(time_pos)
		indet = "─" * (min(20, w // 3)) + "  En directo"
		lines_out.append(c(f"  {elapsed}  ", Colors.DIM) + c(indet, Colors.BLUE))

	lines_out.append(c("─" * w, Colors.DIM))
	lines_out.append("")

	# Modo de reproducción
	mode = (state.get("play_mode") or "").strip() or "Normal"
	mode_line = "  Modo: " + mode
	lines_out.append(c(mode_line[:w], Colors.GREEN))
	lines_out.append("")

	# Emisora (solo nombre) + indicador de favorito
	station = (state.get("station_name") or "").strip()
	channel_url = state.get("channel_url") or ""
	source = (state.get("source") or "").strip()
	is_fav = _is_favorite(channel_url) if channel_url else False
	fav_icon = "⭐" if is_fav else "☆"
	station_line = f"  {fav_icon} " + (station or "Reproduciendo")
	lines_out.append(c(station_line[:w], Colors.WHITE))
	source_line = ""
	if source and source.lower().endswith((".m3u", ".m3u8")):
		source_line = f"  M3U: {source}"
	lines_out.append(c(source_line[:w], Colors.DIM) if source_line else "")
	lines_out.append("")

	# Ahora suena: título de la pista (media-title o metadata/icy-title en radio)
	title = (state.get("media_title") or "").strip()
	now_line = "  Ahora suena: " + (title[:w - 18] if title else "—")
	lines_out.append(c(now_line[:w], Colors.MAGENTA))
	lines_out.append("")

	# Estado pausa: [ PAUSADO ] o línea en blanco
	vol = state.get("volume") or 0
	mute = state.get("mute") or False
	pause = state.get("pause") or False
	pause_line = "  [ PAUSADO ]" if pause else "  "
	lines_out.append(c(pause_line[:w], Colors.GREEN if pause else Colors.DIM))
	lines_out.append("")

	# Botones y estado (iconos ▶/⏸, 🔇/🔈)
	play_icon = getattr(Icon, "PAUSE", "⏸") if pause else getattr(Icon, "PLAY", "▶")
	mute_icon = "🔇" if mute else "🔈"
	p_btn = c(f"{play_icon} Pausa", Colors.GREEN if pause else Colors.WHITE)
	m_btn = c(f"{mute_icon} Mute", Colors.GREEN if mute else Colors.WHITE)
	q_btn = c("[Q] Salir", Colors.MAGENTA)
	btns = f"  {p_btn}  [+] Vol+  [-] Vol-  {m_btn}  Vol:{vol}  [F] Fav  {q_btn}"
	lines_out.append(c(btns[:w], Colors.YELLOW))

	if not first_time:
		sys.stdout.write("\033[%dA" % OSD_LINE_COUNT)  # Cursor up
	for line in lines_out:
		sys.stdout.write(line + "\033[K\n")
	sys.stdout.flush()

# --- Exportar/Importar configuración completa ---

def export_config_complete() -> None:
	"""Exporta configuración, favoritos e historial a un archivo JSON."""
	header("Exportar configuración completa")
	
	# Recolectar datos
	config_data = CONFIG.copy()
	favorites_data = load_favorites()
	history_data = load_history()
	
	export_data = {
		'version': '1.0',
		'export_date': time.strftime('%Y-%m-%d %H:%M:%S'),
		'config': config_data,
		'favorites': favorites_data,
		'history': history_data,
	}
	
	path = input(c("Ruta destino (ej. cmdRadioPy_backup.json): ", Colors.CYAN)).strip()
	if not path:
		print(c("Ruta inválida.", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Asegurar extensión .json
	if not path.lower().endswith('.json'):
		path += '.json'
	
	try:
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(export_data, f, ensure_ascii=False, indent=2)
		print(c(f"Configuración exportada correctamente a: {path}", Colors.GREEN))
		print(c(f"  - Configuración: {len(config_data)} opciones", Colors.DIM))
		print(c(f"  - Favoritos: {len(favorites_data)} emisoras", Colors.DIM))
		print(c(f"  - Historial: {len(history_data)} entradas", Colors.DIM))
	except Exception as e:
		print(c(f"Error al exportar: {e}", Colors.RED))
	
	input(c("Pulsa enter para volver... ", Colors.CYAN))


def import_config_complete() -> None:
	"""Importa configuración, favoritos e historial desde un archivo JSON."""
	global CONFIG, CURRENT_PAGE_SIZE, SORT_PLAYLISTS_ASC, SORT_CHANNELS_ASC
	
	header("Importar configuración completa")
	path = input(c("Ruta origen (archivo JSON de exportación): ", Colors.CYAN)).strip()
	if not path:
		print(c("Ruta inválida.", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	if not os.path.isfile(path):
		print(c("El archivo no existe.", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	try:
		with open(path, 'r', encoding='utf-8') as f:
			data = json.load(f)
	except json.JSONDecodeError:
		print(c("Error: el archivo no es un JSON válido.", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	except Exception as e:
		print(c(f"Error al importar: {e}", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	if not isinstance(data, dict):
		print(c("Formato de archivo inválido.", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Confirmar antes de sobrescribir
	print()
	config_count = len(data.get('config', {})) if isinstance(data.get('config'), dict) else 0
	fav_count = len(data.get('favorites', [])) if isinstance(data.get('favorites'), list) else 0
	hist_count = len(data.get('history', [])) if isinstance(data.get('history'), list) else 0
	
	print(c("Datos a importar:", Colors.CYAN))
	print(c(f"  - Configuración: {config_count} opciones", Colors.DIM))
	print(c(f"  - Favoritos: {fav_count} emisoras", Colors.DIM))
	print(c(f"  - Historial: {hist_count} entradas", Colors.DIM))
	
	if 'export_date' in data:
		print(c(f"  - Fecha de exportación: {data.get('export_date')}", Colors.DIM))
	
	print()
	result = prompt_yes_no("¿Importar y sobrescribir configuración actual?", default_yes=False)
	if result is None or not result:
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Preguntar qué importar
	print()
	import_config = prompt_yes_no("¿Importar configuración?", default_yes=True)
	if import_config is None:
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	import_favorites = prompt_yes_no("¿Importar favoritos?", default_yes=True)
	if import_favorites is None:
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	import_history = prompt_yes_no("¿Importar historial?", default_yes=True)
	if import_history is None:
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	imported = []
	
	# Importar configuración
	if import_config and isinstance(data.get('config'), dict):
		CONFIG.update(data['config'])
		save_config()
		# Aplicar cambios inmediatos
		try:
			ps = int(CONFIG.get('page_size') or 20)
			if 5 <= ps <= 100:
				CURRENT_PAGE_SIZE = ps
		except Exception:
			pass
		sort_pl = (CONFIG.get('sort_playlists') or 'asc').lower()
		SORT_PLAYLISTS_ASC = (sort_pl != 'desc')
		sort_ch = (CONFIG.get('sort_channels') or 'asc').lower()
		SORT_CHANNELS_ASC = (sort_ch != 'desc')
		imported.append("configuración")
	
	# Importar favoritos
	if import_favorites and isinstance(data.get('favorites'), list):
		save_favorites(data['favorites'])
		imported.append("favoritos")
	
	# Importar historial
	if import_history and isinstance(data.get('history'), list):
		save_history(data['history'])
		imported.append("historial")
	
	if imported:
		print(c(f"Importación exitosa: {', '.join(imported)}", Colors.GREEN))
	else:
		print(c("No se importó nada.", Colors.YELLOW))
	
	input(c("Pulsa enter para volver... ", Colors.CYAN))


# --- Menú de configuración ---

def config_menu() -> None:
	global CURRENT_PAGE_SIZE, SORT_PLAYLISTS_ASC, SORT_CHANNELS_ASC, CONFIG
	CONFIG = load_config()
	while True:
		header("Configuración")
		print(f"  {c('1.', Colors.YELLOW)} Tamaño de página actual: {CURRENT_PAGE_SIZE}")
		print(f"  {c('2.', Colors.YELLOW)} Orden playlists: {'A→Z' if SORT_PLAYLISTS_ASC else 'Z→A'}")
		print(f"  {c('3.', Colors.YELLOW)} Orden canales: {'A→Z' if SORT_CHANNELS_ASC else 'Z→A'}")
		print(f"  {c('4.', Colors.YELLOW)} User-Agent: {CONFIG.get('user_agent') or dim('(sin definir)')}")
		print(f"  {c('5.', Colors.YELLOW)} Proxy HTTP: {CONFIG.get('proxy') or dim('(sin definir)')}")
		print(f"  {c('6.', Colors.YELLOW)} Reintentos: {CONFIG.get('retries') or 0} | Espera: {CONFIG.get('retry_delay_sec') or 2}s")
		print(f"  {c('7.', Colors.YELLOW)} Densidad UI: {'cómodo' if is_ui_comfortable() else 'compacto'}")
		print(f"  {c('8.', Colors.YELLOW)} Volumen por defecto mpv: {CONFIG.get('volume') or 40}")
		print(f"  {c('9.', Colors.YELLOW)} Tiempo de apagado (minutos): {CONFIG.get('shutdown_minutes') or 0}")
		validate_enabled = CONFIG.get('validate_urls') or False
		validate_status = 'activada' if validate_enabled else 'desactivada'
		icons_status = 'activados' if icons_enabled() else 'desactivados'
		print(f"  {c('10.', Colors.YELLOW)} {icon('VALIDATE')}Validar URLs antes de reproducir: {validate_status} (v)")
		timeout_val = CONFIG.get('url_validation_timeout') or 5
		if validate_enabled:
			print(f"     Timeout de validación: {timeout_val}s")
		print(f"  {c('11.', Colors.YELLOW)} {icon('MUSIC')}Iconos en interfaz: {icons_status} (i)")
		min_search_len = CONFIG.get('min_search_length', MIN_SEARCH_LENGTH)
		print(f"  {c('12.', Colors.YELLOW)} {icon('FILTER')}Longitud mínima de búsqueda: {min_search_len} caracteres")
		cleanup_mode = CONFIG.get('history_cleanup_mode', 'none')
		cleanup_status = 'desactivada'
		if cleanup_mode == 'days':
			days = CONFIG.get('history_cleanup_days', 30)
			cleanup_status = f"por días ({days} días)"
		elif cleanup_mode == 'count':
			max_entries = CONFIG.get('history_cleanup_max_entries', 200)
			cleanup_status = f"por cantidad ({max_entries} entradas)"
		print(f"  {c('13.', Colors.YELLOW)} {icon('HISTORY')}Limpieza automática del historial: {cleanup_status} (h)")
		auto_discover_enabled = CONFIG.get('auto_discover_categories', False)
		auto_discover_status = 'activada' if auto_discover_enabled else 'desactivada'
		available_cats_count = len(get_available_categories())
		print(f"  {c('14.', Colors.YELLOW)} {icon('ONLINE')}Detección automática de categorías: {auto_discover_status} ({available_cats_count} categorías disponibles) (a)")
		custom_osd_status = 'activada' if CONFIG.get('use_custom_osd') else 'desactivada'
		print(f"  {c('15.', Colors.YELLOW)} OSD propia (logo, barra, botones en terminal): {custom_osd_status} (o)")
		print(f"  {c('16.', Colors.YELLOW)} {icon('EXPORT')}Exportar configuración completa (e)")
		print(f"  {c('17.', Colors.YELLOW)} {icon('IMPORT')}Importar configuración completa (x)")
		print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if opt in ('0', 'q'):
			return
		elif opt == '1':
			val = input(c("Nuevo tamaño de página (5-100): ", Colors.CYAN)).strip()
			if val.isdigit():
				n = int(val)
				if 5 <= n <= 100:
					CURRENT_PAGE_SIZE = n
					CONFIG['page_size'] = n
					save_config()
					print(c("Tamaño de página actualizado.", Colors.GREEN))
				else:
					print(c("Valor fuera de rango.", Colors.RED))
			else:
				print(c("Entrada no válida.", Colors.RED))
		elif opt == '2':
			SORT_PLAYLISTS_ASC = not SORT_PLAYLISTS_ASC
			CONFIG['sort_playlists'] = 'asc' if SORT_PLAYLISTS_ASC else 'desc'
			save_config()
			print(c("Orden de playlists actualizado.", Colors.GREEN))
		elif opt == '3':
			SORT_CHANNELS_ASC = not SORT_CHANNELS_ASC
			CONFIG['sort_channels'] = 'asc' if SORT_CHANNELS_ASC else 'desc'
			save_config()
			print(c("Orden de canales actualizado.", Colors.GREEN))
		elif opt == '4':
			ua = input(c("Nuevo User-Agent (vacío para limpiar): ", Colors.CYAN)).strip()
			CONFIG['user_agent'] = ua or None
			save_config()
		elif opt == '5':
			proxy = input(c("Proxy HTTP (p.ej. http://127.0.0.1:8080) vacío para limpiar: ", Colors.CYAN)).strip()
			CONFIG['proxy'] = proxy or None
			save_config()
		elif opt == '6':
			retries = input(c("Reintentos (0-5): ", Colors.CYAN)).strip()
			delay = input(c("Espera entre reintentos (segundos, 0-10): ", Colors.CYAN)).strip()
			try:
				CONFIG['retries'] = max(0, min(5, int(retries))) if retries.isdigit() else 0
			except Exception:
				CONFIG['retries'] = 0
			try:
				d = int(delay) if delay.isdigit() else 2
				CONFIG['retry_delay_sec'] = max(0, min(10, d))
			except Exception:
				CONFIG['retry_delay_sec'] = 2
			save_config()
		elif opt == '7':
			CONFIG['ui_spacing'] = 'compact' if is_ui_comfortable() else 'comfortable'
			save_config()
		elif opt == '8':
			val = input(c("Volumen por defecto (0-130): ", Colors.CYAN)).strip()
			if val.isdigit():
				v = max(0, min(130, int(val)))
				CONFIG['volume'] = v
				save_config()
				print(c("Volumen por defecto actualizado.", Colors.GREEN))
			else:
				print(c("Entrada no válida.", Colors.RED))
		elif opt == '9':
			val = input(c("Tiempo de apagado (minutos, 0 para desactivar): ", Colors.CYAN)).strip()
			if val.isdigit():
				mins = max(0, int(val))
				CONFIG['shutdown_minutes'] = mins
				save_config()
				print(c("Tiempo de apagado actualizado.", Colors.GREEN))
			else:
				print(c("Entrada no válida.", Colors.RED))
		elif opt == 'v':
			# Toggle validación de URLs
			current = CONFIG.get('validate_urls') or False
			CONFIG['validate_urls'] = not current
			save_config()
			status = 'activada' if CONFIG['validate_urls'] else 'desactivada'
			print(c(f"Validación de URLs {status}.", Colors.GREEN))
			if CONFIG['validate_urls']:
				# Preguntar por timeout si se activa
				timeout_val = input(c("Timeout de validación en segundos (1-30, default 5): ", Colors.CYAN)).strip()
				if timeout_val:
					try:
						timeout_int = max(1, min(30, int(timeout_val)))
						CONFIG['url_validation_timeout'] = timeout_int
						save_config()
						print(c(f"Timeout configurado a {timeout_int}s.", Colors.GREEN))
					except Exception:
						print(c("Timeout inválido, usando valor por defecto (5s).", Colors.YELLOW))
						CONFIG['url_validation_timeout'] = 5
						save_config()
				else:
					CONFIG['url_validation_timeout'] = 5
					save_config()
		elif opt == 'i':
			# Toggle iconos
			current = icons_enabled()
			CONFIG['show_icons'] = not current
			save_config()
			status = 'activados' if CONFIG['show_icons'] else 'desactivados'
			print(c(f"Iconos {status}.", Colors.GREEN))
		elif opt == '12':
			# Configurar longitud mínima de búsqueda
			current_min = CONFIG.get('min_search_length', MIN_SEARCH_LENGTH)
			print(c(f"Longitud mínima actual: {current_min} caracteres", Colors.CYAN))
			print(c("Recomendado: 3 caracteres (evita búsquedas muy amplias)", Colors.DIM))
			val = input(c("Nueva longitud mínima (1-10): ", Colors.CYAN)).strip()
			if val.isdigit():
				n = int(val)
				if 1 <= n <= 10:
					CONFIG['min_search_length'] = n
					save_config()
					print(c(f"Longitud mínima de búsqueda actualizada a {n} caracteres.", Colors.GREEN))
				else:
					print(c("Valor fuera de rango (1-10).", Colors.RED))
			else:
				print(c("Entrada no válida.", Colors.RED))
		elif opt in ('13', 'h'):
			# Configurar limpieza automática del historial
			print()
			print(c("Modos de limpieza:", Colors.CYAN))
			print(f"  {c('1.', Colors.YELLOW)} Desactivada")
			print(f"  {c('2.', Colors.YELLOW)} Por días (mantener últimos N días)")
			print(f"  {c('3.', Colors.YELLOW)} Por cantidad (mantener últimas N entradas)")
			choice = input(c("Selecciona modo: ", Colors.CYAN)).strip()
			if choice == '1':
				CONFIG['history_cleanup_mode'] = 'none'
				save_config()
				print(c("Limpieza automática desactivada.", Colors.GREEN))
			elif choice == '2':
				days_str = input(c("Días a mantener (ej. 30): ", Colors.CYAN)).strip()
				if days_str.isdigit():
					days = int(days_str)
					if days > 0:
						CONFIG['history_cleanup_mode'] = 'days'
						CONFIG['history_cleanup_days'] = days
						save_config()
						print(c(f"Limpieza automática configurada: mantener últimos {days} días.", Colors.GREEN))
						# Limpiar ahora
						cleanup_history_auto()
						print(c("Historial limpiado.", Colors.GREEN))
					else:
						print(c("Debe ser un número mayor que 0.", Colors.RED))
				else:
					print(c("Entrada no válida.", Colors.RED))
			elif choice == '3':
				count_str = input(c("Número máximo de entradas (ej. 200): ", Colors.CYAN)).strip()
				if count_str.isdigit():
					count = int(count_str)
					if count > 0:
						CONFIG['history_cleanup_mode'] = 'count'
						CONFIG['history_cleanup_max_entries'] = count
						save_config()
						print(c(f"Limpieza automática configurada: mantener últimas {count} entradas.", Colors.GREEN))
						# Limpiar ahora
						cleanup_history_auto()
						print(c("Historial limpiado.", Colors.GREEN))
					else:
						print(c("Debe ser un número mayor que 0.", Colors.RED))
				else:
					print(c("Entrada no válida.", Colors.RED))
			else:
				print(c("Opción no válida.", Colors.RED))
		elif opt in ('15', 'o'):
			CONFIG['use_custom_osd'] = not CONFIG.get('use_custom_osd', False)
			save_config()
			status = 'activada' if CONFIG['use_custom_osd'] else 'desactivada'
			print(c(f"OSD propia en reproducción {status}.", Colors.GREEN))
		elif opt in ('14', 'a'):
			# Toggle detección automática de categorías
			current = CONFIG.get('auto_discover_categories', False)
			CONFIG['auto_discover_categories'] = not current
			save_config()
			status = 'activada' if CONFIG['auto_discover_categories'] else 'desactivada'
			print(c(f"Detección automática de categorías {status}.", Colors.GREEN))
			if CONFIG['auto_discover_categories']:
				# Forzar descubrimiento inmediato
				print(c("Descubriendo categorías disponibles...", Colors.CYAN))
				discover_categories_from_repo(force_refresh=True)
				available_cats = get_available_categories()
				print(c(f"Total de categorías disponibles: {len(available_cats)}", Colors.GREEN))
			else:
				available_cats = get_available_categories()
				print(c(f"Usando solo categorías manuales: {len(available_cats)} categorías", Colors.CYAN))
		elif opt in ('16', 'e'):
			export_config_complete()
			CONFIG = load_config()  # Recargar configuración por si cambió
		elif opt in ('17', 'x'):
			import_config_complete()
			CONFIG = load_config()  # Recargar configuración después de importar
		else:
			print(c("Opción no válida.", Colors.RED))

# --- Menú de estadísticas ---

def format_duration(seconds: float) -> str:
	"""Formatea una duración en segundos a formato legible."""
	if seconds < 60:
		return f"{int(seconds)}s"
	elif seconds < 3600:
		mins = int(seconds // 60)
		secs = int(seconds % 60)
		return f"{mins}m {secs}s"
	else:
		hours = int(seconds // 3600)
		mins = int((seconds % 3600) // 60)
		if mins > 0:
			return f"{hours}h {mins}m"
		return f"{hours}h"


def draw_ascii_bar(value: int, max_value: int, width: int = 30) -> str:
	"""Dibuja una barra ASCII simple."""
	if max_value == 0:
		return ' ' * width
	fill = int((value / max_value) * width)
	bar = '█' * fill + '░' * (width - fill)
	return bar


def draw_osd_progress_bar(pos: int, total: int, width: int = 40) -> str:
	"""Barra de progreso para la OSD (estilo ▓░ con bordes)."""
	if total <= 0 or width < 3:
		return "[" + " " * (width - 2) + "]"
	fill = int((pos / total) * (width - 2))
	fill = min(fill, width - 2)
	bar = "[" + "▓" * fill + "░" * (width - 2 - fill) + "]"
	return bar


def stats_menu() -> None:
	header("Estadísticas")
	
	# Cargar datos
	history_entries = load_history()
	favorites = load_favorites()
	
	# Calcular estadísticas básicas
	total_reproducciones = len(history_entries)
	total_favoritos = len(favorites)
	
	# Calcular tiempo total de reproducción
	total_duration = 0.0
	for entry in history_entries:
		duration = entry.get('duration', 0)
		if isinstance(duration, (int, float)) and duration > 0:
			total_duration += duration
	
	# Emisoras más reproducidas
	station_counts: Dict[str, int] = {}
	station_durations: Dict[str, float] = {}
	for entry in history_entries:
		name = entry.get('name') or entry.get('url') or 'Unknown'
		url = entry.get('url') or ''
		key = url if url else name
		station_counts[key] = station_counts.get(key, 0) + 1
		duration = entry.get('duration', 0)
		if isinstance(duration, (int, float)) and duration > 0:
			station_durations[key] = station_durations.get(key, 0.0) + duration
	
	# Ordenar por número de reproducciones
	sorted_stations = sorted(station_counts.items(), key=lambda x: x[1], reverse=True)
	top_stations = sorted_stations[:10]  # Top 10
	
	# Fuentes más usadas
	source_counts: Dict[str, int] = {}
	for entry in history_entries:
		source = entry.get('source') or 'desconocido'
		source_counts[source] = source_counts.get(source, 0) + 1
	
	sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
	
	# Horas más activas
	hour_counts: Dict[int, int] = {}
	for entry in history_entries:
		ts = entry.get('ts', 0)
		if ts:
			try:
				dt = datetime.fromtimestamp(ts)
				hour = dt.hour
				hour_counts[hour] = hour_counts.get(hour, 0) + 1
			except Exception:
				pass
	
	# Días más activos (día de la semana)
	day_counts: Dict[int, int] = {}
	day_names = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
	for entry in history_entries:
		ts = entry.get('ts', 0)
		if ts:
			try:
				dt = datetime.fromtimestamp(ts)
				weekday = dt.weekday()
				day_counts[weekday] = day_counts.get(weekday, 0) + 1
			except Exception:
				pass
	
	print()
	print(c("Resumen general:", Colors.CYAN))
	print(f"  {c('Total de reproducciones:', Colors.DIM)} {total_reproducciones}")
	print(f"  {c('Emisoras únicas reproducidas:', Colors.DIM)} {len(station_counts)}")
	print(f"  {c('Favoritos guardados:', Colors.DIM)} {total_favoritos}")
	if total_duration > 0:
		print(f"  {c('Tiempo total escuchado:', Colors.DIM)} {format_duration(total_duration)}")
	
	# Gráfico de horas más activas
	if hour_counts:
		print()
		print(c("Horas más activas:", Colors.CYAN))
		max_hour_count = max(hour_counts.values()) if hour_counts.values() else 1
		for hour in range(24):
			count = hour_counts.get(hour, 0)
			bar = draw_ascii_bar(count, max_hour_count, 20)
			hour_str = f"{hour:02d}:00"
			print(f"  {c(hour_str, Colors.YELLOW)} {bar} {dim(f'({count})')}")
	
	# Gráfico de días más activos
	if day_counts:
		print()
		print(c("Días de la semana más activos:", Colors.CYAN))
		max_day_count = max(day_counts.values()) if day_counts.values() else 1
		for day_idx in range(7):
			count = day_counts.get(day_idx, 0)
			bar = draw_ascii_bar(count, max_day_count, 20)
			day_name = day_names[day_idx]
			print(f"  {c(day_name, Colors.YELLOW)} {bar} {dim(f'({count})')}")
	
	if top_stations:
		print()
		print(c("Top 10 emisoras más reproducidas:", Colors.CYAN))
		for i, (key, count) in enumerate(top_stations, 1):
			# Buscar el nombre de la emisora
			name = key
			for entry in history_entries:
				if (entry.get('url') or '') == key or (not key and entry.get('name')):
					name = entry.get('name') or key or 'Unknown'
					break
			duration_info = ""
			if key in station_durations and station_durations[key] > 0:
				duration_info = f" [{format_duration(station_durations[key])}]"
			print(f"  {c(str(i).rjust(2) + '.', Colors.YELLOW)} {name[:50]} {dim(f'({count}x)')}{duration_info}")
	
	if sorted_sources:
		print()
		print(c("Fuentes más escuchadas:", Colors.CYAN))
		max_source_count = max(sorted_sources, key=lambda x: x[1])[1] if sorted_sources else 1
		for source, count in sorted_sources[:5]:
			bar = draw_ascii_bar(count, max_source_count, 15)
			print(f"  {c(source, Colors.GREEN)} {bar} {dim(f'({count})')}")
	
	# Últimas reproducciones
	if history_entries:
		print()
		print(c("Últimas 5 reproducciones:", Colors.CYAN))
		for entry in history_entries[-5:][::-1]:  # Últimas 5, más reciente primero
			name = entry.get('name') or entry.get('url') or 'Unknown'
			source = entry.get('source') or ''
			ts = entry.get('ts', 0)
			duration = entry.get('duration', 0)
			if ts:
				try:
					dt = datetime.fromtimestamp(ts)
					time_str = dt.strftime('%Y-%m-%d %H:%M')
				except Exception:
					time_str = 'fecha desconocida'
			else:
				time_str = 'fecha desconocida'
			badge = dim(f"[{source}]") if source else ''
			duration_str = f" - {format_duration(duration)}" if isinstance(duration, (int, float)) and duration > 0 else ""
			print(f"  {name[:45]} {badge} {dim(f'({time_str})')}{duration_str}")
	
	print()
	input(c("Pulsa enter para volver... ", Colors.CYAN))


# --- Menú de historial ---

def history_menu() -> None:
	entries = load_history()
	if not entries:
		header("Historial")
		print(c("No hay historial todavía.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	labels = []
	for e in reversed(entries):
		name = e.get('name') or e.get('url')
		src = e.get('source') or ''
		badge = dim(f"[{src}]") if src else ''
		labels.append(f"{name} {badge}")
	while True:
		print()
		header(f"Historial (recientes) ({len(entries)} entradas)")
		print(f"  {c('1.', Colors.YELLOW)} {icon('LAST')}Reproducir último (l)  |  {c('2.', Colors.YELLOW)} {icon('EXPORT')}Exportar (e)  |  {c('3.', Colors.YELLOW)} {icon('IMPORT')}Importar (i)  |  {c('4.', Colors.YELLOW)} {icon('RANDOM')}Aleatorio (r)  |  {c('5.', Colors.YELLOW)} {icon('TRASH')}Limpiar (c)  |  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		cmd = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if cmd in ('0', 'q'):
			return
		if cmd in ('1', 'l'):
			# Reproducir último canal del historial
			if entries:
				last_entry = entries[-1]
				name = last_entry.get('name') or last_entry.get('url') or ''
				url = last_entry.get('url') or ''
				if url:
					print(f"{c('Reproduciendo último:', Colors.GREEN)} {name}")
					try:
						play_with_config(url, name, source=last_entry.get('source'))
					except MpvNotFoundError as e:
						print(str(e))
					append_history(name, url, last_entry.get('source') or 'historial')
				else:
					print(c("No hay URL válida en la última entrada.", Colors.RED))
			else:
				print(c("No hay historial.", Colors.YELLOW))
			input(c("Pulsa enter para volver... ", Colors.CYAN))
			continue
		if cmd in ('5', 'c'):
			# Limpiar historial
			if not entries:
				print(c("El historial ya está vacío.", Colors.YELLOW))
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				continue
			print(c(f"El historial contiene {len(entries)} entradas.", Colors.CYAN))
			result = prompt_yes_no("¿Limpiar todo el historial?", default_yes=False)
			if result is True:
				save_history([])
				entries = []
				labels = []
				print(c("Historial limpiado.", Colors.GREEN))
			input(c("Pulsa enter para volver... ", Colors.CYAN))
			continue
		if cmd in ('2', 'e'):
			path = input(c("Ruta destino (ej. history_export.json): ", Colors.CYAN)).strip()
			if not path:
				print(c("Ruta inválida.", Colors.RED))
			else:
				try:
					with open(path, 'w', encoding='utf-8') as f:
						json.dump(entries, f, ensure_ascii=False, indent=2)
					print(c("Historial exportado.", Colors.GREEN))
				except Exception as e:
					print(c(f"Error exportando: {e}", Colors.RED))
			continue
		if cmd in ('3', 'i'):
			src = input(c("Ruta origen (archivo JSON de historial): ", Colors.CYAN)).strip()
			try:
				with open(src, 'r', encoding='utf-8') as f:
					data = json.load(f)
				if isinstance(data, list):
					save_history(data)
					print(c("Historial importado.", Colors.GREEN))
					entries = load_history()
					labels = []
					for e in reversed(entries):
						name = e.get('name') or e.get('url')
						src2 = e.get('source') or ''
						badge2 = dim(f"[{src2}]") if src2 else ''
						labels.append(f"{name} {badge2}")
				else:
					print(c("Formato inválido.", Colors.RED))
			except Exception as e:
				print(c(f"Error importando: {e}", Colors.RED))
			continue
		if cmd in ('4', 'r'):
			attempts = 0
			while True:
				entry = random.choice(entries)
				name = entry.get('name') or entry.get('url') or ''
				print(f"{c('Reproduciendo (aleatorio historial):', Colors.GREEN)} {name}")
				try:
					code = play_with_config(entry.get('url') or '', name, source=entry.get('source'))
				except MpvNotFoundError as e:
					print(str(e))
					break
				if code != 0:
					attempts += 1
					if attempts <= 3:
						print(c("Fallo, probando otra entrada...", Colors.YELLOW))
						continue
					else:
						print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
						break
				# Solo añadir al historial si la reproducción fue exitosa
				append_history(name, entry.get('url') or '', entry.get('source') or 'historial')
				result = prompt_yes_no("¿Reproducir otro historial aleatorio?", default_yes=True)
				if result is None or not result:
					break
			continue
		idx = paginated_select(labels, "Historial (recientes)", show_count=False)
		if idx in (0, -1):
			return
		if idx == -2 or idx == -3:
			continue
		entry = list(reversed(entries))[idx - 1]
		print(f"{c('Reproduciendo desde historial:', Colors.GREEN)} {entry.get('name')}")
		try:
			play_with_config(entry.get('url') or '', entry.get('name'), source=entry.get('source'))
		except MpvNotFoundError as e:
			print(str(e))
		append_history(entry.get('name') or '', entry.get('url') or '', entry.get('source') or '')


# --- Descarga de listas desde GitHub ---

GITHUB_REPO_BASE = "https://raw.githubusercontent.com/junguler/m3u-radio-music-playlists/main"

# Categorías populares disponibles en el repositorio (archivos en la raíz)
POPULAR_CATEGORIES = [
	("rock", "Rock"),
	("pop", "Pop"),
	("electronic", "Electronic"),
	("hip_hop", "Hip Hop"),
	("jazz", "Jazz"),
	("classical", "Classical"),
	("country", "Country"),
	("reggae", "Reggae"),
	("metal", "Metal"),
	("dance", "Dance"),
	("techno", "Techno"),
	("house", "House"),
	("trance", "Trance"),
	("latin", "Latin"),
	("funk", "Funk"),
	("blues", "Blues"),
	("alternative", "Alternative"),
	("indie", "Indie"),
	("hardrock", "Hard Rock"),
	("acid_jazz", "Acid Jazz"),
	("smooth_jazz", "Smooth Jazz"),
	("eurodance", "Eurodance"),
	("jpop", "J-Pop"),
	# Categorías adicionales ampliadas
	("disco", "Disco"),
	("dubstep", "Dubstep"),
	("edm", "EDM"),
	("hardcore", "Hardcore"),
	("lofi", "Lo-Fi"),
	("rnb", "R&B"),
	("rap", "Rap"),
	("trap", "Trap"),
	("garage", "Garage"),
	("goa", "Goa"),
	("jungle", "Jungle"),
	("progressive", "Progressive"),
	("reggaeton", "Reggaeton"),
	("soundtrack", "Soundtrack"),
	("oldies", "Oldies"),
	("classic", "Classic"),
	("ambient", "Ambient"),
	("chill", "Chill"),
	("folk", "Folk"),
	("gospel", "Gospel"),
	("grunge", "Grunge"),
	("industrial", "Industrial"),
	("kpop", "K-Pop"),
	("new_age", "New Age"),
	("punk", "Punk"),
	("ska", "Ska"),
	("soul", "Soul"),
	("synthwave", "Synthwave"),
	("world_music", "World Music"),
	("deep_house", "Deep House"),
	("drum_and_bass", "Drum and Bass"),
	("minimal_techno", "Minimal Techno"),
	("post_rock", "Post Rock"),
	("progressive_house", "Progressive House"),
	("progressive_metal", "Progressive Metal"),
	("progressive_rock", "Progressive Rock"),
	("black_metal", "Black Metal"),
	("death_metal", "Death Metal"),
	("heavy_metal", "Heavy Metal"),
	("soft_rock", "Soft Rock"),
	("modern_rock", "Modern Rock"),
	("classic_rock", "Classic Rock"),
	("alternative_rock", "Alternative Rock"),
	("pop_rock", "Pop Rock"),
	("dancehall", "Dancehall"),
	("roots_reggae", "Roots Reggae"),
	("lovers_rock_reggae", "Lovers Rock Reggae"),
	("urban", "Urban"),
	("hits", "Hits"),
	("top_40", "Top 40"),
	("easy_listening", "Easy Listening"),
]

# Estilos más populares (selección recomendada)
MOST_POPULAR_GENRES = [
	"rock", "pop", "electronic", "hip_hop", "jazz", "metal", 
	"dance", "techno", "house", "trance", "latin", "alternative"
]

# Caché para categorías descubiertas automáticamente
DISCOVERED_CATEGORIES_CACHE: Optional[List[tuple]] = None
DISCOVERED_CATEGORIES_CACHE_TIME: Optional[float] = None
CACHE_DURATION_SECONDS = 3600  # 1 hora


def discover_categories_from_repo(force_refresh: bool = False) -> List[tuple]:
	"""
	Descubre automáticamente las categorías disponibles en el repositorio de GitHub.
	
	Usa la API de GitHub para listar archivos .m3u en el repositorio y extrae
	las categorías de los nombres de archivo.
	
	Args:
		force_refresh: Si es True, fuerza la actualización del caché
		
	Returns:
		Lista de tuplas (category_key, category_name) con las categorías descubiertas
	"""
	global DISCOVERED_CATEGORIES_CACHE, DISCOVERED_CATEGORIES_CACHE_TIME
	
	# Verificar caché
	current_time = time.time()
	if not force_refresh and DISCOVERED_CATEGORIES_CACHE is not None:
		if DISCOVERED_CATEGORIES_CACHE_TIME is not None:
			if current_time - DISCOVERED_CATEGORIES_CACHE_TIME < CACHE_DURATION_SECONDS:
				return DISCOVERED_CATEGORIES_CACHE
	
	# Intentar cargar desde caché en disco
	cache_file = os.path.join(USER_DATA_DIR, 'discovered_categories_cache.json')
	if not force_refresh and os.path.isfile(cache_file):
		try:
			with open(cache_file, 'r', encoding='utf-8') as f:
				cache_data = json.load(f)
				cache_time = cache_data.get('timestamp', 0)
				if current_time - cache_time < CACHE_DURATION_SECONDS:
					categories = cache_data.get('categories', [])
					if categories:
						DISCOVERED_CATEGORIES_CACHE = [(c[0], c[1]) for c in categories]
						DISCOVERED_CATEGORIES_CACHE_TIME = cache_time
						return DISCOVERED_CATEGORIES_CACHE
		except Exception:
			pass
	
	# Usar API de GitHub para descubrir categorías
	api_url = "https://api.github.com/repos/junguler/m3u-radio-music-playlists/contents/"
	discovered: List[tuple] = []
	
	print(c("Descubriendo categorías disponibles en el repositorio...", Colors.CYAN), end='', flush=True)
	
	try:
		files = http_get_json(api_url, timeout=15)
		if files and isinstance(files, list):
			for item in files:
				if isinstance(item, dict):
					name = item.get('name', '')
					# Filtrar solo archivos .m3u (excluir .m3u8 y otros)
					if name.endswith('.m3u') and not name.startswith('---'):
						# Extraer categoría del nombre (sin extensión)
						category_key = name[:-4]  # Quitar .m3u
						# Convertir a nombre legible
						category_name = category_key.replace('_', ' ').replace('-', ' ').title()
						# Limpiar nombres comunes
						category_name = category_name.replace('Rn B', 'R&B').replace('R N B', 'R&B')
						category_name = category_name.replace('Hip Hop', 'Hip Hop').replace('Hiphop', 'Hip Hop')
						discovered.append((category_key, category_name))
			
			# Ordenar por nombre
			discovered.sort(key=lambda x: x[1])
			
			# Actualizar caché en memoria
			DISCOVERED_CATEGORIES_CACHE = discovered
			DISCOVERED_CATEGORIES_CACHE_TIME = current_time
			
			# Guardar en caché en disco
			try:
				with open(cache_file, 'w', encoding='utf-8') as f:
					json.dump({
						'timestamp': current_time,
						'categories': discovered
					}, f, ensure_ascii=False, indent=2)
			except Exception:
				pass
			
			check_icon = Icons.get_icon('CHECK')
			print(c(f" {check_icon} {len(discovered)} categorías descubiertas", Colors.GREEN))
		else:
			cross_icon = Icons.get_icon('CROSS')
			print(c(f" {cross_icon} No se pudieron obtener categorías", Colors.YELLOW))
	except Exception as e:
		cross_icon = Icons.get_icon('CROSS')
		print(c(f" {cross_icon} Error: {str(e)}", Colors.RED))
	
	return discovered if discovered else []


def get_available_categories() -> List[tuple]:
	"""
	Retorna las categorías disponibles para búsqueda.
	
	Si la detección automática está habilitada, combina las categorías manuales
	con las descubiertas automáticamente. Si no, solo retorna las manuales.
	
	Returns:
		Lista de tuplas (category_key, category_name) con todas las categorías disponibles
	"""
	# Verificar si la detección automática está habilitada
	auto_discover = CONFIG.get('auto_discover_categories', False)
	
	if auto_discover:
		# Obtener categorías descubiertas
		discovered = discover_categories_from_repo()
		
		# Combinar con categorías manuales (evitando duplicados)
		manual_keys = {cat[0] for cat in POPULAR_CATEGORIES}
		all_categories = list(POPULAR_CATEGORIES)
		
		for cat in discovered:
			if cat[0] not in manual_keys:
				all_categories.append(cat)
		
		return all_categories
	else:
		# Solo usar categorías manuales
		return POPULAR_CATEGORIES


def download_playlist_from_github(category: str, filename: str, display_name: str) -> bool:
	"""Descarga una playlist desde el repositorio de GitHub.
	
	Args:
		category: Categoría/carpeta en el repo (ej: "rock", "" para raíz)
		filename: Nombre del archivo M3U
		display_name: Nombre para mostrar al usuario
		
	Returns:
		True si la descarga fue exitosa, False en caso contrario.
	"""
	# Construir URL
	if category:
		url = f"{GITHUB_REPO_BASE}/{category}/{filename}"
	else:
		url = f"{GITHUB_REPO_BASE}/{filename}"
	
	# Nombre del archivo local (usar el nombre original o uno más limpio)
	local_filename = filename
	if not local_filename.lower().endswith(('.m3u', '.m3u8')):
		local_filename += '.m3u'
	
	dest_path = os.path.join(PLAYLISTS_DIR, local_filename)
	
	# Verificar si ya existe
	if os.path.exists(dest_path):
		result = prompt_yes_no(f"El archivo '{local_filename}' ya existe. ¿Sobrescribir?", default_yes=False)
		if result is None or not result:
			return False
	
	print(c(f"Descargando {display_name}...", Colors.CYAN), end='', flush=True)
	
	success, error_msg = http_download_file(url, dest_path, timeout=60)
	if success:
		# Verificar que el archivo se descargó correctamente
		try:
			channels = parse_m3u_file(dest_path)
			check_icon = Icons.get_icon('CHECK')
			print(c(f" {check_icon} ({len(channels)} emisoras)", Colors.GREEN))
			return True
		except Exception as e:
			cross_icon = Icons.get_icon('CROSS')
			print(c(f" {cross_icon}", Colors.RED))
			print(c(f"Error: El archivo descargado no es válido: {e}", Colors.RED))
			# Intentar eliminar el archivo corrupto
			try:
				os.remove(dest_path)
			except Exception:
				pass
			return False
	else:
		cross_icon = Icons.get_icon('CROSS')
		print(c(f" {cross_icon}", Colors.RED))
		if error_msg:
			print(c(f"Error: {error_msg}", Colors.RED))
		else:
			print(c(f"Error: No se pudo descargar el archivo desde {url}", Colors.RED))
		return False


def multi_select_categories() -> List[tuple]:
	"""Permite seleccionar múltiples categorías con checkboxes.
	
	Returns:
		Lista de tuplas (category_key, category_name) seleccionadas.
	"""
	selected = set()
	# Obtener categorías disponibles (puede incluir descubiertas)
	available_cats = get_available_categories()
	categories_dict = {cat[0]: cat for cat in available_cats}
	
	while True:
		header("Seleccionar categorías (múltiple)")
		print()
		print(c("Instrucciones:", Colors.CYAN))
		print("  - Escribe el número para seleccionar/deseleccionar")
		print("  - 'a' para seleccionar estilos más populares")
		print("  - 'd' para descargar las seleccionadas")
		print("  - 'q' para cancelar")
		print()
		
		# Mostrar categorías con checkboxes
		for i, (key, name) in enumerate(available_cats, 1):
			marker = "✓" if key in selected else " "
			marker_color = Colors.GREEN if key in selected else Colors.WHITE
			is_popular = "⭐" if key in MOST_POPULAR_GENRES else " "
			print(f"  {c(f'[{marker}]', marker_color)} {c(str(i), Colors.YELLOW)}. {is_popular} {name} ({key})")
		
		print()
		print(f"  {c('a.', Colors.GREEN)} Seleccionar estilos más populares ({len(MOST_POPULAR_GENRES)} estilos)")
		print(f"  {c('d.', Colors.GREEN)} Descargar seleccionadas ({len(selected)} categorías)")
		print(f"  {c('0.', Colors.YELLOW)} Cancelar (q)")
		print(c(line(), Colors.BLUE))
		
		choice = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		
		if choice in ('0', 'q'):
			return []
		elif choice == 'a':
			# Seleccionar estilos más populares
			selected.update(MOST_POPULAR_GENRES)
			print(c(f"✓ Seleccionados {len(MOST_POPULAR_GENRES)} estilos más populares", Colors.GREEN))
			input(c("Pulsa enter para continuar... ", Colors.CYAN))
		elif choice == 'd':
			if not selected:
				print(c("No hay categorías seleccionadas.", Colors.YELLOW))
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
				continue
			# Confirmar descarga
			selected_list = [categories_dict[key] for key in selected if key in categories_dict]
			names = [cat[1] for cat in selected_list]
			print()
			print(c(f"Se descargarán {len(selected_list)} categorías:", Colors.CYAN))
			for name in names:
				print(f"  - {name}")
			print()
			result = prompt_yes_no("¿Continuar con la descarga?", default_yes=True)
			if result is None or not result:
				continue
			return selected_list
		elif choice.isdigit():
			num = int(choice)
			if 1 <= num <= len(available_cats):
				key = available_cats[num - 1][0]
				if key in selected:
					selected.remove(key)
				else:
					selected.add(key)
			else:
				print(c("Número inválido.", Colors.RED))
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
		else:
			print(c("Opción no válida.", Colors.RED))
			input(c("Pulsa enter para continuar... ", Colors.CYAN))


def search_remote_repository(query: str, categories: Optional[List[str]] = None) -> List[Dict]:
	"""Busca en el repositorio remoto de GitHub sin descargar archivos.
	
	Args:
		query: Texto a buscar
		categories: Lista de categorías donde buscar (None = todas)
		
	Returns:
		Lista de canales encontrados con formato {'name': str, 'url': str, 'source': str}
	"""
	from m3u_parser import parse_m3u
	
	# Obtener categorías disponibles (puede incluir descubiertas automáticamente)
	available_categories = get_available_categories()
	
	if categories is None:
		# Buscar en todas las categorías disponibles
		categories_to_search = [cat[0] for cat in available_categories]
	else:
		categories_to_search = categories
	
	query_lower = query.lower()
	results: List[Dict] = []
	
	print(c(f"Buscando en {len(categories_to_search)} categorías remotas...", Colors.CYAN))
	
	for i, category_key in enumerate(categories_to_search, 1):
		# Buscar el nombre de la categoría
		category_name = next((cat[1] for cat in available_categories if cat[0] == category_key), category_key)
		filename = f"{category_key}.m3u"
		url = f"{GITHUB_REPO_BASE}/{filename}"
		
		# Mostrar progreso
		print(c(f"  [{i}/{len(categories_to_search)}] Buscando en {category_name}...", Colors.CYAN), end='\r', flush=True)
		
		# Descargar contenido en memoria
		content, error = http_fetch_content(url, timeout=30)
		if error or not content:
			continue
		
		# Parsear M3U
		try:
			channels = parse_m3u(content)
		except Exception:
			continue
		
		# Buscar coincidencias
		for ch in channels:
			name = (ch.get('name') or '')
			url_ch = (ch.get('url') or '')
			if query_lower in name.lower() or query_lower in url_ch.lower():
				results.append({
					'name': name or url_ch,
					'url': url_ch,
					'source': f"remote:{category_name}",
					'category': category_key
				})
	
	# Limpiar línea de progreso
	print(' ' * 80, end='\r', flush=True)
	
	return results


def remote_search_menu() -> None:
	"""Menú para buscar en el repositorio remoto sin descargar."""
	header("Búsqueda en repositorio remoto")
	
	# Cargar historial de búsquedas y sugerencias
	search_history = load_search_history()
	favorites = load_favorites()
	play_history = load_history()
	
	# Mostrar búsquedas recientes si existen
	if search_history:
		print(c("Búsquedas recientes:", Colors.CYAN))
		for i, h in enumerate(search_history[:5], 1):
			print(f"  {c(str(i), Colors.YELLOW)}. {h}")
		print()
	
	# Obtener sugerencias
	suggestions = get_search_suggestions("", search_history, favorites, play_history)
	query = prompt_with_suggestions("Texto a buscar (nombre de emisora) o número de sugerencia: ", suggestions, search_history)
	
	if not query:
		print(c("Búsqueda vacía.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Validar longitud mínima de búsqueda
	min_length = CONFIG.get('min_search_length', MIN_SEARCH_LENGTH)
	try:
		min_length = int(min_length)
	except Exception:
		min_length = MIN_SEARCH_LENGTH
	
	if len(query) < min_length:
		print(c(f"⚠ Búsqueda muy corta ({len(query)} caracteres).", Colors.YELLOW))
		print(c(f"Se recomienda al menos {min_length} caracteres para evitar resultados excesivos.", Colors.YELLOW))
		if len(query) == 1:
			result = prompt_yes_no(f"¿Realmente quieres buscar con solo '{query}'? (puede tardar mucho)", default_yes=False)
			if result is None or not result:
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				return
		elif len(query) == 2:
			result = prompt_yes_no(f"¿Continuar con la búsqueda '{query}'? (puede generar muchos resultados)", default_yes=False)
			if result is None or not result:
				input(c("Pulsa enter para volver... ", Colors.CYAN))
				return
	
	# Obtener categorías disponibles (puede incluir descubiertas automáticamente)
	available_categories = get_available_categories()
	auto_discover_enabled = CONFIG.get('auto_discover_categories', False)
	
	# Preguntar si buscar en todas las categorías o seleccionar
	print()
	print(c("¿Dónde buscar?", Colors.CYAN))
	if auto_discover_enabled:
		print(f"  {c('1.', Colors.YELLOW)} Todas las categorías ({len(available_categories)} categorías, incluye descubiertas)")
	else:
		print(f"  {c('1.', Colors.YELLOW)} Todas las categorías ({len(available_categories)} categorías)")
	print(f"  {c('2.', Colors.YELLOW)} Solo estilos más populares ({len(MOST_POPULAR_GENRES)} categorías)")
	print(f"  {c('3.', Colors.YELLOW)} Seleccionar categorías específicas")
	print(f"  {c('0.', Colors.YELLOW)} Cancelar (q)")
	print(c(line(), Colors.BLUE))
	
	search_opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
	
	categories_to_search = None
	if search_opt == '0' or search_opt == 'q':
		return
	elif search_opt == '1':
		# Todas las categorías
		categories_to_search = None
	elif search_opt == '2':
		# Solo populares
		categories_to_search = MOST_POPULAR_GENRES
	elif search_opt == '3':
		# Selección múltiple
		selected = multi_select_categories()
		if not selected:
			return
		categories_to_search = [cat[0] for cat in selected]
	else:
		print(c("Opción no válida.", Colors.RED))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Añadir a historial de búsquedas
	add_to_search_history(query)
	
	# Realizar búsqueda
	results = search_remote_repository(query, categories_to_search)
	
	if not results:
		print(c("Sin resultados en el repositorio remoto.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
	
	# Interacción con resultados
	while True:
		labels = []
		for r in results:
			badge = dim(f"[{r['source']}]")
			labels.append(f"{r['name']} {badge}")
		
		print()
		header(f"Resultados remotos ({len(results)})")
		print(f"  {c('1.', Colors.YELLOW)} Aleatorio entre resultados (r)")
		print(f"  {c('2.', Colors.YELLOW)} {icon('IMPORT')}Descargar categorías de resultados (d)")
		print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		
		sel = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		
		if sel in ('0', 'q'):
			return
		elif sel in ('1', 'r'):
			# Bucle aleatorio sobre resultados
			attempts = 0
			while True:
				item = random.choice(results)
				print(f"{c('Reproduciendo (aleatorio remoto):', Colors.GREEN)} {item['name']} {dim(f'[{item['source']}]')}")
				try:
					code = play_with_config(item['url'], item.get('name'), source=item.get('source'))
				except MpvNotFoundError as e:
					print(str(e))
					return
				if code != 0:
					attempts += 1
					if attempts <= 3:
						print(c("Fallo, probando otra emisora...", Colors.YELLOW))
						continue
					else:
						print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
						return
				# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
				append_history(item['name'], item['url'], item['source'])
				offer_add_favorite(item['name'], item['url'], item['source'])
				result = prompt_yes_no("¿Reproducir otra emisora aleatoria de los resultados?", default_yes=True)
				if result is None or not result:
					return
			continue
		elif sel in ('2', 'd'):
			# Descargar categorías de los resultados
			categories_found = set(r.get('category', '') for r in results if r.get('category'))
			if not categories_found:
				print(c("No se pueden identificar las categorías de los resultados.", Colors.YELLOW))
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
				continue
			
			# Usar categorías disponibles (puede incluir descubiertas)
			available_cats = get_available_categories()
			categories_to_download = [(key, name) for key, name in available_cats if key in categories_found]
			names = [cat[1] for cat in categories_to_download]
			print()
			print(c(f"Se descargarán {len(categories_to_download)} categorías encontradas:", Colors.CYAN))
			for name in names:
				print(f"  - {name}")
			print()
			result = prompt_yes_no("¿Continuar con la descarga?", default_yes=True)
			if result is not None and result:
				download_multiple_categories(categories_to_download)
			continue
		
		# Selección paginada
		idx = paginated_select(labels, "Resultados remotos")
		if idx == 0 or idx == -1:
			return
		item = results[idx - 1]
		print(f"{c('Reproduciendo:', Colors.GREEN)} {item['name']} {dim(f'[{item['source']}]')}")
		try:
			code = play_with_config(item['url'], item.get('name'), source=item.get('source'))
		except MpvNotFoundError as e:
			print(str(e))
			return
		# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
		if code == 0:
			append_history(item['name'], item['url'], item['source'])
		offer_add_favorite(item['name'], item['url'], item['source'])


def download_multiple_categories(categories: List[tuple]) -> None:
	"""Descarga múltiples categorías en secuencia."""
	if not categories:
		return
	
	total = len(categories)
	success_count = 0
	failed_count = 0
	
	print()
	print(c(f"Descargando {total} categorías...", Colors.CYAN))
	print()
	
	for i, (category_key, category_name) in enumerate(categories, 1):
		filename = f"{category_key}.m3u"
		print(c(f"[{i}/{total}] ", Colors.CYAN), end='', flush=True)
		success = download_playlist_from_github("", filename, category_name)
		if success:
			success_count += 1
		else:
			failed_count += 1
	
	print()
	print(c(line(), Colors.BLUE))
	print(c(f"Descarga completada:", Colors.CYAN))
	print(c(f"  ✓ Exitosas: {success_count}", Colors.GREEN))
	if failed_count > 0:
		print(c(f"  ✗ Fallidas: {failed_count}", Colors.RED))
	print()


def download_playlists_menu() -> None:
	"""Menú para descargar playlists desde el repositorio de GitHub."""
	header("Descargar playlists desde GitHub")
	
	while True:
		print()
		print(c("Repositorio: junguler/m3u-radio-music-playlists", Colors.CYAN))
		print()
		print(f"  {c('1.', Colors.YELLOW)} Descargar 'everything-full.m3u' (lista completa)")
		print(f"  {c('2.', Colors.YELLOW)} Descargar una categoría")
		print(f"  {c('3.', Colors.YELLOW)} {icon('IMPORT')}Descargar múltiples categorías (selección)")
		print(f"  {c('4.', Colors.YELLOW)} {icon('STAR')}Descargar estilos más populares ({len(MOST_POPULAR_GENRES)} estilos)")
		print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		
		opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		
		if opt in ('0', 'q'):
			return
		elif opt == '1':
			# Descargar everything-full.m3u (el archivo real se llama ---everything-full.m3u)
			success = download_playlist_from_github("", "---everything-full.m3u", "Everything Full")
			if success:
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
			else:
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
		elif opt == '2':
			# Menú de categorías (una sola)
			header("Seleccionar categoría")
			available_cats = get_available_categories()
			categories_list = [f"{cat[1]} ({cat[0]})" for cat in available_cats]
			idx = paginated_select(categories_list, "Categorías disponibles")
			
			if idx == 0:
				continue
			if idx > 0 and idx <= len(available_cats):
				category_key, category_name = available_cats[idx - 1]
				# El nombre del archivo suele ser el mismo que la categoría con .m3u
				# Los archivos de categorías están en la raíz, no en subcarpetas
				filename = f"{category_key}.m3u"
				success = download_playlist_from_github("", filename, category_name)
				if success:
					input(c("Pulsa enter para continuar... ", Colors.CYAN))
				else:
					input(c("Pulsa enter para continuar... ", Colors.CYAN))
		elif opt == '3':
			# Selección múltiple
			selected = multi_select_categories()
			if selected:
				download_multiple_categories(selected)
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
		elif opt == '4':
			# Descargar estilos más populares directamente
			available_cats = get_available_categories()
			popular_categories = [(key, name) for key, name in available_cats if key in MOST_POPULAR_GENRES]
			names = [cat[1] for cat in popular_categories]
			print()
			print(c(f"Se descargarán {len(popular_categories)} estilos más populares:", Colors.CYAN))
			for name in names:
				print(f"  - {name}")
			print()
			result = prompt_yes_no("¿Continuar con la descarga?", default_yes=True)
			if result is not None and result:
				download_multiple_categories(popular_categories)
				input(c("Pulsa enter para continuar... ", Colors.CYAN))


def main() -> int:
	global SORT_PLAYLISTS_ASC, CONFIG, CURRENT_PAGE_SIZE, SORT_CHANNELS_ASC
	CONFIG = load_config()
	# Aplicar preferencias del archivo de config
	try:
		ps = int(CONFIG.get('page_size') or 20)
		if 5 <= ps <= 100:
			CURRENT_PAGE_SIZE = ps
	except Exception:
		pass
	sort_pl = (CONFIG.get('sort_playlists') or 'asc').lower()
	SORT_PLAYLISTS_ASC = (sort_pl != 'desc')
	sort_ch = (CONFIG.get('sort_channels') or 'asc').lower()
	SORT_CHANNELS_ASC = (sort_ch != 'desc')

	enable_colors_on_windows()
	header("Menú principal - cmdRadioPy")
	print_ascii_logo()
	pls = list_playlists()
	if not pls:
		print(f"No se encontraron listas en '{PLAYLISTS_DIR}'. Añade archivos .m3u/.m3u8.")
		return 1
	while True:
		print()
		header("Menú principal - cmdRadioPy")
		print_ascii_logo()
		
		# REPRODUCCIÓN
		print(c("  ┌─ REPRODUCCIÓN", Colors.CYAN))
		print(f"  {c('1.', Colors.YELLOW)} {icon('PLAY')}Mostrar canales")
		print(f"  {c('2.', Colors.YELLOW)} {icon('RANDOM')}Reproducción aleatoria (r)")
		print(f"  {c('3.', Colors.YELLOW)} {icon('LAST')}Reproducir último canal (u/l)")
		
		# BÚSQUEDA
		print(c("  ┌─ BÚSQUEDA", Colors.CYAN))
		print(f"  {c('4.', Colors.YELLOW)} {icon('SEARCH')}Buscar en canales locales (/)")
		print(f"  {c('5.', Colors.YELLOW)} {icon('ONLINE')}Buscar online (Radio Browser) (b)")
		print(f"  {c('6.', Colors.YELLOW)} {icon('SEARCH')}Buscar en repositorio remoto (g)")
		
		# GESTIÓN
		print(c("  ┌─ GESTIÓN", Colors.CYAN))
		print(f"  {c('7.', Colors.YELLOW)} {icon('FAVORITE')}Favoritos")
		print(f"  {c('8.', Colors.YELLOW)} {icon('HISTORY')}Historial")
		print(f"  {c('9.', Colors.YELLOW)} {icon('STATS')}Estadísticas (s)")
		
		# CONFIGURACIÓN Y DATOS
		print(c("  ┌─ CONFIGURACIÓN Y DATOS", Colors.CYAN))
		print(f"  {c('10.', Colors.YELLOW)} {icon('IMPORT')}Descargar playlists desde GitHub (d)")
		print(f"  {c('11.', Colors.YELLOW)} {icon('CONFIG')}Configuración (c)")
		
		print()
		print(f"  {c('0.', Colors.YELLOW)} {icon('EXIT')}Salir (q)")
		print(c(line(), Colors.BLUE))
		opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if opt in ('0', 'q'):
			return 0
		# REPRODUCCIÓN
		elif opt == '1':
			pls = list_playlists()
			# Filtro para playlists
			pl_filter = ''
			while True:
				filtered_pls = [p for p in pls if pl_filter in p.lower()] if pl_filter else pls
				title_with_count = f"Playlists detectadas ({len(filtered_pls)})"
				idx = paginated_select(filtered_pls, title_with_count)
				if idx == -2:
					SORT_PLAYLISTS_ASC = not SORT_PLAYLISTS_ASC
					CONFIG['sort_playlists'] = 'asc' if SORT_PLAYLISTS_ASC else 'desc'
					save_config()
					pls = list_playlists()
					continue
				if idx == -3:
					pl_filter = input(c("Texto a filtrar playlists: ", Colors.CYAN)).strip().lower()
					continue
				break
			if idx == 0:
				continue
			path = os.path.join(PLAYLISTS_DIR, filtered_pls[idx - 1])
			icon_pl = icon('PLAYLIST')
			print(c(f"{icon_pl}Cargando playlist...", Colors.CYAN), end='', flush=True)
			try:
				channels = parse_m3u_file(path)
				check_icon = Icons.get_icon('CHECK')
				print(c(f" {check_icon} ({len(channels)} emisoras)", Colors.GREEN))
			except Exception as e:
				cross_icon = Icons.get_icon('CROSS')
				print(c(f" {cross_icon}", Colors.RED))
				print(f"{c('Error leyendo la playlist:', Colors.RED)} {e}")
				continue
			if not channels:
				print(c("La playlist no contiene entradas válidas.", Colors.RED))
				continue
			while True:
				print()
				pl_name = filtered_pls[idx - 1]
				pl_count = len(channels)
				header(f"Playlist: {pl_name} ({pl_count} emisoras)")
				print(f"  {c('1.', Colors.YELLOW)} Elegir canal")
				print(f"  {c('2.', Colors.YELLOW)} Reproducir canal aleatorio de esta playlist (r)")
				print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
				print(c(line(), Colors.BLUE))
				sub = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
				if sub in ('0', 'q'):
					break
				elif sub in ('2', 'r'):
					channels_sorted = sorted(channels, key=lambda ch: (ch.get('name') or ch.get('url') or '').lower(), reverse=not SORT_CHANNELS_ASC)
					attempts = 0
					while True:
						channel = random.choice(channels_sorted)
						name = channel.get('name') or channel.get('url')
						print(f"{c('Reproduciendo (aleatorio en playlist):', Colors.GREEN)} {name}")
						try:
							code = play_with_config(channel.get('url'), name, source=filtered_pls[idx - 1])
						except MpvNotFoundError as e:
							print(str(e))
							break
						if code != 0:
							attempts += 1
							if attempts <= 3:
								print(c("Fallo, probando otro canal...", Colors.YELLOW))
								continue
							else:
								print(c("Demasiados fallos, saliendo del aleatorio.", Colors.RED))
								break
						# Solo añadir al historial y ofrecer favoritos si la reproducción fue exitosa
						append_history(name, channel.get('url'), filtered_pls[idx - 1])
						offer_add_favorite(name, channel.get('url'), filtered_pls[idx - 1])
						result = prompt_yes_no("¿Reproducir otra emisora aleatoria de esta playlist?", default_yes=True)
						if result is None or not result:
							break
					continue
				elif sub == '1':
					select_and_play(channels, source=filtered_pls[idx - 1])
					continue
				else:
					print(c("Opción no válida.", Colors.RED))
			continue
		elif opt in ('2', 'r'):
			random_channel_from_all(pls)
			continue
		elif opt in ('3', 'u', 'l'):
			# Reproducir último canal
			entries = load_history()
			if entries:
				last_entry = entries[-1]
				name = last_entry.get('name') or last_entry.get('url') or ''
				url = last_entry.get('url') or ''
				if url:
					print(f"{c('Reproduciendo último canal:', Colors.GREEN)} {name}")
					try:
						play_with_config(url, name, source=last_entry.get('source'))
					except MpvNotFoundError as e:
						print(str(e))
					append_history(name, url, last_entry.get('source') or 'historial')
				else:
					print(c("No hay URL válida en la última entrada.", Colors.RED))
					input(c("Pulsa enter para continuar... ", Colors.CYAN))
			else:
				print(c("No hay historial.", Colors.YELLOW))
				input(c("Pulsa enter para continuar... ", Colors.CYAN))
			continue
		# BÚSQUEDA
		elif opt in ('4', '/'):
			global_search(pls)
			continue
		elif opt in ('5', 'b'):
			online_search_radio_browser()
			continue
		elif opt == '6' or opt == 'g':
			# Búsqueda en repositorio remoto
			remote_search_menu()
			continue
		# GESTIÓN
		elif opt == '7':
			favorites_menu()
			continue
		elif opt == '8':
			history_menu()
			continue
		elif opt in ('9', 's'):
			# Estadísticas
			stats_menu()
			continue
		# CONFIGURACIÓN Y DATOS
		elif opt in ('10', 'd'):
			# Descargar playlists desde GitHub
			download_playlists_menu()
			pls = list_playlists()  # Actualizar lista de playlists
			continue
		elif opt in ('11', 'c'):
			config_menu()
			continue
		else:
			print(c("Opción no válida.", Colors.RED))


if __name__ == '__main__':
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		print("\nInterrumpido.")
		sys.exit(130)
