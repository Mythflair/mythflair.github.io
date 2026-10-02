param([string]$SiteRoot = ".")
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = Join-Path $SiteRoot ".zisai-theme-backup-$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$targets = @(
  "layouts/index.html","layouts/partials/header.html","layouts/_partials/header.html",
  "layouts/partials/extend_head.html","layouts/_partials/extend_head.html",
  "assets/css/extended/zisai.css","static/css/zisai.css","static/favicon.ico","static/images/zisai"
)
foreach($rel in $targets){
  $src = Join-Path $SiteRoot $rel
  if(Test-Path $src){
    $dst = Join-Path $Backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -Recurse -Force $src $dst
  }
}
@("layouts/partials","layouts/_partials","assets/css/extended","static/images","static/css") | ForEach-Object {
  New-Item -ItemType Directory -Force -Path (Join-Path $SiteRoot $_) | Out-Null
}
Copy-Item -Force (Join-Path $Here "layouts/index.html") (Join-Path $SiteRoot "layouts/index.html")
Copy-Item -Force (Join-Path $Here "layouts/partials/header.html") (Join-Path $SiteRoot "layouts/partials/header.html")
Copy-Item -Force (Join-Path $Here "layouts/_partials/header.html") (Join-Path $SiteRoot "layouts/_partials/header.html")
Copy-Item -Force (Join-Path $Here "layouts/partials/extend_head.html") (Join-Path $SiteRoot "layouts/partials/extend_head.html")
Copy-Item -Force (Join-Path $Here "layouts/_partials/extend_head.html") (Join-Path $SiteRoot "layouts/_partials/extend_head.html")
Copy-Item -Force (Join-Path $Here "assets/css/extended/zisai.css") (Join-Path $SiteRoot "assets/css/extended/zisai.css")
Copy-Item -Force (Join-Path $Here "static/css/zisai.css") (Join-Path $SiteRoot "static/css/zisai.css")
Copy-Item -Force (Join-Path $Here "static/favicon.ico") (Join-Path $SiteRoot "static/favicon.ico")
$imgTarget = Join-Path $SiteRoot "static/images/zisai"
if(Test-Path $imgTarget){ Remove-Item -Recurse -Force $imgTarget }
Copy-Item -Recurse -Force (Join-Path $Here "static/images/zisai") $imgTarget
Write-Host "ZISAI theme overlay installed. Backup: $Backup"
Write-Host "Next: merge zisai-config-snippet.toml into hugo.toml, then run: hugo server -D"
