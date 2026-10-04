# 03 – Änderungen gegenüber Upstream

Basis: Fork `icepaule/RansomLook` auf Commit **`de8d93d`**. Alle Änderungen liegen als Patch in `deploy/patches/0001-local-modifications.patch` plus neue Dateien in `deploy/`.

> Der aktuelle `main` des Forks ist neuer als `de8d93d` (ca. 76 Dateien Unterschied) und enthält diese Änderungen **nicht**. Wer auf neueren Upstream wechselt, muss den Patch prüfen und ggf. neu schneiden.

| Datei | Änderung | Grund |
|---|---|---|
| `Dockerfile` | `net-tools` installiert; `ENTRYPOINT /entrypoint.sh`; `poetry run update --yes`; `CMD poetry run start` | Warten auf Redis-Socket, Erst-Update beim Build, Diagnose (`netstat`) |
| `entrypoint.sh` (neu) | wartet auf `cache.sock`, ruft `import_from_instance.py`, `3rdparty.py`, `malpedia.py` auf, dann `exec "$@"` | sauberer Start-Ablauf |
| `cache/cache.conf` | `unixsocket /ransomlook/cache/cache.sock`, `daemonize no` | Socket-Pfad im Container, Redis muss im Vordergrund laufen |
| `docker-compose.yml` | Redis-Service, Endlosschleife statt Einmal-Lauf, DNS 1.1.1.1/8.8.8.8, Port 8083, Netz `misp-docker_default`, ro-Mounts für `tools/` und `sharedutils.py`, Ofelia | Container beendete sich nach `parse` → Restart-Schleife und DSM-Mail „stopped unexpectedly“ |
| `ransomlook/sharedutils.py` | Typ-/Leerprüfungen in `statsgroup`, `run_data_viz`, `hostcount*`, `onlinecount` | Einträge in Redis, die keine Dicts/Listen sind (z. B. gespeicherte Fehlerantworten), ließen Statistik/Startseite abstürzen |
| `tools/import_from_instance.py` | Key optional über `RANSOMLOOK_API_KEY`, HTTP-Fehler und Fehler-JSON werden **nicht** nach Redis geschrieben | `ransomlook.io/api/export/*` verlangt seit 2026 einen Key (HTTP 401); früher wurde die Fehlermeldung als Daten gespeichert |
| `tools/import_public.py` (neu) | importiert fehlende Gruppen, Märkte, Posts und Leaks über die **öffentlichen** Endpunkte | Ersatz für `/api/export/*` ohne Key; ersetzt auch `tools/breach.py` (leak-lookup.com liefert nichts mehr) |
| `tools/malpedia.py` | `profile` robust zusammenführen (Duplikate, fehlendes Feld) | Absturz bei Gruppen ohne `profile` |
| `tools/import_telegram.py` | `strip()` und Überspringen zu kurzer Zeilen | numerische Telethon-IDs sind nicht scrapebar |
| `ofelia.ini` (neu) | Job `import-telegram` stündlich | Telegram-Kanäle nachziehen |
| `fetch_telegram_groups.py` (neu) | Liste der beigetretenen Telegram-Gruppen exportieren | Quelle für `data/telegram.txt` |

## Zum Export-Key

Nur `GET /api/export/{db}` braucht einen Key (Swagger: `securityDefinitions.apikey`, Header `Authorization`). Es gibt keine Selbstregistrierung; Keys vergeben die Maintainer (Anfrage über GitHub-Issue im Upstream-Repo oder Mastodon `@Ransomlook` auf social.circl.lu). Alle übrigen rund 50 Endpunkte sind offen. Diese Instanz kommt ohne Key aus.
