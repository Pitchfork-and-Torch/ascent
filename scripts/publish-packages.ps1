# Publish ASCENT packages when credentials are present.
# - PyPI: set TWINE_USERNAME=__token__ and TWINE_PASSWORD=pypi-...  OR  ~/.pypirc
# - npm public: npm login  then  npm publish packages/ascent-js --access public
# - GitHub Packages npm: uses GH_TOKEN (Pitchfork-and-Torch)
# ASCII hyphens only.

param(
  [switch]$PyPI,
  [switch]$NpmPublic,
  [switch]$NpmGitHub,
  [switch]$ReleaseAssetsOnly,
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "pyproject.toml"))) {
  $Root = $PSScriptRoot
  if (-not (Test-Path (Join-Path $Root "pyproject.toml"))) {
    $Root = (Get-Location).Path
  }
}
Set-Location $Root
Write-Host "Root: $Root"

function Build-Python {
  if (Test-Path dist) { Remove-Item -Recurse -Force dist }
  if (Test-Path build) { Remove-Item -Recurse -Force build }
  py -3 -m pip install -U build twine -q
  py -3 -m build
  Get-ChildItem dist | Format-Table Name, Length
}

function Publish-PyPI {
  if (-not $env:TWINE_PASSWORD -and -not (Test-Path "$env:USERPROFILE\.pypirc")) {
    if (-not $env:PYPI_TOKEN) {
      throw "No PyPI credentials. Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=pypi-... or create ~/.pypirc"
    }
    $env:TWINE_USERNAME = "__token__"
    $env:TWINE_PASSWORD = $env:PYPI_TOKEN
  }
  if (-not $env:TWINE_USERNAME) { $env:TWINE_USERNAME = "__token__" }
  py -3 -m twine check dist/*
  py -3 -m twine upload dist/*
}

function Publish-NpmGitHub {
  $pkgDir = Join-Path $Root "packages\ascent-js"
  Push-Location $pkgDir
  try {
    node scripts/sync-from-site.js
    $token = $env:GH_TOKEN
    if (-not $token) { $token = $env:GITHUB_TOKEN }
    if (-not $token) {
      $token = (gh auth token 2>$null)
    }
    if (-not $token) { throw "No GH_TOKEN for GitHub Packages" }
    # GitHub Packages requires scope matching owner
    $pkg = Get-Content package.json -Raw | ConvertFrom-Json
    $pkg.name = "@Pitchfork-and-Torch/ascent"
    $pkg.publishConfig = @{ registry = "https://npm.pkg.github.com" }
    ($pkg | ConvertTo-Json -Depth 10) | Set-Content package.json -Encoding utf8
    @"
@Pitchfork-and-Torch:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=$token
"@ | Set-Content .npmrc -Encoding ascii
    npm publish --access restricted
  } finally {
    Pop-Location
  }
}

function Publish-NpmPublic {
  $pkgDir = Join-Path $Root "packages\ascent-js"
  Push-Location $pkgDir
  try {
    node scripts/sync-from-site.js
    npm whoami | Out-Null
    npm publish --access public
  } finally {
    Pop-Location
  }
}

function Attach-ReleaseAssets {
  $ver = (Select-String -Path (Join-Path $Root "pyproject.toml") -Pattern 'version\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
  $tag = "v$ver"
  gh release upload $tag (Get-ChildItem dist\*.whl, dist\*.tar.gz).FullName `
    -R Pitchfork-and-Torch/ascent --clobber
  Write-Host "Attached dist assets to release $tag"
}

if (-not $SkipBuild) { Build-Python }

if ($ReleaseAssetsOnly -or (-not $PyPI -and -not $NpmPublic -and -not $NpmGitHub)) {
  Attach-ReleaseAssets
}

if ($PyPI) { Publish-PyPI }
if ($NpmGitHub) { Publish-NpmGitHub }
if ($NpmPublic) { Publish-NpmPublic }

Write-Host "Done."
