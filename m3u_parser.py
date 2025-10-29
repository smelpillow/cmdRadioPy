from __future__ import annotations
from typing import List, Dict, Optional


def parse_m3u(content: str) -> List[Dict[str, Optional[str]]]:
	entries: List[Dict[str, Optional[str]]] = []
	current_name: Optional[str] = None
	current_attrs: Dict[str, str] = {}

	for raw_line in content.splitlines():
		line = raw_line.strip()
		if not line:
			continue

		if line.startswith('#EXTINF'):
			# Example: #EXTINF:-1 tvg-id="id" group-title="News",Channel Name
			# Split header and display name
			try:
				header, display_name = line.split(',', 1)
			except ValueError:
				header, display_name = line, ''

			current_name = display_name.strip() or None
			current_attrs = {}

			# Extract key="value" attributes
			# Simple scan to avoid heavy regex
			tmp = header
			while '="' in tmp:
				before, rest = tmp.split('="', 1)
				key = before.strip().split()[-1]
				if '"' in rest:
					value, tmp = rest.split('"', 1)
					current_attrs[key] = value
				else:
					break
			continue

		if line.startswith('#'):
			# Ignore other directives
			continue

		# If we get here, it's a URL line
		url = line
		name = current_name or url
		entries.append({
			'name': name,
			'url': url,
			'attrs': current_attrs.copy() if current_attrs else {},
		})

		# Reset for next entry
		current_name = None
		current_attrs = {}

	return entries


def parse_m3u_file(path: str) -> List[Dict[str, Optional[str]]]:
	with open(path, 'r', encoding='utf-8', errors='ignore') as f:
		content = f.read()
	return parse_m3u(content)
