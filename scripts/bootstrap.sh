#!/bin/sh
# Baut /volume2/docker/RansomLook (oder $TARGET) aus Fork + Overlay dieses Repos neu auf.
# Aufruf (als root auf dem Synology):  sh bootstrap.sh [/volume2/docker/RansomLook]
set -eu
TARGET="${1:-/volume2/docker/RansomLook}"
FORK="https://github.com/icepaule/RansomLook.git"
UPSTREAM_COMMIT="de8d93d"          # Stand, auf dem der Overlay entwickelt wurde
HERE="$(cd "$(dirname "$0")/.." && pwd)"

[ -e "$TARGET" ] && { echo "$TARGET existiert bereits - abbrechen"; exit 1; }
git clone "$FORK" "$TARGET"
cd "$TARGET"
git checkout "$UPSTREAM_COMMIT"

# 1) Aenderungen an Upstream-Dateien
git apply "$HERE/deploy/patches/0001-local-modifications.patch"

# 2) neue Dateien
cp "$HERE/deploy/docker-compose.yml"          docker-compose.yml
cp "$HERE/deploy/entrypoint.sh"               entrypoint.sh
cp "$HERE/deploy/ofelia.ini"                  ofelia.ini
cp "$HERE/deploy/fetch_telegram_groups.py"    fetch_telegram_groups.py
cp "$HERE/deploy/tools/import_public.py"      tools/import_public.py
chmod +x entrypoint.sh tools/import_public.py

# 3) Config aus Vorlage - ECHTE WERTE DANACH EINTRAGEN
cp "$HERE/deploy/config/generic.json.example" config/generic.json
mkdir -p data source/screenshots

echo
echo "Fertig. Jetzt: $TARGET/config/generic.json editieren (siehe docs/02-wiederherstellung.md),"
echo "dann: cd $TARGET && docker compose build && docker compose up -d"
