$ErrorActionPreference = 'Stop'

$packageName = 'cmdradiopy'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$packageArgs = @{
  packageName    = $packageName
  unzipLocation  = $toolsDir
  url64bit       = 'https://github.com/smelpillow/cmdRadiopy/releases/download/v1.2.0/cmdradiopy-win64.zip'
  checksum64     = 'REPLACE_WITH_SHA256'
  checksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

Write-Host 'Plantilla inicial Chocolatey. Ajustar URL/hash y binario final.'
