#!/usr/bin/env python3
# Import aus den OEFFENTLICHEN Endpunkten von ransomlook.io (ohne API-Key).
# Ersatz fuer /api/export/*, das seit 2026 einen Key verlangt.
#  - Gruppen (db0) + deren Posts (db2): nur Gruppen, die lokal noch fehlen
#  - Maerkte/Foren (db3) + Posts (db2): nur fehlende
#  - Leaks (db4): nur fehlende IDs (Ersatz fuer tools/breach.py, leak-lookup.com liefert nichts mehr)
# Screenshots der Gegenseite werden nicht uebernommen (lokal nicht vorhanden).
import json
import sys
import time

import redis
import requests

from ransomlook.default import get_socket_path

API = 'https://www.ransomlook.io/api'
session = requests.Session()
session.headers['User-Agent'] = 'RansomLook-local-import'


def get(path: str):  # type: ignore
    for attempt in range(3):
        try:
            r = session.get(f'{API}/{path}', timeout=300)
            if r.status_code == 200:
                return r.json()
            print(f'  {path}: HTTP {r.status_code}')
            if r.status_code in (401, 403, 404):
                return None
        except (requests.RequestException, ValueError) as e:
            print(f'  {path}: {e}')
        time.sleep(5 * (attempt + 1))
    return None


def clean_meta(meta: dict) -> dict:
    for loc in meta.get('locations', []):
        loc.pop('screen', None)  # base64-Screenshot der Remote-Instanz, lokal irrelevant
    return meta


def clean_post(post: dict) -> dict:
    post['screen'] = 'None'
    return post


def merge_posts(red2: redis.Redis, name: str, remote_posts: list) -> int:
    raw = red2.get(name)
    local = json.loads(raw) if raw else []
    if not isinstance(local, list):
        local = []
    titles = {p.get('post_title') for p in local if isinstance(p, dict)}
    added = 0
    for p in remote_posts:
        if isinstance(p, dict) and isinstance(p.get('discovered'), str) and p.get('post_title') not in titles:
            local.append(clean_post(p))
            titles.add(p.get('post_title'))
            added += 1
    if added:
        red2.set(name, json.dumps(local))
    return added


def import_entities(kind: str, list_path: str, item_path: str, db: int) -> None:
    names = get(list_path)
    if not isinstance(names, list):
        print(f'{kind}: Liste nicht abrufbar')
        return
    red = redis.Redis(unix_socket_path=get_socket_path('cache'), db=db)
    red2 = redis.Redis(unix_socket_path=get_socket_path('cache'), db=2)
    existing = {k.decode() for k in red.keys()}
    missing = [n for n in names if isinstance(n, str) and n not in existing]
    print(f'{kind}: remote {len(names)}, lokal {len(existing)}, fehlend {len(missing)}')
    new_posts = 0
    for i, name in enumerate(missing, 1):
        data = get(f'{item_path}/{requests.utils.quote(name, safe="")}')
        if not (isinstance(data, list) and len(data) == 2 and isinstance(data[0], dict)):
            continue
        meta, posts = data
        red.set(name, json.dumps(clean_meta(meta)))
        if isinstance(posts, list):
            new_posts += merge_posts(red2, name, posts)
        if i % 50 == 0:
            print(f'  {i}/{len(missing)}')
        time.sleep(0.3)
    print(f'{kind}: {len(missing)} neu, {new_posts} Posts uebernommen')


def import_leaks() -> None:
    leaks = get('leaks/leaks')
    if not isinstance(leaks, list):
        print('Leaks: Liste nicht abrufbar')
        return
    red = redis.Redis(unix_socket_path=get_socket_path('cache'), db=4)
    existing = {k.decode() for k in red.keys()}
    missing = [l for l in leaks if isinstance(l, dict) and str(l.get('id')) not in existing]
    print(f'Leaks: remote {len(leaks)}, lokal {len(existing)}, fehlend {len(missing)}')
    for i, leak in enumerate(missing, 1):
        data = get(f'leaks/leaks/{leak["id"]}')
        if isinstance(data, dict) and data.get('name'):
            red.set(str(leak['id']), json.dumps(data))
        if i % 500 == 0:
            print(f'  {i}/{len(missing)}')
        time.sleep(0.1)
    print(f'Leaks: {len(missing)} neu')


if __name__ == '__main__':
    what = sys.argv[1:] or ['groups', 'markets', 'leaks']
    if 'groups' in what:
        import_entities('Gruppen', 'groups', 'group', 0)
    if 'markets' in what:
        import_entities('Maerkte', 'markets', 'market', 3)
    if 'leaks' in what:
        import_leaks()
