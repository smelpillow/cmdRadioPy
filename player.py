from __future__ import annotations
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional

class MpvNotFoundError(RuntimeError):
	pass


def find_mpv_executable() -> Optional[str]:
	# Busca mpv en PATH (mpv o mpv.exe)
	candidates: List[str] = ['mpv', 'mpv.exe']
	for name in candidates:
		found = shutil.which(name)
		if found:
			return found
	return None


def ensure_mpv() -> str:
	mpv = find_mpv_executable()
	if not mpv:
		raise MpvNotFoundError(
			"mpv no encontrado en PATH. Instálalo y asegúrate de que 'mpv' esté disponible.\n"
			"Windows: choco install mpv | Linux: sudo apt install mpv | macOS: brew install mpv"
		)
	return mpv


def play_url(url: str, extra_args: Optional[List[str]] = None) -> int:
	mpv = ensure_mpv()
	# Forzamos solo audio desactivando el vídeo.
	base_audio_only = ['--no-video', '--vid=no']
	args = [mpv, *base_audio_only, url]
	if extra_args:
		args.extend(extra_args)
	# Ejecuta mpv y espera a que termine. El usuario puede salir con 'q'.
	proc = subprocess.run(args)
	return proc.returncode


# ---- Mini UI controlando mpv por stdin ----

def _read_key_blocking() -> str:
	# Windows
	if os.name == 'nt':
		try:
			import msvcrt  # type: ignore
			while True:
				if msvcrt.kbhit():
					ch = msvcrt.getwch()
					return ch
				time.sleep(0.02)
		except Exception:
			return sys.stdin.read(1)
	# POSIX
	try:
		import termios, tty, select
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			while True:
				r, _, _ = select.select([sys.stdin], [], [], 0.05)
				if r:
					ch = sys.stdin.read(1)
					return ch
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
	except Exception:
		return sys.stdin.read(1)


def _print_controls(title: str) -> None:
	print()
	print(f"=== {title} ===")
	print("Controles: p=pausa/reanudar  +=vol+  -=vol-  m=mutear  q=salir")
	print("(Usando UI propia de cmdRadioPy; mpv corre en segundo plano)")
	print()


def _send_cmd(proc: subprocess.Popen, cmd: bytes) -> bool:
	try:
		if proc.stdin:
			proc.stdin.write(cmd)
			proc.stdin.flush()
			return True
		return False
	except (BrokenPipeError, OSError, ValueError):
		return False


# ---- IPC para OSD propia ----

def _ipc_server_path() -> str:
	"""Ruta para conectar desde Python al IPC de mpv."""
	if os.name == 'nt':
		return r"\\.\pipe\cmdradiopy-mpv"
	xdg = os.environ.get("XDG_RUNTIME_DIR")
	if xdg:
		return os.path.join(xdg, "cmdradiopy-mpv.sock")
	return "/tmp/cmdradiopy-mpv.sock"


def _ipc_mpv_server_arg() -> str:
	"""Valor para --input-ipc-server. En Windows mpv requiere la ruta completa del pipe (\\\\.\\pipe\\nombre)."""
	return _ipc_server_path()


def _ipc_connect(timeout_sec: float = 0.5) -> Optional[Any]:
	"""
	Conecta al IPC de mpv. Retorna un objeto conexión (socket o file-like) o None.
	"""
	path = _ipc_server_path()
	if os.name == 'nt':
		try:
			# Named pipe en Windows (bloquea hasta que mpv crea el pipe)
			f = open(path, "r+b", buffering=0)
			return f
		except (OSError, IOError):
			return None
	else:
		try:
			sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			sock.settimeout(timeout_sec)
			sock.connect(path)
			return sock
		except (OSError, socket.error):
			return None


def _ipc_send(conn: Any, msg: Dict[str, Any]) -> None:
	line = json.dumps(msg) + "\n"
	if hasattr(conn, "sendall"):
		conn.sendall(line.encode("utf-8"))
	else:
		conn.write(line.encode("utf-8"))
		conn.flush()


