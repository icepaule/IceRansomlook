# 07 – Secrets-Checkliste (ohne Werte)

Werte stehen **nicht** in diesem Repo. Diese Liste sagt, was für einen Neuaufbau nötig ist und wo es herkommt.

| Geheimnis | Verwendet in | Woher neu beschaffen |
|---|---|---|
| Malpedia-API-Key | `config/generic.json` → `malpedia` | Malpedia-Account → Profil |
| MISP-Auth-Key (Heim-MISP) | `generic.json` → `misp.apikey`; Feed-Key-Datei `heim-misp.key` | MISP → Administration → Auth Keys |
| MISP-Key `misp.thesoc.de` | `thesoc.key` (Feed, 2. Ziel) | liefert der Betreiber, **steht noch aus** |
| SMTP-Zugang | `generic.json` → `email_smtp_auth` | Mail-Server (Relay) |
| Telegram API-ID/-Hash + Session | `.env`, `telegram_session.session` | my.telegram.org, Session per Login neu erzeugen |
| ransomlook.io Export-Key (optional) | Env `RANSOMLOOK_API_KEY` | Maintainer-Anfrage; **nicht nötig** |
| Authentik-/Hetzner-/HAProxy-Zugänge | `sso-gate.sh` | Passwortmanager |

Regeln: Secrets nie in Compose-Dateien, nie ins Repo. `.gitignore` schließt `generic.json`, `*.key`, `.env`, `telegram_session*`, `state.json` und `targets.json` aus.
