#!/usr/bin/env bash
# Günlük akışın Python kısmı. İş Yatırım verisi (fetch_isyatirim.js çıktısı) hazır olduktan sonra çalışır.
# Kullanım: bash robot/calistir.sh <veri.json>
set -euo pipefail
cd "$(dirname "$0")/.."
VERI="${1:?veri.json yolu gerekli}"
TMP="$(mktemp -d)"
python3 robot/temel_analiz.py "$VERI" "$TMP" > /dev/null
GUN="$(python3 -c "import json,sys;from datetime import datetime;from zoneinfo import ZoneInfo;a=json.load(open(sys.argv[1]))['meta']['asOf'].replace('Z','+00:00');print(datetime.fromisoformat(a).astimezone(ZoneInfo('Europe/Istanbul')).date())" "$TMP/sonuc.json")"   # TR tarihi
cp "$TMP/sonuc.json" site/data/sonuc.json                 # sitenin okuduğu veri
mkdir -p site/data/gecmis && cp "$TMP/sonuc.json" "site/data/gecmis/$GUN.json"   # günlük arşiv
cp "$TMP/rapor.md" raporlar/son-rapor.md
python3 robot/build_site.py site/data/sonuc.json site > /dev/null   # site/hisse-takip.html (veri gömülü, yan panel için)
echo "tamam: $GUN"
