# 01 – Architektur

RansomLook crawlt Leak-Sites von Ransomware-Gruppen (über Tor), wertet sie mit gruppenspezifischen Parsern aus und stellt Gruppen, Posts, Märkte, Krypto-Wallets und Erpresserbriefe per Web-UI und REST-API bereit.

## Überblick

```mermaid
flowchart LR
  subgraph SYN["Synology SynNAS 10.10.0.186 (Container Manager)"]
    direction TB
    RL["ransomlook<br/>Ubuntu 22.04 + Tor + Playwright<br/>gunicorn :8000 (10 Worker)<br/>Port 8083 → 8000"]
    RD[("ransomlook-redis<br/>redis:7, nur Unix-Socket<br/>dump.rdb ~150 MB")]
    OF["ofelia<br/>Cron für Docker<br/>stündlich: import_telegram"]
    RL <-->|"cache.sock"| RD
    OF -->|"docker exec"| RL
  end
  TOR(("Tor-Netz<br/>Leak-Sites .onion"))
  IO["www.ransomlook.io<br/>öffentliche API"]
  MAL["Malpedia API"]
  RL --> TOR
  RL -->|"import_public.py"| IO
  RL -->|"malpedia.py"| MAL
  MISPD[("misp-core<br/>Docker-Netz misp-docker_default")]
  RL -. "gleiches Docker-Netz,<br/>publish=false" .-> MISPD

  subgraph NUC["NUC-HA"]
    FEED["ransomlook-misp.py<br/>Cron :17 stündlich"]
  end
  IO -->|"/api/recent/200"| FEED
  FEED -->|"POST /events/add"| HMISP[("Heim-MISP<br/>192.168.178.171:7443")]
  FEED -.->|"später"| TMISP[("misp.thesoc.de")]

  USER(("Browser")) -->|"https://ransomlook.mpauli.de"| EDGE["pfSense HAProxy"]
  EDGE --> AK["Authentik Embedded Outpost<br/>SSO + 2FA"]
  AK -->|"http://192.168.178.171:8083"| RL
```

## Container

| Container | Image | Aufgabe |
|---|---|---|
| `ransomlook-ransomlook-1` | lokal gebaut (`ubuntu:22.04`) | Tor, Scraper/Parser, Website (gunicorn) |
| `ransomlook-redis` | `redis:7` | Datenhaltung, **nur Unix-Socket** (`port 0`), Konfig `cache/cache.conf` |
| `ransomlook-ofelia-1` | `mcuadros/ofelia:latest` | Cron-Job `import-telegram` stündlich per `docker exec` |

Docker-Netze: `ransomlook_default` (intern) und das **externe** Netz `misp-docker_default` (muss existieren, sonst startet Compose nicht – gehört zum MISP-Stack auf dem Synology).

## Verzeichnislayout (`/volume2/docker/RansomLook`)

| Pfad | Inhalt | Persistent/Sichern? |
|---|---|---|
| `config/generic.json` | Konfiguration inkl. Secrets | **ja, geheim** |
| `cache/` | `cache.conf`, `dump.rdb` (Redis-Daten), Socket/PID | **ja** (`dump.rdb`) |
| `data/` | z. B. `telegram.txt` (Kanal-Liste) | ja |
| `source/` | gecachte Roh-HTML der Leak-Sites (~40 MB) | nein, neu erzeugbar |
| `source/screenshots/` | Screenshots (~250 MB) | nein, neu erzeugbar |
| `tools/` | Hilfsskripte, **read-only** in den Container gemountet | aus Repo |
| `ransomlook/sharedutils.py` | gepatchte Datei, read-only gemountet | aus Repo |
| `telegram_session.session` | Telethon-Login | **geheim**, nur falls Telegram genutzt wird |

## Redis-Datenbanken

| DB | Inhalt |
|---|---|
| 0 | Gruppen (Metadaten, Standorte/`locations`) |
| 2 | Posts je Gruppe/Markt |
| 3 | Märkte/Foren |
| 4 | Leaks (Data Breaches) |
| 5 | Telegram-Kanäle |
| 6 | Telegram-Nachrichten |

Persistenz: `save 3600 1` (Snapshot, wenn in einer Stunde ≥1 Änderung), **kein** AOF. Ein Crash verliert also bis zu eine Stunde.

## Zyklus im Container

Der Container-Befehl (`docker-compose.yml`) startet Tor und das Backend (`poetry run start`) und läuft danach in einer Dauerschleife (Intervall 2 h):

```mermaid
sequenceDiagram
  participant C as Container-Loop
  participant IO as ransomlook.io (öffentlich)
  participant MP as Malpedia
  participant T as Tor / Leak-Sites
  participant R as Redis
  loop alle 7200 s
    C->>IO: import_public.py (fehlende Gruppen/Märkte/Leaks)
    IO-->>R: neue Einträge (db0/2/3/4)
    C->>MP: malpedia.py (Beschreibung/Profile)
    C->>T: scrape (HTML holen)
    C->>R: parse (Posts schreiben)
    C->>T: screen (Screenshots)
    C->>R: notes, cryptocur
  end
```

Fehler einzelner Schritte werden nur geloggt (`|| echo "... failed"`), die Schleife läuft weiter. Viele `net::ERR_TIMED_OUT` im Log sind bei Onion-Seiten normal.

## Ports

| Port | Wo | Zweck |
|---|---|---|
| 8083/tcp | Synology-Host | Web-UI + `/api/*` (→ Container 8000) |
| 8000/tcp | Container | gunicorn |
| Unix-Socket | `cache/cache.sock` | Redis (kein TCP) |

> Hinweis: Die Startseite `/` braucht unter Last ca. 7–8 s, `/api/*` antwortet in unter 1 s. Das ist kein Ausfall.
