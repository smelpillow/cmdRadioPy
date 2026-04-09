$ErrorActionPreference = 'Stop'

$packageName = 'cmdradiopy'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$packageArgs = @{
  packageName    = $packageName
  unzipLocation  = $toolsDir
  url64bit       = 'https://github.com/smelpillow/cmdRadioPy/releases/download/v1.2.6/cmdradiopy-win64.zip'
  checksum64     = 'ff7785f39521902273120b4d5815dd1333f640bd46155cabe3e5b8611551f5e1'
  checksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

Write-Host 'Instalador Chocolatey listo para v1.2.6. Verifica que la URL del release publicado coincida con esta versión y hash.'
