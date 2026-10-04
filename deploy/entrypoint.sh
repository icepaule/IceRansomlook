#!/bin/bash
# Warten bis Redis bereit ist
echo "⏳ Waiting for Redis..."
until [ -S /ransomlook/cache/cache.sock ]; do
  echo "Redis socket not ready yet..."
  sleep 1
done

# Führe den Import durch
echo "✅ Redis ready. Importing groups..."
poetry run tools/import_from_instance.py || echo "⚠️ Import failed"
poetry run tools/3rdparty.py || echo "⚠️ Import failed"
poetry run tools/malpedia.py || echo "⚠️ Import failed"

# Starte standardmäßig den Webserver oder den gewünschten Prozess
exec "$@"