def _ipc_recv(conn: Any, timeout_sec: float = 0.4) -> Optional[Dict[str, Any]]:
	"""Lee una línea JSON de la conexión. Timeout solo en Unix (socket)."""
	try:
		if hasattr(conn, "recv"):
			conn.settimeout(timeout_sec)
			buf = b""
			while True:
				ch = conn.recv(1)
				if not ch:
					return None
				buf += ch
				if buf.endswith(b"\n"):
					break
			return json.loads(buf.decode("utf-8").strip())
		else:
			# Windows: pipe sin timeout nativo; usar PeekNamedPipe para evitar bloqueo
			def _win_pipe_available(pipe_conn: Any) -> int:
				try:
					import ctypes
					import ctypes.wintypes as wintypes
					import msvcrt  # type: ignore
					handle = msvcrt.get_osfhandle(pipe_conn.fileno())
					avail = wintypes.DWORD()
					res = ctypes.windll.kernel32.PeekNamedPipe(
						wintypes.HANDLE(handle),
						None,
						0,
						None,
						ctypes.byref(avail),
						None,
					)
					if res == 0:
						return 0
					return int(avail.value)
				except Exception:
					return 0

			deadline = time.monotonic() + timeout_sec
			while _win_pipe_available(conn) <= 0:
				if time.monotonic() >= deadline:
					return None
				time.sleep(0.02)

			buf = b""
			while True:
				ch = conn.read(1)
				if not ch:
					return None
				buf += ch
				if buf.endswith(b"\n"):
					break
			return json.loads(buf.decode("utf-8").strip())
	except (json.JSONDecodeError, OSError, socket.timeout, ValueError):
		return None


def _ipc_get_property(conn: Any, prop: str) -> Optional[Any]:
	"""Obtiene una propiedad de mpv vía IPC. Retorna el valor o None."""
	req_id = hash((prop, time.time())) % (2 ** 31)
	_ipc_send(conn, {"request_id": req_id, "command": ["get_property", prop]})
	# Ignorar eventos asíncronos hasta recibir la respuesta con el request_id.
	for _ in range(12):
		resp = _ipc_recv(conn)
		if not resp:
			return None
		if resp.get("request_id") == req_id and "data" in resp:
			return resp["data"]
	return None


def _ipc_show_text(conn: Any, text: str, duration_ms: int = 2000) -> None:
	"""Muestra un mensaje en la OSD de mpv. El texto puede incluir códigos ASS (color, negrita)."""
	try:
		_ipc_send(conn, {"command": ["show-text", text, duration_ms]})
	except Exception:
		pass


# --- Helpers ASS para formatear texto en la OSD de mpv (issue #3913) ---
# ASS usa &HBBGGRR& (BGR); ver https://github.com/mpv-player/mpv/issues/3913

def ass_color(text: str, r: int, g: int, b: int) -> str:
	"""Envuelve el texto en color ASS (r, g, b en 0-255)."""
	# ASS: \c&HBBGGRR& (BGR)
	bb, gg, rr = b & 0xFF, g & 0xFF, r & 0xFF
	return f"{{\\c&H{bb:02X}{gg:02X}{rr:02X}&}}{text}{{\\c&HFFFFFF&}}"


def ass_bold(text: str) -> str:
	"""Envuelve el texto en negrita ASS."""
	return "{\\b1}" + text + "{\\b0}"


def ass_color_bold(text: str, r: int, g: int, b: int) -> str:
	"""Texto en color y negrita."""
	return ass_bold(ass_color(text, r, g, b))


def _ipc_close(conn: Any) -> None:
	try:
		if hasattr(conn, "close"):
			conn.close()
	except Exception:
		pass


