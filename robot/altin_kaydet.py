#!/usr/bin/env python3
"""Altınkaynak'ın herkese açık altın servisinden gram altın, çeyrek ve 22 ayar hurda fiyatlarını
site/data/altin-gecmis.json dosyasına ekler (grafik için geçmiş). GitHub Actions saatlik çalıştırır.

Servis: https://static.altinkaynak.com/public/Gold  (bkz. https://www.altinkaynak.com/Araclar/Servisler)
Kullanım: python3 robot/altin_kaydet.py [site/data/altin-gecmis.json] [--girdi gold.json]
"""
import json, os, sys, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

KAYNAK = "https://static.altinkaynak.com/public/Gold"
KODLAR = ["GA", "C", "B_T", "XAUUSD"]  # gram altın, çeyrek, 22 ayar hurda, ons (USD)
SAKLA_GUN = 400                     # en fazla ~13 aylık geçmiş tut
TR = ZoneInfo("Europe/Istanbul")

def sayi(s):
    try:
        return float(str(s).replace(".", "").replace(",", "."))
    except ValueError:
        return None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    yol = args[0] if args else "site/data/altin-gecmis.json"
    if "--girdi" in sys.argv:
        liste = json.load(open(sys.argv[sys.argv.index("--girdi") + 1], encoding="utf-8"))
    else:
        req = urllib.request.Request(KAYNAK, headers={"Accept": "application/json", "User-Agent": "hissetakip/1.0 (kisisel takip)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            liste = json.load(r)
    by = {x["Kod"]: x for x in liste}
    eksik = [k for k in KODLAR if k not in by]
    if eksik:
        sys.exit(f"Serviste bulunamadı: {eksik}")
    zaman = datetime.strptime(by["GA"]["GuncellenmeZamani"], "%d.%m.%Y %H:%M:%S").replace(tzinfo=TR)
    kayit = {"t": zaman.isoformat(timespec="minutes")}
    for k in KODLAR:
        kayit[k] = [sayi(by[k]["Alis"]), sayi(by[k]["Satis"])]

    veri = {"kaynak": "Altınkaynak (static.altinkaynak.com/public/Gold)", "kodlar": {"GA": "Gram altın", "C": "Çeyrek altın", "B_T": "22 ayar hurda", "XAUUSD": "Ons altın (USD)"}, "kayitlar": []}
    if os.path.exists(yol):
        veri = json.load(open(yol, encoding="utf-8"))
    kayitlar = veri["kayitlar"]
    if kayitlar and kayitlar[-1]["t"] == kayit["t"]:
        print("değişiklik yok:", kayit["t"]); return
    kayitlar.append(kayit)
    sinir = datetime.now(TR).timestamp() - SAKLA_GUN * 86400
    veri["kayitlar"] = [k for k in kayitlar if datetime.fromisoformat(k["t"]).timestamp() >= sinir]
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, separators=(",", ":"))
    print("eklendi:", kayit)

if __name__ == "__main__":
    main()
