from __future__ import annotations
import os
import shutil
import subprocess
import sys
import time
from typing import List, Optional


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