def _stdin_raw_enter() -> Optional[Any]:
	"""Activa modo raw en stdin (POSIX). Retorna atributos anteriores para restaurar."""
	if os.name != 'nt':
		try:
			import termios
			import tty
			fd = sys.stdin.fileno()
			old = termios.tcgetattr(fd)
			tty.setraw(fd)
			return old
		except Exception:
			pass
	return None


def _stdin_raw_leave(saved: Optional[Any]) -> None:
	if saved is not None and os.name != 'nt':
		try:
			import termios
			fd = sys.stdin.fileno()
			termios.tcsetattr(fd, termios.TCSADRAIN, saved)
		except Exception:
			pass


def _read_key_with_timeout(timeout_sec: float) -> str:
	"""Lee una tecla si está disponible; si no, retorna '' tras el timeout."""
	if os.name == 'nt':
		try:
			import msvcrt  # type: ignore
			deadline = time.monotonic() + timeout_sec
			while time.monotonic() < deadline:
				if msvcrt.kbhit():
					return msvcrt.getwch()
				time.sleep(0.02)
			return ""
		except Exception:
			return ""
	try:
		import select
		fd = sys.stdin.fileno()
		r, _, _ = select.select([sys.stdin], [], [], timeout_sec)
		if r:
			return sys.stdin.read(1)
		return ""
	except Exception:
		return ""


