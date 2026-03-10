$ErrorActionPreference = 'Stop'

$packageName = 'cmdradiopy'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$packageArgs = @{
  packageName    = $packageName
  unzipLocation  = $toolsDir
  url64bit       = 'https://github.com/smelpillow/cmdRadiopy/releases/download/v1.2.1/cmdradiopy-win64.zip'
  checksum64     = 'fbf23651a4f9fadda0e2f37e122f50ecfc2ef70b6963da82a862c946c7538ac7'
  checksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

Write-Host 'Instalador Chocolatey listo para v1.2.1. Verifica que la URL del release publicado coincida con esta versión y hash.'
