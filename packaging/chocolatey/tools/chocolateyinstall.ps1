$ErrorActionPreference = 'Stop'

$packageName = 'cmdradiopy'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$packageArgs = @{
  packageName    = $packageName
  unzipLocation  = $toolsDir
  url64bit       = 'https://github.com/smelpillow/cmdRadioPy/releases/download/v1.2.7/cmdradiopy-win64.zip'
  checksum64     = '7d6643dddacbb629ac4d04e9b0908763d0142cd04700bf0ec576b29b845da7c5'
  checksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

Write-Host 'Instalador Chocolatey listo para v1.2.7. Verifica que la URL del release publicado coincida con esta versión y hash.'