def play_url_with_custom_osd(
	url: str,
	station_name: Optional[str],
	play_mode: Optional[str] = None,
	source: Optional[str] = None,
	extra_args: Optional[List[str]] = None,
	draw_osd_cb: Optional[Callable[[Dict[str, Any], bool], None]] = None,
	log_cb: Optional[Callable[[str], None]] = None,
) -> int:
	"""
	Reproduce una URL con mpv en segundo plano y OSD propia en terminal.
	draw_osd_cb(state, first_time) se llama con el estado (volume, mute, pause, media_title, time_pos, duration, station_name, play_mode, channel_url, source).
	log_cb(message) opcional para registrar mensajes (ej. fallo IPC).
	"""
	mpv = ensure_mpv()
	ipc_path = _ipc_server_path()
	ipc_mpv_arg = _ipc_mpv_server_arg()
	base_args = [
		"--no-video", "--vid=no",
		"--really-quiet", "--quiet",
		"--input-terminal=no",
		"--input-ipc-server=" + ipc_mpv_arg,
	]
	# En Windows mpv sale antes de crear el pipe si recibe la URL en la línea de comandos
	# o si usa --input-file=- (p. ej. EOF en stdin). Arrancar con --idle sin stdin, conectar
	# al IPC y enviar todos los comandos por IPC.
	use_idle_then_load = os.name == "nt"
	if use_idle_then_load:
		base_args.append("--idle")
	else:
		base_args.append("--input-file=-")
	args = [mpv, *base_args]
	if extra_args:
		args.extend(extra_args)
	if not use_idle_then_load:
		args.append(url)

	proc = subprocess.Popen(args, stdin=subprocess.PIPE)
	conn = None
	saved_term = _stdin_raw_enter()
	ipc_path = _ipc_server_path()

	try:
		# Esperar a que mpv cree el socket/pipe (streams pueden tardar más)
		for attempt in range(40):
			try:
				time.sleep(0.25)
			except KeyboardInterrupt:
				raise
			conn = _ipc_connect(timeout_sec=0.4)
			if conn is not None:
				break
		if conn is not None and use_idle_then_load:
			try:
				_ipc_send(conn, {"command": ["loadfile", url, "replace"]})
				time.sleep(0.3)
			except Exception:
				pass
		if conn is None:
			# Si arrancamos con --idle (sin stdin) y no conectamos, no podemos cargar URL; terminar
			if use_idle_then_load and proc.poll() is None:
				try:
					proc.kill()
					proc.wait(timeout=2)
				except Exception:
					pass
				return proc.returncode if proc.returncode is not None else 1
			try:
				print("No se pudo conectar al IPC de mpv. Reproducción sin OSD (controles: p, +, -, m, q).")
				print(f"Ruta IPC: {ipc_path}")
			except Exception:
				pass
			if log_cb:
				try:
					log_cb(f"IPC no conectado. Ruta: {ipc_path}")
				except Exception:
					pass
			while proc.poll() is None:
				key = _read_key_with_timeout(0.3)
				if key and key.lower() == "q":
					_send_cmd(proc, b"quit\n")
					break
				if key:
					k = key.lower()
					if k == "p":
						_send_cmd(proc, b"cycle pause\n")
					elif k == "+":
						_send_cmd(proc, b"add volume 5\n")
					elif k == "-":
						_send_cmd(proc, b"add volume -5\n")
					elif k == "m":
						_send_cmd(proc, b"cycle mute\n")
			try:
				proc.wait(timeout=5)
			except Exception:
				proc.kill()
			return proc.returncode or 0

		first_draw = True
		while True:
			if proc.poll() is not None:
				return proc.returncode or 0

			key = _read_key_with_timeout(0.3)
			if key:
				k = key.lower()
				if k == "q":
					try:
						_ipc_send(conn, {"command": ["quit"]})
					except Exception:
						pass
					try:
						proc.wait(timeout=5)
					except Exception:
						pass
					return 0
				if k == "p":
					try:
						_ipc_send(conn, {"command": ["cycle", "pause"]})
					except Exception:
						pass
					time.sleep(0.1)
					state = _gather_mpv_state(conn, station_name, play_mode, url, source)
					if state.get("pause"):
						_ipc_show_text(conn, ass_color_bold("Pausado", 255, 200, 0), 1500)
					else:
						_ipc_show_text(conn, ass_color("Reproduciendo", 0, 255, 0), 1500)
				elif k == "+":
					try:
						_ipc_send(conn, {"command": ["add", "volume", 5]})
					except Exception:
						pass
					time.sleep(0.1)
					state = _gather_mpv_state(conn, station_name, play_mode, url, source)
					vol = state.get("volume", 0)
					_ipc_show_text(conn, ass_color_bold(f"Vol: {vol}%", 0, 255, 0), 1500)
				elif k == "-":
					try:
						_ipc_send(conn, {"command": ["add", "volume", -5]})
					except Exception:
						pass
					time.sleep(0.1)
					state = _gather_mpv_state(conn, station_name, play_mode, url, source)
					vol = state.get("volume", 0)
					_ipc_show_text(conn, ass_color_bold(f"Vol: {vol}%", 0, 255, 0), 1500)
				elif k == "m":
					try:
						_ipc_send(conn, {"command": ["cycle", "mute"]})
					except Exception:
						pass
					time.sleep(0.1)
					state = _gather_mpv_state(conn, station_name, play_mode, url, source)
					if state.get("mute"):
						_ipc_show_text(conn, ass_color_bold("Mute", 255, 100, 0), 1500)
					else:
						_ipc_show_text(conn, ass_color("Sonido", 0, 255, 0), 1500)
				elif k == "f":
					# Tecla 'f' para toggle favorito (se maneja en draw_osd_cb con key param)
					if draw_osd_cb:
						state = _gather_mpv_state(conn, station_name, play_mode, url, source)
						draw_osd_cb(state, first_draw, key="f")
						first_draw = False
			if draw_osd_cb:
				state = _gather_mpv_state(conn, station_name, play_mode, url, source)
				draw_osd_cb(state, first_draw)
				first_draw = False
			else:
				# Timeout: actualizar OSD
				if draw_osd_cb:
					state = _gather_mpv_state(conn, station_name, play_mode, url, source)
					draw_osd_cb(state, first_draw)
					first_draw = False
	finally:
		_stdin_raw_leave(saved_term)
		_ipc_close(conn)
		try:
			if proc.poll() is None:
				proc.terminate()
				proc.wait(timeout=2)
		except Exception:
			pass
	return proc.returncode or 0


