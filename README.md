# IceRansomlook

Vollständige Dokumentation und Overlay für die selbst gehostete **[RansomLook](https://github.com/RansomLook/RansomLook)**-Instanz im Heimnetz (Synology „SynNAS“), inklusive stündlichem **MISP-Feed** neuer Leak-Site-Posts.

Ziel: Geht die Instanz kaputt, lässt sie sich mit diesem Repo **Schritt für Schritt** wieder aufbauen – ohne dass Zugangsdaten im Repo stehen.

| | |
|---|---|
| Fork | <https://github.com/icepaule/RansomLook> |
| Upstream-Stand der Instanz | Commit `de8d93d` („Fix mastodon validation“, März 2025) |
| Host | Synology `10.10.0.186`, Verzeichnis `/volume2/docker/RansomLook` |
| Web/API intern | `http://10.10.0.186:8083` (ohne Login!) |
| Extern | `https://ransomlook.mpauli.de` (Authentik SSO + 2FA) |
| MISP-Feed | `/opt/ransomlook-misp/` auf NUC-HA, stündlich |

## Inhalt

| Datei | Zweck |
|---|---|
| [docs/01-architektur.md](docs/01-architektur.md) | Komponenten, Datenfluss, Ports, Redis-DBs |
| [docs/02-wiederherstellung.md](docs/02-wiederherstellung.md) | **Disaster Recovery, Schritt für Schritt** |
| [docs/03-aenderungen-gegenueber-upstream.md](docs/03-aenderungen-gegenueber-upstream.md) | Was am Fork-Stand geändert wurde und warum |
| [docs/04-misp-feed.md](docs/04-misp-feed.md) | RansomLook → MISP (Heim-MISP, später misp.thesoc.de) |
| [docs/05-sso-und-extern.md](docs/05-sso-und-extern.md) | Authentik, DNS, Zertifikat, HAProxy |
| [docs/06-betrieb-und-troubleshooting.md](docs/06-betrieb-und-troubleshooting.md) | Backup, Monitoring, bekannte Fallen |
| [docs/07-secrets-checkliste.md](docs/07-secrets-checkliste.md) | Welche Geheimnisse es gibt und wo sie liegen (ohne Werte) |
| `deploy/` | Dateien, die auf das Synology kommen (Compose, Patch, Tools, Config-Vorlage) |
| `misp-feed/` | Feed-Skript, Cron, Target-Vorlage |
| `scripts/` | `bootstrap.sh` (Neuaufbau), `backup.sh` (Sicherung) |

## Schnellstart Neuaufbau

```sh
git clone https://github.com/icepaule/IceRansomlook.git
sh IceRansomlook/scripts/bootstrap.sh /volume2/docker/RansomLook
# danach config/generic.json mit echten Werten füllen und bauen/starten:
# siehe docs/02-wiederherstellung.md
```

## Sicherheit dieses Repos

Enthalten sind nur Code, Vorlagen und Doku. **Nicht** enthalten: `config/generic.json` (SMTP, MISP-Key, Malpedia-Key), `telegram_session.session`, API-Keys, Passwörter, Redis-Dump. Interne RFC1918-Adressen stehen bewusst in der Doku.
