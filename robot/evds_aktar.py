#!/usr/bin/env python3
"""TCMB EVDS'den geriye dönük günlük altın fiyatlarını alır ve Altınkaynak fiyat düzeyine ölçekleyerek
site/data/altin-gecmis.json dosyasına "tahmini" (kaynak: evds) kayıt olarak ekler.

Neden ölçekleme: EVDS'de Altınkaynak'ın çeyrek / gram / 22 ayar hurda fiyatları yok. EVDS'deki altın serisinin
günlük hareketi alınır ve ilk gerçek Altınkaynak kaydındaki fiyata oranlanır (o gün EVDS = Altınkaynak olacak şekilde).
Bu kayıtlar grafikte kesikli çizilir ve "tahmini" diye işaretlenir. Altınkaynak kayıtlarına dokunulmaz.

Gerekli: EVDS_API_KEY ortam değişkeni (https://evds2.tcmb.gov.tr → üye ol → Profil → API Anahtarı).
İsteğe bağlı: EVDS_SERI_GRAM, EVDS_SERI_CEYREK (seri kodunu elle vermek için), EVDS_BASE.
Kullanım: python3 robot/evds_aktar.py [site/data/altin-gecmis.json] [--gun 45]
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TR = ZoneInfo("Europe/Istanbul")
BASES = [os.environ.get("EVDS_BASE")] if os.environ.get("EVDS_BASE") else [
    "https://evds2.tcmb.gov.tr/service/evds",
    "https://evds3.tcmb.gov.tr/igmevdsms-dis",
]
KEY = os.environ.get("EVDS_API_KEY", "").strip()

def get(base, path):
    req = urllib.request.Request(f"{base}/{path}", headers={"key": KEY, "Accept": "application/json", "User-Agent": "hissetakip/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        txt = r.read().decode("utf-8", "replace")
    return json.loads(txt)

def sec_base():
    for b in BASES:
        try:
            c = get(b, "categories/type=json")
            if isinstance(c, list) and c:
                return b, c
        except Exception as e:
            print(f"{b}: {e}")
    sys.exit("EVDS'ye bağlanılamadı (anahtar veya adres hatalı olabilir).")

def seri_bul(base, kategoriler):
    """'Altın' geçen veri gruplarındaki serilerden külçe (gram) ve Cumhuriyet altını satış serilerini bulur."""
    adaylar = []
    for k in kategoriler:
        kid = k.get("CATEGORY_ID")
        try:
            gruplar = get(base, f"datagroups/mode=2&code={kid}&type=json")
        except Exception:
            continue
        for g in gruplar if isinstance(gruplar, list) else []:
            ad = (g.get("DATAGROUP_NAME") or "") + " " + (g.get("DATAGROUP_NAME_ENG") or "")
            if "ltın" not in ad and "old" not in ad:
                continue
            try:
                seriler = get(base, f"serieList/type=json&code={g['DATAGROUP_CODE']}")
            except Exception:
                continue
            for s in seriler if isinstance(seriler, list) else []:
                adaylar.append((s.get("SERIE_CODE"), s.get("SERIE_NAME") or "", s.get("FREQUENCY_STR") or ""))
    print("Bulunan altın serileri:")
    for c in adaylar:
        print("  ", c)
    def bul(*kelimeler):
        for kod, ad, frek in adaylar:
            a = ad.lower()
            if all(w in a for w in kelimeler) and ("satış" in a or "satis" in a) and not any(w in frek.lower() for w in ("ayl", "hafta", "yıll", "month", "week", "annual", "quarter", "çeyrek")):
                return kod
        return None
    gram = os.environ.get("EVDS_SERI_GRAM") or bul("külçe") or bul("altın", "gr")
    ceyrek = os.environ.get("EVDS_SERI_CEYREK") or bul("cumhuriyet") or gram
    if not gram:
        sys.exit("Altın serisi bulunamadı. EVDS_SERI_GRAM ile seri kodunu elle verin.")
    print("Seçilen seriler → gram/hurda:", gram, " çeyrek:", ceyrek)
    return gram, ceyrek

def veri(base, kod, bas, bit):
    j = get(base, f"series={kod}&startDate={bas:%d-%m-%Y}&endDate={bit:%d-%m-%Y}&type=json")
    alan = kod.replace(".", "_")
    out = {}
    for it in j.get("items", []):
        v = it.get(alan)
        if v in (None, "", "ND"):
            continue
        out[datetime.strptime(it["Tarih"], "%d-%m-%Y").date()] = float(v)
    return out

def main():
    if not KEY:
        sys.exit("EVDS_API_KEY tanımlı değil.")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    yol = args[0] if args else "site/data/altin-gecmis.json"
    gun = int(sys.argv[sys.argv.index("--gun") + 1]) if "--gun" in sys.argv else 45
    dosya = json.load(open(yol, encoding="utf-8"))
    gercek = [k for k in dosya["kayitlar"] if k.get("kaynak") != "evds"]
    if not gercek:
        sys.exit("Ölçekleme için en az bir Altınkaynak kaydı gerekli.")
    ref = gercek[0]
    ref_t = datetime.fromisoformat(ref["t"])
    base, kategoriler = sec_base()
    print("EVDS adresi:", base)
    s_gram, s_ceyrek = seri_bul(base, kategoriler)
    bas, bit = (ref_t - timedelta(days=gun)).date(), ref_t.date()
    seriler = {s_gram: veri(base, s_gram, bas, bit)}
    if s_ceyrek != s_gram:
        seriler[s_ceyrek] = veri(base, s_ceyrek, bas, bit)
    harita = {"GA": s_gram, "B_T": s_gram, "C": s_ceyrek}
    # Referans gündeki (ya da öncesindeki en yakın) EVDS değerine göre ölçek
    olcek = {}
    for kod, seri in harita.items():
        d = seriler[seri]
        gunler = sorted(x for x in d if x <= ref_t.date())
        if not gunler or ref.get(kod) is None:
            sys.exit(f"{kod} için ölçek kurulamadı (EVDS'de {ref_t.date()} öncesi veri yok).")
        e = d[gunler[-1]]
        olcek[kod] = (ref[kod][0] / e, ref[kod][1] / e)
        print(f"{kod}: EVDS {gunler[-1]} = {e:,.2f} → Altınkaynak alış/satış {ref[kod]} (ölçek {olcek[kod][1]:.4f})")
    tum_gunler = sorted(set().union(*[set(v) for v in seriler.values()]))
    yeni = []
    for g in tum_gunler:
        t = datetime(g.year, g.month, g.day, 15, 30, tzinfo=TR)
        if t >= ref_t:
            continue
        k = {"t": t.isoformat(timespec="minutes"), "kaynak": "evds"}
        for kod, seri in harita.items():
            v = seriler[seri].get(g)
            if v is not None:
                k[kod] = [round(v * olcek[kod][0]), round(v * olcek[kod][1])]
        if len(k) > 2:
            yeni.append(k)
    dosya["kayitlar"] = sorted(yeni + gercek, key=lambda k: k["t"])
    dosya["evds"] = {"seriler": {"GA": s_gram, "B_T": s_gram, "C": s_ceyrek}, "referans": ref["t"],
                     "aciklama": "kaynak=evds kayıtları, EVDS serisinin referans günündeki Altınkaynak fiyatına ölçeklenmiş tahminidir."}
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(dosya, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(yeni)} tahmini kayıt eklendi ({bas} – {ref_t.date()}).")

if __name__ == "__main__":
    main()