def _gather_mpv_state(
	conn: Any,
	station_name: Optional[str],
	play_mode: Optional[str],
	channel_url: Optional[str] = None,
	source: Optional[str] = None,
) -> Dict[str, Any]:
	"""Recoge volumen, mute, pause, media-title, time-pos, duration y opcionalmente codec/bitrate desde mpv IPC."""
	state: Dict[str, Any] = {
		"volume": 0,
		"mute": False,
		"pause": False,
		"media_title": "",
		"time_pos": 0.0,
		"duration": None,
		"station_name": station_name or "",
		"play_mode": play_mode or "",
		"channel_url": channel_url or "",
		"source": source or "",
		"audio_codec": None,
		"audio_bitrate_kbps": None,
		"samplerate_hz": None,
	}
	try:
		v = _ipc_get_property(conn, "volume")
		if v is not None:
			state["volume"] = int(v) if isinstance(v, (int, float)) else 0
		m = _ipc_get_property(conn, "mute")
		state["mute"] = bool(m)
		p = _ipc_get_property(conn, "pause")
		state["pause"] = bool(p)
		# En streams de radio, el título suele venir de ICY (Icecast/Shoutcast).
		icy = _ipc_get_property(conn, "metadata/icy-title")
		if icy is not None and str(icy).strip():
			state["media_title"] = str(icy).strip()
		else:
			t = _ipc_get_property(conn, "media-title")
			state["media_title"] = (str(t).strip() if t is not None else "") or ""
		tp = _ipc_get_property(conn, "time-pos")
		state["time_pos"] = float(tp) if tp is not None else 0.0
		d = _ipc_get_property(conn, "duration")
		state["duration"] = float(d) if d is not None else None
	except Exception:
		pass
	try:
		params = _ipc_get_property(conn, "audio-params")
		if isinstance(params, dict):
			fmt = params.get("format")
			if fmt is not None:
				state["audio_codec"] = str(fmt).upper()
			sr = params.get("samplerate")
			if sr is not None:
				state["samplerate_hz"] = int(sr)
	except Exception:
		pass
	try:
		br = _ipc_get_property(conn, "audio-bitrate")
		if br is not None:
			# mpv suele devolver bits/s
			bps = int(br) if isinstance(br, (int, float)) else 0
			if bps > 0:
				state["audio_bitrate_kbps"] = round(bps / 1000)
	except Exception:
		pass
	return state


def play_url_with_ui(name: str, url: str) -> int:
	mpv = ensure_mpv()
	base_args = [
		'--no-video', '--vid=no',
		'--really-quiet', '--quiet',
		'--input-terminal=no',
		'--input-file=-',  # comandos por stdin
	]
	args = [mpv, *base_args, url]
	proc = subprocess.Popen(args, stdin=subprocess.PIPE)
	try:
		_print_controls(name or url)
		paused = False
		muted = False
		while True:
			if proc.poll() is not None:
				# mpv terminó
				return proc.returncode or 0
			key = _read_key_blocking()
			if not key:
				continue
			k = key.lower()
			if k == 'q':
				_send_cmd(proc, b"quit\n")
				try:
					proc.wait(timeout=5)
				except Exception:
					pass
				return 0
			elif k == 'p':
				# toggle pause
				paused = not paused
				if not _send_cmd(proc, b"cycle pause\n"):
					return 0
			elif k == '+':
				# subir volumen 5
				if not _send_cmd(proc, b"add volume 5\n"):
					return 0
			elif k == '-':
				# bajar volumen 5
				if not _send_cmd(proc, b"add volume -5\n"):
					return 0
			elif k == 'm':
				muted = not muted
				if not _send_cmd(proc, b"cycle mute\n"):
					return 0
			# Ignorar otras teclas
	finally:
		# No hacemos flush al finalizar para evitar errores en Windows si el pipe ya cerró
		pass
