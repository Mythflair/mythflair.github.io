#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$ROOT/.zisai-theme-backup-$STAMP"
mkdir -p "$BACKUP"
for p in layouts/index.html layouts/partials/header.html layouts/_partials/header.html layouts/partials/extend_head.html layouts/_partials/extend_head.html assets/css/extended/zisai.css static/css/zisai.css static/favicon.ico static/images/zisai; do
  if [ -e "$ROOT/$p" ]; then mkdir -p "$BACKUP/$(dirname "$p")"; cp -a "$ROOT/$p" "$BACKUP/$p"; fi
done
mkdir -p "$ROOT/layouts/partials" "$ROOT/layouts/_partials" "$ROOT/assets/css/extended" "$ROOT/static/images" "$ROOT/static/css"
cp "$HERE/layouts/index.html" "$ROOT/layouts/index.html"
cp "$HERE/layouts/partials/header.html" "$ROOT/layouts/partials/header.html"
cp "$HERE/layouts/_partials/header.html" "$ROOT/layouts/_partials/header.html"
cp "$HERE/layouts/partials/extend_head.html" "$ROOT/layouts/partials/extend_head.html"
cp "$HERE/layouts/_partials/extend_head.html" "$ROOT/layouts/_partials/extend_head.html"
cp "$HERE/assets/css/extended/zisai.css" "$ROOT/assets/css/extended/zisai.css"
cp "$HERE/static/css/zisai.css" "$ROOT/static/css/zisai.css"
cp "$HERE/static/favicon.ico" "$ROOT/static/favicon.ico"
rm -rf "$ROOT/static/images/zisai"
cp -a "$HERE/static/images/zisai" "$ROOT/static/images/zisai"
echo "ZISAI theme overlay installed. Backup: $BACKUP"
echo "Next: merge zisai-config-snippet.toml into hugo.toml, then run hugo server -D."
