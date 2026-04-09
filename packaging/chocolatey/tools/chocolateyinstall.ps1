$ErrorActionPreference = 'Stop'

$packageName = 'cmdradiopy'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$packageArgs = @{
  packageName    = $packageName
  unzipLocation  = $toolsDir
  url64bit       = 'https://github.com/smelpillow/cmdRadiopy/releases/download/v1.2.2/cmdradiopy-win64.zip'
  checksum64     = 'dd4f84fb17fac83d723a6fd337ded6b9f90d19ae6f0bf82d8b98f87ef06a2f22'
  checksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

Write-Host 'Instalador Chocolatey listo para v1.2.2. Verifica que la URL del release publicado coincida con esta versión y hash.'
