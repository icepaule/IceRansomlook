import os
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat
from dotenv import load_dotenv

# 🔁 .env einlesen
load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID", 0))
api_hash = os.getenv("TELEGRAM_API_HASH", "")
session_file = 'telegram_session'

if not api_id or not api_hash:
    raise RuntimeError("❌ TELEGRAM_API_ID oder TELEGRAM_API_HASH fehlt in .env!")

output_file = 'data/telegram.txt'
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with TelegramClient(session_file, api_id, api_hash) as client:
    print("🔍 Lade beigetretene Gruppen...")
    dialogs = client.get_dialogs()

    group_links = []

    for dialog in dialogs:
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)) and getattr(entity, 'megagroup', True):
            try:
                invite_link = client.export_chat_invite_link(entity)
                group_links.append(invite_link)
            except Exception:
                if hasattr(entity, 'username') and entity.username:
                    group_links.append(f"https://t.me/{entity.username}")
                elif hasattr(entity, 'id'):
                    group_links.append(str(entity.id))

    with open(output_file, 'w') as f:
        for link in sorted(set(group_links)):
            f.write(link + '\n')

    print(f"✅ {len(group_links)} Gruppen gespeichert in {output_file}")

