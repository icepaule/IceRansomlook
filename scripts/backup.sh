#!/bin/sh
# Sicherung der NICHT rekonstruierbaren Laufzeitdaten. Auf dem Synology als root:
#   sh backup.sh [/volume2/docker/RansomLook] [/volume1/NetBackup/ransomlook]
# Enthaelt Secrets (config/generic.json) -> Archiv NICHT in ein oeffentliches Repo legen!
set -eu
SRC="${1:-/volume2/docker/RansomLook}"
DST="${2:-/volume1/NetBackup/ransomlook}"
TS="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DST"

# Redis-Snapshot erzwingen (save 3600 1 laeuft sonst nur stuendlich)
docker exec ransomlook-redis redis-cli -s /ransomlook/cache/cache.sock BGSAVE >/dev/null 2>&1 || true
sleep 15

tar czf "$DST/ransomlook-$TS.tar.gz" -C "$SRC" \
    config data cache/dump.rdb docker-compose.yml ofelia.ini entrypoint.sh \
    fetch_telegram_groups.py ransomlook/sharedutils.py tools \
    $( [ -f "$SRC/telegram_session.session" ] && echo telegram_session.session )
# Screenshots (~250 MB) sind per scrape/screen neu erzeugbar -> bewusst nicht enthalten.
ls -1t "$DST"/ransomlook-*.tar.gz | tail -n +15 | xargs -r rm -f   # 14 Staende behalten
echo "OK: $DST/ransomlook-$TS.tar.gz"
