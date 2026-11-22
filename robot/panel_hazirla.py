#!/usr/bin/env python3
"""Claude yan paneli (artifact) için sitenin çok dosyalı bir kopyasını hazırlar.

Yan panelde Cloudflare Worker (/api/altin) olmadığı için canlı altın fiyatı yerine
site/data/altin-gecmis.json içindeki son Altınkaynak kaydı api/altin.json olarak konur.
Sayfalar, içerik ve tasarım canlı siteyle aynıdır.

Kullanım: python3 robot/panel_hazirla.py [cikti_klasoru]   (varsayılan: reponun yanındaki hisse-panel klasörü; /tmp altı yayınlanamaz)
Çıktıdaki tüm dosyalar artifact'e aynı göreli yollarla yayınlanır (dosyalar.txt listesi).
"""
import json, os, shutil, sys
from datetime import datetime

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(KOK, "site")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(KOK), "hisse-panel")
DOSYALAR = ["index.html", "altin.html", "hisseler.html", "stil.css", "ortak.js", "icon.svg",
            "data/sonuc.json", "data/altin-gecmis.json"]
ADLAR = {"GA": "Gram altın", "C": "Çeyrek altın", "B_T": "22 ayar hurda", "XAUUSD": "Ons altın"}

shutil.rmtree(OUT, ignore_errors=True)
for d in DOSYALAR:
    os.makedirs(os.path.dirname(os.path.join(OUT, d)), exist_ok=True)
    shutil.copyfile(os.path.join(SITE, d), os.path.join(OUT, d))

# Sayfalar canlı fiyatı api/altin yerine api/altin.json'dan okusun
for sayfa in ["index.html", "altin.html", "hisseler.html"]:
    p = os.path.join(OUT, sayfa)
    s = open(p, encoding="utf-8").read()
    s = s.replace('<script src="ortak.js"></script>', '<script>window.HT_API="api/altin.json"</script>\n<script src="ortak.js"></script>')
    open(p, "w", encoding="utf-8").write(s)

# Son Altınkaynak kaydından (kaynak alanı olmayan) api/altin.json üret
kayitlar = json.load(open(os.path.join(SITE, "data/altin-gecmis.json"), encoding="utf-8"))["kayitlar"]
gercek = [k for k in kayitlar if not k.get("kaynak")]
kalemler = []
for kod, ad in ADLAR.items():
    son = next((k for k in reversed(gercek) if k.get(kod)), None)
    if son:
        t = datetime.fromisoformat(son["t"]).strftime("%d.%m.%Y %H:%M:00")
        kalemler.append({"kod": kod, "ad": ad, "alis": son[kod][0], "satis": son[kod][1], "guncelleme": t})
os.makedirs(os.path.join(OUT, "api"), exist_ok=True)
json.dump({"kaynak": "Altınkaynak (son kayıt)", "kalemler": kalemler}, open(os.path.join(OUT, "api/altin.json"), "w", encoding="utf-8"), ensure_ascii=False)

liste = DOSYALAR + ["api/altin.json"]
open(os.path.join(OUT, "dosyalar.txt"), "w").write("\n".join(liste) + "\n")
print(OUT)
for d in liste:
    print(" ", d)
