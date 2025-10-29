from __future__ import annotations
import os
import sys
import random
import shutil
import json
import time
from typing import List, Dict, Optional

from m3u_parser import parse_m3u_file
from player import play_url, MpvNotFoundError


BASE_DIR = os.path.dirname(__file__)
PLAYLISTS_DIR = os.path.join(BASE_DIR, 'playlists')
FAVORITES_FILE = os.path.join(BASE_DIR, 'favorites.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# Estado de configuración (editable en tiempo de ejecución)
CURRENT_PAGE_SIZE = 20
SORT_PLAYLISTS_ASC = True
SORT_CHANNELS_ASC = True
CONFIG: Dict[str, Optional[str]] = {}


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


def prompt_yes_no(message: str, default_yes: bool = True) -> bool:
	"""Devuelve True si la respuesta es afirmativa."""
	default_hint = 'S/n' if default_yes else 's/N'
	while True:
		resp = input(c(f"{message} ({default_hint}): ", Colors.CYAN)).strip().lower()
		if not resp:
			return default_yes
		if resp in ('s', 'si', 'sí', 'y', 'yes'):
			return True
		if resp in ('n', 'no'):
			return False
		print(c("Entrada no válida. Responde con s/n.", Colors.RED))


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
	query = input(c("Texto a buscar (nombre de emisora): ", Colors.CYAN)).strip()
	country = input(c("Filtrar país (código o nombre, opcional): ", Colors.CYAN)).strip()
	language = input(c("Filtrar idioma (opcional): ", Colors.CYAN)).strip()
	bitrate = input(c("Bitrate mínimo (kbps, opcional): ", Colors.CYAN)).strip()
	if not query:
		print(c("Búsqueda vacía.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
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
		print(f"  {c('r', Colors.GREEN)} Aleatorio entre resultados  |  {c('0', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		sel = input(c("Pulsa 'r' para aleatorio o enter para listar: ", Colors.CYAN)).strip().lower()
		if sel == 'q':
			return
		if sel == 'r':
			attempts = 0
			while True:
				pool = results
				if not pool:
					print(c("No hay resultados para aleatorio.", Colors.RED))
					return
				item = random.choice(pool)
				print(f"{c('Reproduciendo (online aleatorio):', Colors.GREEN)} {item['name']} {dim(item['source'])}")
				try:
					code = play_with_config(item['url'])
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
				append_history(item['name'], item['url'], 'online')
				offer_add_favorite(item['name'], item['url'], 'online')
				if not prompt_yes_no("¿Reproducir otra emisora aleatoria online?", default_yes=True):
					return
			continue
		idx = paginated_select(labels, "Resultados online")
		if idx in (0, -1):
			return
		item = results[idx - 1]
		print(f"{c('Reproduciendo:', Colors.GREEN)} {item['name']} {dim(item['source'])}")
		try:
			play_with_config(item['url'])
		except MpvNotFoundError as e:
			print(str(e))
		append_history(item['name'], item['url'], 'online')
		offer_add_favorite(item['name'], item['url'], 'online')


def play_with_config(url: str) -> int:
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
		code = play_url(url, extra_args=extra)
		if code == 0:
			return 0
		if attempt >= retries:
			return code
		print(c(f"Fallo de reproducción (código {code}). Reintentando...", Colors.YELLOW))
		attempt += 1
		time.sleep(max(0, delay))


def append_history(name: str, url: str, source: Optional[str]) -> None:
	entry = {
		'name': name or url,
		'url': url,
		'source': source or '',
		'ts': int(time.time()),
	}
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
	# Limitar a últimos 200
	if len(hist) > 200:
		hist = hist[-200:]
	try:
		with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
			json.dump(hist, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


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


def paginated_select(options: List[str], title: str, page_size: int = None) -> int:
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
		header(f"{title}  {dim(f'(página {page + 1}/{pages})')}")

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
			print(f"  {c('n', Colors.GREEN)} Siguiente página    {c('p', Colors.GREEN)} Página anterior    {c('g', Colors.GREEN)} Ir a página")
		print(f"  {c('s', Colors.GREEN)} Alternar orden (A↔Z)    {c('/', Colors.GREEN)} Filtrar")
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
	if prompt_yes_no("¿Añadir a favoritos?", default_yes=False):
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
		header("Favoritos")
		print(f"  {c('e', Colors.GREEN)} Exportar favoritos  |  {c('i', Colors.GREEN)} Importar favoritos  |  {c('r', Colors.GREEN)} Aleatorio  |  {c('0', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		cmd = input(c("Pulsa 'e'/'i'/'r' o enter para listar: ", Colors.CYAN)).strip().lower()
		if cmd in ('0', 'q'):
			return
		if cmd == 'e':
			path = input(c("Ruta destino (ej. favorites_export.json): ", Colors.CYAN)).strip()
			if not path:
				print(c("Ruta inválida.", Colors.RED))
			else:
				try:
					with open(path, 'w', encoding='utf-8') as f:
						json.dump(favs, f, ensure_ascii=False, indent=2)
					print(c("Favoritos exportados.", Colors.GREEN))
				except Exception as e:
					print(c(f"Error exportando: {e}", Colors.RED))
			continue
		if cmd == 'i':
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
		if cmd == 'r':
			while True:
				fav = random.choice(favs)
				name = fav.get('name') or fav.get('url') or ''
				print(f"{c('Reproduciendo (aleatorio favoritos):', Colors.GREEN)} {name}")
				try:
					play_with_config(fav.get('url') or '')
				except MpvNotFoundError as e:
					print(str(e))
					break
				append_history(name, fav.get('url') or '', 'favoritos')
				if not prompt_yes_no("¿Reproducir otro favorito aleatorio?", default_yes=True):
					break
			continue
		idx = paginated_select(options, "Favoritos")
		if idx == 0 or idx == -1:
			return
		fav = favs[idx - 1]
		# Submenú del favorito
		while True:
			header(f"Favorito: {fav.get('name')}")
			print(f"  {c('1.', Colors.YELLOW)} Reproducir")
			print(f"  {c('2.', Colors.YELLOW)} Eliminar")
			print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
			print(c(line(), Colors.BLUE))
			opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
			if opt in ('0', 'q'):
				break
			elif opt == '1':
				try:
					play_url(fav.get('url'))
				except MpvNotFoundError as e:
					print(str(e))
			elif opt == '2':
				# Eliminar favorito
				favs = [x for x in favs if (x.get('url') or '').strip() != (fav.get('url') or '').strip()]
				save_favorites(favs)
				print(c("Eliminado de favoritos.", Colors.GREEN))
				break
			else:
				print(c("Opción no válida.", Colors.RED))


def global_search(playlists: List[str]) -> None:
	header("Búsqueda global en playlists")
	query = input(c("Texto a buscar (en nombre/url): ", Colors.CYAN)).strip().lower()
	if not query:
		print(c("Búsqueda vacía.", Colors.YELLOW))
		input(c("Pulsa enter para volver... ", Colors.CYAN))
		return
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
		print(f"  {c('r', Colors.GREEN)} Aleatorio entre resultados  |  {c('0', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		sel = input(c("Pulsa 'r' para aleatorio o enter para listar: ", Colors.CYAN)).strip().lower()
		if sel == 'q':
			return
		if sel == 'r':
			# Bucle aleatorio sobre resultados + oferta favoritos
			while True:
				item = random.choice(results)
				print(f"{c('Reproduciendo (aleatorio):', Colors.GREEN)} {item['name']} {dim(f'[{item['source']}]')}")
				try:
					play_with_config(item['url'])
				except MpvNotFoundError as e:
					print(str(e))
					return
				append_history(item['name'], item['url'], item['source'])
				offer_add_favorite(item['name'], item['url'], item['source'])
				if not prompt_yes_no("¿Reproducir otra emisora aleatoria de los resultados?", default_yes=True):
					return
			continue
		# Selección paginada
		idx = paginated_select(labels, "Resultados de búsqueda")
		if idx == 0 or idx == -1:
			return
		item = results[idx - 1]
		print(f"{c('Reproduciendo:', Colors.GREEN)} {item['name']} {dim(f'[{item['source']}]')}")
		try:
			play_with_config(item['url'])
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
		header("Selección de canales")
		print(f"  {c('r', Colors.GREEN)} Aleatorio entre resultados  |  {c('f', Colors.GREEN)} Favorito por número  |  {c('0', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		selection = input(c("Pulsa 'r' aleatorio, 'f' favorito o enter para listar: ", Colors.CYAN)).strip().lower()
		if selection == 'q':
			return
		if selection == 'r':
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
					code = play_with_config(url)
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
				append_history(name, url, source)
				offer_add_favorite(name, url, source)
				if not prompt_yes_no("¿Reproducir otra emisora aleatoria de los resultados?", default_yes=True):
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
		print(f"{c('Reproduciendo:', Colors.GREEN)} {name}")
		try:
			play_with_config(url)
		except MpvNotFoundError as e:
			print(str(e))
			return
		append_history(name, url, source)
		# Ofrecer favoritos tras reproducir selección directa
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
			code = play_with_config(channel.get('url'))
		except MpvNotFoundError as e:
			print(str(e))
			return
		if code != 0:
			print(c("Fallo, probando otra emisora...", Colors.YELLOW))
			continue
		append_history(name, channel.get('url'), pl)
		if not prompt_yes_no("¿Reproducir otra emisora aleatoria global?", default_yes=True):
			break

def print_ascii_logo() -> None:
	# Recuadro centrado con el nombre exacto
	title = "cmdRadioPy"
	sub = "Reproductor M3U para terminal"
	inner_w = max(len(title), len(sub)) + 4
	w = term_width()
	box_w = min(inner_w + 2, max(w - 4, inner_w + 2))
	pad_left = max(0, (w - box_w) // 2)

	top = "╔" + "═" * (box_w - 2) + "╗"
	bot = "╚" + "═" * (box_w - 2) + "╝"
	space_line = "║" + " " * (box_w - 2) + "║"

	def center_text(s: str) -> str:
		inner = box_w - 2
		pad = max(0, (inner - len(s)) // 2)
		rem = max(0, inner - len(s) - pad)
		return "║" + (" " * pad) + s + (" " * rem) + "║"

	lines = [top, space_line, center_text(title), center_text(sub), space_line, bot]
	for ln in lines:
		print(" " * pad_left + c(ln, Colors.CYAN))
	print()

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
		else:
			print(c("Opción no válida.", Colors.RED))

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
		header("Historial (recientes)")
		print(f"  {c('e', Colors.GREEN)} Exportar historial  |  {c('i', Colors.GREEN)} Importar historial  |  {c('r', Colors.GREEN)} Aleatorio  |  {c('0', Colors.YELLOW)} Volver (q)")
		print(c(line(), Colors.BLUE))
		cmd = input(c("Pulsa 'e'/'i'/'r' o enter para listar: ", Colors.CYAN)).strip().lower()
		if cmd in ('0', 'q'):
			return
		if cmd == 'e':
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
		if cmd == 'i':
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
		if cmd == 'r':
			while True:
				entry = random.choice(entries)
				name = entry.get('name') or entry.get('url') or ''
				print(f"{c('Reproduciendo (aleatorio historial):', Colors.GREEN)} {name}")
				try:
					play_with_config(entry.get('url') or '')
				except MpvNotFoundError as e:
					print(str(e))
					break
				append_history(name, entry.get('url') or '', entry.get('source') or 'historial')
				if not prompt_yes_no("¿Reproducir otro historial aleatorio?", default_yes=True):
					break
			continue
		idx = paginated_select(labels, "Historial (recientes)")
		if idx in (0, -1):
			return
		if idx == -2 or idx == -3:
			continue
		entry = list(reversed(entries))[idx - 1]
		print(f"{c('Reproduciendo desde historial:', Colors.GREEN)} {entry.get('name')}")
		try:
			play_with_config(entry.get('url') or '')
		except MpvNotFoundError as e:
			print(str(e))
		append_history(entry.get('name') or '', entry.get('url') or '', entry.get('source') or '')


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
		print(f"  {c('1.', Colors.YELLOW)} Mostrar canales")
		print(f"  {c('2.', Colors.YELLOW)} Buscar en canales (/)")
		print(f"  {c('3.', Colors.YELLOW)} Reproducción aleatoria (r)")
		print(f"  {c('4.', Colors.YELLOW)} Buscar online (Radio Browser) (b)")
		print(f"  {c('5.', Colors.YELLOW)} Favoritos")
		print(f"  {c('6.', Colors.YELLOW)} Historial")
		print(f"  {c('7.', Colors.YELLOW)} Configuración (c)")
		print(f"  {c('8.', Colors.YELLOW)} Salir (q)")
		print(c(line(), Colors.BLUE))
		opt = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
		if opt in ('8', 'q'):
			return 0
		elif opt in ('3', 'r'):
			random_channel_from_all(pls)
			continue
		elif opt in ('4', 'b'):
			online_search_radio_browser()
			continue
		elif opt in ('2', '/'):
			global_search(pls)
			continue
		elif opt == '6':
			history_menu()
			continue
		elif opt == '5':
			favorites_menu()
			continue
		elif opt == '7':
			config_menu()
			continue
		elif opt == '1':
			pls = list_playlists()
			# Filtro para playlists
			pl_filter = ''
			while True:
				filtered_pls = [p for p in pls if pl_filter in p.lower()] if pl_filter else pls
				idx = paginated_select(filtered_pls, "Playlists detectadas")
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
			try:
				channels = parse_m3u_file(path)
			except Exception as e:
				print(f"{c('Error leyendo la playlist:', Colors.RED)} {e}")
				continue
			if not channels:
				print(c("La playlist no contiene entradas válidas.", Colors.RED))
				continue
			while True:
				print()
				header(f"Playlist: {filtered_pls[idx - 1]}")
				print(f"  {c('1.', Colors.YELLOW)} Elegir canal")
				print(f"  {c('2.', Colors.YELLOW)} Reproducir canal aleatorio de esta playlist (r)")
				print(f"  {c('0.', Colors.YELLOW)} Volver (q)")
				print(c(line(), Colors.BLUE))
				sub = input(c("Selecciona: ", Colors.CYAN)).strip().lower()
				if sub in ('0', 'q'):
					break
				elif sub in ('2', 'r'):
					channels_sorted = sorted(channels, key=lambda ch: (ch.get('name') or ch.get('url') or '').lower(), reverse=not SORT_CHANNELS_ASC)
					while True:
						channel = random.choice(channels_sorted)
						name = channel.get('name') or channel.get('url')
						print(f"{c('Reproduciendo (aleatorio en playlist):', Colors.GREEN)} {name}")
						try:
							play_with_config(channel.get('url'))
						except MpvNotFoundError as e:
							print(str(e))
							break
						append_history(name, channel.get('url'), filtered_pls[idx - 1])
						# Ofrecer favoritos también aquí
						offer_add_favorite(name, channel.get('url'), filtered_pls[idx - 1])
						if not prompt_yes_no("¿Reproducir otra emisora aleatoria de esta playlist?", default_yes=True):
							break
					continue
				elif sub == '1':
					select_and_play(channels, source=filtered_pls[idx - 1])
					continue
				else:
					print(c("Opción no válida.", Colors.RED))
			continue
		else:
			print(c("Opción no válida.", Colors.RED))


if __name__ == '__main__':
	sys.exit(main())
