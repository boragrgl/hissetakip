#!/usr/bin/env python3
"""Kullanıcının verdiği günlük altın fiyatı Excel dosyasını site/data/altin-gecmis.json dosyasına ekler.

Beklenen sütunlar (ilk sayfa): Tarih | Gram Altın (TL/gram) | Çeyrek Altın (TL/adet) | 22 Ayar Hurda Gösterge (TL/gram)
Kayıtlar kaynak="dosya" olarak işaretlenir. Dosyada yalnız tek fiyat (satış/kapanış) olduğu için alış boş bırakılır.
Aynı günden önceden eklenmiş "dosya" ya da "evds" kaydı varsa yenisiyle değiştirilir. Altınkaynak kayıtlarına dokunulmaz.

Kullanım: python3 robot/dosya_aktar.py <dosya.xlsx> [site/data/altin-gecmis.json]
"""
import json, sys
from datetime import datetime, time
from zoneinfo import ZoneInfo
import openpyxl

TR = ZoneInfo("Europe/Istanbul")
SUTUN = {"GA": "gram", "C": "çeyrek", "B_T": "22 ayar"}

def main():
    xlsx = sys.argv[1]
    yol = sys.argv[2] if len(sys.argv) > 2 else "site/data/altin-gecmis.json"
    ws = openpyxl.load_workbook(xlsx, data_only=True).worksheets[0]
    satirlar = list(ws.iter_rows(values_only=True))
    bas = [str(h or "").lower() for h in satirlar[0]]
    idx = {"t": next(i for i, h in enumerate(bas) if "tarih" in h)}
    for kod, kelime in SUTUN.items():
        idx[kod] = next(i for i, h in enumerate(bas) if kelime in h)
    yeni = []
    for r in satirlar[1:]:
        t = r[idx["t"]]
        if not isinstance(t, datetime):
            continue
        k = {"t": datetime.combine(t.date(), time(18, 0), TR).isoformat(timespec="minutes"), "kaynak": "dosya"}
        for kod in SUTUN:
            v = r[idx[kod]]
            if isinstance(v, (int, float)):
                k[kod] = [None, round(float(v), 2)]
        if len(k) > 2:
            yeni.append(k)
    veri = json.load(open(yol, encoding="utf-8"))
    gunler = {k["t"][:10] for k in yeni}
    eski = [k for k in veri["kayitlar"] if not (k.get("kaynak") in ("dosya", "evds") and k["t"][:10] in gunler)]
    veri["kayitlar"] = sorted(eski + yeni, key=lambda k: k["t"])
    veri["dosya"] = {"ad": xlsx.rsplit("/", 1)[-1], "gun": len(yeni), "ilk": yeni[0]["t"][:10], "son": yeni[-1]["t"][:10],
                     "aciklama": "kaynak=dosya kayıtları kullanıcının verdiği günlük kapanış dosyasından; tek fiyat (satış/gösterge), alış yok."}
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(yeni)} gün eklendi: {yeni[0]['t'][:10]} – {yeni[-1]['t'][:10]}")

if __name__ == "__main__":
    main()
