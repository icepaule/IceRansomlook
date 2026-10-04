# 06 – Betrieb und Troubleshooting

## Backup

`scripts/backup.sh` sichert Config, Daten, Redis-Dump, Compose/Tools (ohne Screenshots, ohne `source/`). Es erzwingt vorher einen Redis-`BGSAVE` und behält 14 Stände.

```sh
sh scripts/backup.sh /volume2/docker/RansomLook /volume1/NetBackup/ransomlook
```

> Stand der Doku: Das Skript ist **noch nicht im DSM-Aufgabenplaner eingetragen und nicht im Echtbetrieb getestet.** Empfehlung: DSM → Aufgabenplaner → täglich als root. Das Archiv enthält Secrets – nicht in öffentliche Ablagen legen.

## Updates

- **Container neu bauen:** `docker compose build --pull && docker compose up -d`.
- **Upstream aktualisieren:** Fork syncen, neuen Commit auschecken, `git apply --check deploy/patches/0001-local-modifications.patch`. Schlägt der Patch fehl, Änderungen manuell übertragen und Patch neu erzeugen (`git diff > …`). Das ist bisher nicht durchgeführt.

## Monitoring

- Uptime Kuma: HTTP-Check auf `https://ransomlook.mpauli.de` (Redirect auf SSO = „lebt“) bzw. intern `http://10.10.0.186:8083/api/groups`.
- Wichtig: Timeout für `/` mindestens 30 s setzen, die Startseite braucht ca. 7–8 s.

## Bekannte Fallen

| Symptom | Ursache | Lösung |
|---|---|---|
| Startseite lädt nur „000“/Timeout bei `curl -m 5` | Startseite ist langsam (~7,5 s); `/api/*` ist schnell | Timeout erhöhen |
| DSM-Mail „Container stopped unexpectedly“ | Container-Befehl endet | Endlosschleife im Compose (ist umgesetzt) |
| Startseite/Statistik wirft Fehler | Nicht-Dict-Einträge in Redis | gepatchte `sharedutils.py` (ro-Mount) prüfen |
| Redis-Daten voller Fehlertexte | Export ohne Key liefert HTTP 401 + `{"message":…}` | gepatchtes `import_from_instance.py`; `import_public.py` nutzen |
| `docker compose up` bricht ab: Netz `misp-docker_default` fehlt | MISP-Stack nicht gestartet | MISP starten oder Netz anlegen/Block entfernen |
| Viele `ERR_TIMED_OUT` im Log | Onion-Seiten offline/langsam | normal |
| Redis startet nicht | falsche Rechte in `cache/` | `chown -R 999 cache` |
| Alt-Doku nennt Port 8888 | veraltet | richtig ist **8083** |

## Nützliche Befehle

```sh
docker compose logs --tail 50 ransomlook
docker exec ransomlook-redis redis-cli -s /ransomlook/cache/cache.sock -n 2 DBSIZE
docker exec ransomlook-ransomlook-1 poetry run tools/import_public.py groups   # nur Gruppen nachziehen
docker exec ransomlook-ransomlook-1 poetry run tools/malpedia.py
```
