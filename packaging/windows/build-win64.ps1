param(
	[string]$PythonExe = 'python'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$distRoot = Join-Path $repoRoot 'dist'
$workRoot = Join-Path $repoRoot 'build\pyinstaller'
$releaseDir = Join-Path $distRoot 'cmdradiopy'
$zipPath = Join-Path $distRoot 'cmdradiopy-win64.zip'
$playlistsDir = Join-Path $repoRoot 'playlists'

Push-Location $repoRoot
try {
	$version = (& $PythonExe -c "from version import APP_VERSION; print(APP_VERSION)").Trim()
	if (-not $version) {
		throw 'No se pudo leer APP_VERSION desde version.py'
	}

	& $PythonExe -m PyInstaller --version *> $null
	if ($LASTEXITCODE -ne 0) {
		throw 'PyInstaller no está disponible en el entorno actual. Instala el extra build-win.'
	}

	if (Test-Path $releaseDir) {
		Remove-Item $releaseDir -Recurse -Force
	}
	if (Test-Path $zipPath) {
		Remove-Item $zipPath -Force
	}
	if (-not (Test-Path $playlistsDir)) {
		throw "No se encontró el directorio de playlists en $playlistsDir"
	}

	& $PythonExe -m PyInstaller `
		--noconfirm `
		--clean `
		--onedir `
		--name cmdradiopy `
		--distpath $distRoot `
		--workpath $workRoot `
		--specpath $workRoot `
		--add-data "${playlistsDir};playlists" `
		main.py

	$exePath = Join-Path $releaseDir 'cmdradiopy.exe'
	if (-not (Test-Path $exePath)) {
		throw "No se generó el ejecutable esperado en $exePath"
	}

	Compress-Archive -Path $releaseDir -DestinationPath $zipPath -CompressionLevel Optimal
	$sha256 = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()

	Write-Host "Build Windows completado para v$version"
	Write-Host "Artefacto: $zipPath"
	Write-Host "SHA256:   $sha256"
	Write-Host 'Recuerda actualizar Scoop y Chocolatey con la URL y hash reales.'
}
finally {
	Pop-Location
}