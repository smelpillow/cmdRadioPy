# Windows packaging

Este directorio contiene el scaffold inicial para generar el artefacto Windows.

## Objetivo

Generar un zip de release con esta estructura:

```text
cmdradiopy-win64.zip
└── cmdradiopy/
    ├── cmdradiopy.exe
    └── playlists/
```

## Requisitos

- Python 3.9+
- `mpv` instalado en PATH en la máquina destino
- PyInstaller disponible en el entorno de build

Instalación recomendada para build local:

```powershell
pip install ".[build-win]"
```

## Build local

Desde la raíz del repo:

```powershell
./packaging/windows/build-win64.ps1
```

El script:

1. Genera `dist/cmdradiopy/cmdradiopy.exe`
2. Incluye `playlists/` dentro del artefacto
3. Crea `dist/cmdradiopy-win64.zip`
4. Calcula el SHA256 final

## Pendiente después del primer build

- Subir `cmdradiopy-win64.zip` a GitHub Releases
- Actualizar `packaging/scoop/cmdradiopy.json`
- Actualizar `packaging/chocolatey/tools/chocolateyinstall.ps1`
- Verificar `cmdradiopy.exe --version`