#!/usr/bin/env python3
"""BIST Temel Analiz Robotu — "Hisse Seçimi Maddeleri" yöntemi.

Girdi : fetch_isyatirim.js çıktısı (JSON; araç çıktısı dosyası da olabilir)
Çıktı : sonuc.json (hisse bazında tüm hesaplar) + rapor.md (özet)

Kullanım: python3 temel_analiz.py <veri.json> [cikti_klasoru]
"""
import json, sys, os, statistics
from datetime import datetime
from zoneinfo import ZoneInfo

# ---------------- AYARLAR (yöntem eşikleri) ----------------
CFG = {
    "faiz_ortami": "yuksek",      # "yuksek" | "dusuk"  (mali yapı yorumunu etkiler)
    "nis_gecme_fazla": 0.20,      # Madde 1: dönen varlıklar KVB'den en az %20 fazla
    "nis_ideal_oran": 2.0,        # Madde 1: ideal DV/KVB = 2
    "nakit_karsilama_min": 0.50,  # Madde 2: (nakit+fin.yat.) / KV finansal borç ≥ %50
    "ticari_alacak_uyari": 0.40,  # Madde 2: ticari alacak / dönen varlık > %40 → dipnot kontrolü
    "mali_guclu": 0.60,           # Madde 3: özkaynak/varlık ≥ %60 güçlü
    "mali_dengeli": 0.40,         # Madde 3: %40-60 dengeli, ≤%40 güçsüz
    "favok_civari_tolerans": 0.90,# Madde 3: güçsüz yapıda FAVÖK marjı sektörün en az %90'ı ("civarı")
    "bonus_var": 10.0,            # Bonus: özkaynak / ödenmiş sermaye ≥ 10x → bedelsiz potansiyeli var
    "bonus_guclu": 40.0,          #        ≥ 40x (dokümandaki "40/1") güçlü potansiyel
    "bonus_zirve": 100.0,         #        ≥ 100x "zirve kağıt, al yaslan"
    "favok_marj_makul_max": 1.0,  # FAVÖK marjı > %100 ise (satışı çok düşük holding/GYO) marj güvenilmez sayılır
    "sektor_min_eleman": 3,       # sektör ortalaması için en az bu kadar geçerli şirket
}

def sdiv(a, b):
    try:
        if a is None or b in (None, 0):
            return None
        return a / b
    except Exception:
        return None

def load(path):
    raw = open(path, encoding="utf-8").read().strip()
    obj = json.loads(raw)
    # araç çıktısı formatı: [{"type":"text","text":"\"{...}\""}]
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "text" in obj[0]:
        obj = obj[0]["text"]
    while isinstance(obj, str):  # sondaki "(captured at origin ...)" gibi ekleri yok say
        obj = json.JSONDecoder().raw_decode(obj.strip())[0]
    return obj

def sector_stats(market):
    """Sektör ve piyasa medyanları: F/K, PD/DD, FAVÖK marjı (=FD/Satış ÷ FD/FAVÖK)."""
    by = {}
    allv = {"fk": [], "pddd": [], "favok": []}
    for kod, ad, sek, kap, fk, fdfavok, fdsat, pddd, donem in market:
        d = by.setdefault(sek or "Bilinmiyor", {"fk": [], "pddd": [], "favok": [], "n": 0})
        d["n"] += 1
        if fk and fk > 0:
            d["fk"].append(fk); allv["fk"].append(fk)
        if pddd and pddd > 0:
            d["pddd"].append(pddd); allv["pddd"].append(pddd)
        m = sdiv(fdsat, fdfavok)
        if m is not None and fdfavok and fdfavok > 0 and 0 < m < 1.5:
            d["favok"].append(m); allv["favok"].append(m)
    med = lambda xs: statistics.median(xs) if xs else None
    out = {}
    for s, d in by.items():
        out[s] = {k: (med(d[k]) if len(d[k]) >= CFG["sektor_min_eleman"] else None) for k in ("fk", "pddd", "favok")}
        out[s].update({f"n_{k}": len(d[k]) for k in ("fk", "pddd", "favok")})
        out[s]["n"] = d["n"]
    piyasa = {k: med(v) for k, v in allv.items()}
    return out, piyasa

def analyze(kod, f, m, sek_stats, piyasa):
    r = {"kod": kod}
    if m:
        _, ad, sek, kap, fk, fdfavok, fdsat, pddd, donem = m
        r.update(ad=ad, sektor=sek, fiyat=kap, fk=fk, pddd=pddd, donem=donem)
    if not f or "error" in f:
        r["hata"] = (f or {}).get("error", "Veri yok")
        r["karar"] = "VERİ YOK"
        return r
    it = f["items"]; g = lambda k: it.get(k)
    DV, NAKIT, FINYAT, TICALAC = g("1A"), g("1AA"), g("1AB"), g("1AC")
    TV, KVB, KVFB, UVFB = g("1BL"), g("2A"), g("2AA"), g("2BA")
    OZK, ODS, SAT = g("2N"), g("2OA"), g("3C")
    FAVOK = (g("3DF") or 0) + (g("4B") or 0) if g("3DF") is not None else None
    r["mali_donem"] = f["period"]
    r["ham"] = {"donen_varliklar": DV, "kv_borclar": KVB, "nakit": NAKIT, "finansal_yatirimlar": FINYAT,
                "kv_finansal_borc": KVFB, "uv_finansal_borc": UVFB, "ticari_alacak": TICALAC,
                "toplam_varlik": TV, "ozkaynak": OZK, "odenmis_sermaye": ODS, "net_satis": SAT, "favok": FAVOK}
    notlar = []

    # --- Madde 1: Net işletme sermayesi
    dv_kvb = sdiv(DV, KVB)
    r["nis_fazla"] = None if dv_kvb is None else dv_kvb - 1
    if dv_kvb is None:
        r["m1"] = "?"
    elif dv_kvb - 1 >= CFG["nis_gecme_fazla"]:
        r["m1"] = "GEÇTİ"
        if dv_kvb >= CFG["nis_ideal_oran"]:
            notlar.append("Dönen varlıklar KVB'nin 2 katından fazla (ideal).")
    elif dv_kvb >= 1:
        r["m1"] = "SINIRDA"
        notlar.append("Dönen varlıklar KVB'yi karşılıyor ama %20 fazlalık yok.")
    else:
        r["m1"] = "KALDI"
        notlar.append("KVB > dönen varlıklar: bedelli sermaye artışı riski.")

    # --- Madde 2: Nakit durumu
    nakit_top = (NAKIT or 0) + (FINYAT or 0)
    if not KVFB:
        r["nakit_karsilama"] = None
        r["m2"] = "GEÇTİ"
        notlar.append("Kısa vadeli finansal borç yok.")
    else:
        r["nakit_karsilama"] = nakit_top / KVFB
        r["m2"] = "GEÇTİ" if r["nakit_karsilama"] >= CFG["nakit_karsilama_min"] else "KALDI"
        if r["m2"] == "KALDI":
            notlar.append("Nakit + finansal yatırımlar KV finansal borcun yarısını karşılamıyor.")
    r["ticari_alacak_payi"] = sdiv(TICALAC, DV)
    if r["ticari_alacak_payi"] is not None and r["ticari_alacak_payi"] > CFG["ticari_alacak_uyari"] and CFG["faiz_ortami"] == "yuksek":
        notlar.append(f"Ticari alacaklar dönen varlıkların %{r['ticari_alacak_payi']*100:.0f}'i: dipnotlarda teminatlı/şüpheli ayrımına bak.")

    # --- Madde 3: Mali yapı
    oz = sdiv(OZK, TV)
    r["ozkaynak_orani"] = oz
    r["m3"] = "?" if oz is None else ("GÜÇLÜ" if oz >= CFG["mali_guclu"] else "DENGELİ" if oz > CFG["mali_dengeli"] else "GÜÇSÜZ")

    # --- Madde 4: Kârlılık (FAVÖK marjı vs sektör)
    marj = sdiv(FAVOK, SAT)
    if marj is not None and abs(marj) > CFG["favok_marj_makul_max"]:
        notlar.append(f"FAVÖK marjı %{marj*100:.0f} çıktı (satışlar çok düşük); kârlılık maddesi değerlendirilemedi.")
        marj = None
    r["favok_marji"] = marj
    ss = sek_stats.get(r.get("sektor"), {})
    ref = ss.get("favok"); ref_kaynak = "sektör"
    if ref is None:
        ref, ref_kaynak = piyasa.get("favok"), "piyasa"
    r["sektor_favok_marji"], r["favok_ref_kaynak"] = ref, ref_kaynak
    if marj is None or ref is None:
        r["m4"] = "?"
    else:
        r["m4"] = "GEÇTİ" if marj > ref else "KALDI"

    # --- Bonus: bedelsiz potansiyeli
    b = sdiv(OZK, ODS)
    r["ozk_sermaye_kat"] = b
    r["bonus"] = None if b is None else ("ZİRVE" if b >= CFG["bonus_zirve"] else "GÜÇLÜ" if b >= CFG["bonus_guclu"] else "VAR" if b >= CFG["bonus_var"] else "YOK")

    # --- Hedef fiyat
    sfk, spd = ss.get("fk"), ss.get("pddd")
    r["sektor_fk"], r["sektor_pddd"] = sfk, spd
    if sfk is None:
        sfk = piyasa.get("fk")
        if r.get("fk"):
            notlar.append("Sektörde yeterli şirket yok; F/K için piyasa medyanı kullanıldı.")
    if spd is None:
        spd = piyasa.get("pddd")
        notlar.append("Sektörde yeterli şirket yok; PD/DD için piyasa medyanı kullanıldı.")
    fiyat = r.get("fiyat")
    h_pd = sdiv(spd, r.get("pddd")) * fiyat if (fiyat and r.get("pddd") and r["pddd"] > 0 and spd) else None
    h_fk = sdiv(sfk, r.get("fk")) * fiyat if (fiyat and r.get("fk") and r["fk"] > 0 and sfk) else None
    r["hedef_pddd"], r["hedef_fk"] = h_pd, h_fk
    hs = [h for h in (h_pd, h_fk) if h]
    r["hedef"] = sum(hs) / len(hs) if hs else None
    if h_fk is None and h_pd is not None:
        notlar.append("F/K hesaplanamıyor (zarar); hedef yalnız PD/DD'ye göre.")
    r["fark"] = r["hedef"] - fiyat if (r["hedef"] and fiyat) else None
    r["potansiyel"] = sdiv(r["fark"], fiyat)

    # --- Karar (yönteme göre)
    yuksek = CFG["faiz_ortami"] == "yuksek"
    favok_civari = marj is not None and ref is not None and marj >= ref * CFG["favok_civari_tolerans"]
    if r["m3"] == "GÜÇSÜZ" and yuksek and (FAVOK is None or FAVOK <= 0 or (marj is not None and not favok_civari)):
        karar = "UZAK DUR"
        notlar.append("Yüksek faizde mali yapı güçsüz ve FAVÖK sektör civarında değil.")
    elif r["m1"] == "KALDI" or r["m2"] == "KALDI":
        karar = "İZLEME (BSA FIRSATI)"
        notlar.append("Alınmaz; izlemede tut. Bedelli onayı sonrası sert düşüş = olası giriş noktası.")
    elif r["m1"] == "GEÇTİ" and r["m2"] == "GEÇTİ" and r["m3"] in ("GÜÇLÜ", "DENGELİ") and r["m4"] == "GEÇTİ":
        karar = "ALIM ADAYI"
        if r["m3"] == "DENGELİ":
            notlar.append("Mali yapı dengeli: borcun 'iyi borç' olduğunu (finansman giderleri) kontrol et.")
    else:
        karar = "KOŞULLU"
        if r["m3"] == "GÜÇSÜZ":
            notlar.append("Mali yapı güçsüz ama FAVÖK sektör civarında; borç kalitesini kontrol et.")
        if r["m4"] == "KALDI":
            notlar.append("FAVÖK marjı sektörün altında.")
    if r["bonus"] == "ZİRVE":
        notlar.append("Bedelsiz potansiyeli çok yüksek: 'zirve kağıt, al yaslan' (kaymaklı fıstık sarma).")
    elif r["bonus"] == "GÜÇLÜ":
        notlar.append("Bedelsiz sermaye artışı potansiyeli yüksek (kaymaklı fıstık sarma).")
    r["karar"], r["notlar"] = karar, notlar
    return r

ORDER = {"ALIM ADAYI": 0, "KOŞULLU": 1, "İZLEME (BSA FIRSATI)": 2, "UZAK DUR": 3, "VERİ YOK": 4}

def pct(x, d=0):
    return "—" if x is None else f"%{x*100:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def num(x, d=2):
    return "—" if x is None else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def kat(x):
    return "—" if x is None else num(x, 1) + "x"

def main():
    src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(out, exist_ok=True)
    data = load(src)
    market = data["market"]; mk = {m[0]: m for m in market}
    sek, piyasa = sector_stats(market)
    res = [analyze(k, f, mk.get(k), sek, piyasa) for k, f in data["fin"].items()]
    res.sort(key=lambda r: (ORDER.get(r["karar"], 9), -(r.get("favok_marji") or -9)))
    meta = {"asOf": data["asOf"], "faiz_ortami": CFG["faiz_ortami"], "piyasa": piyasa, "ayarlar": CFG,
            "hisse_sayisi_bist": len(market)}
    json.dump({"meta": meta, "sonuclar": res}, open(os.path.join(out, "sonuc.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    L = [f"# Temel Analiz Raporu — {datetime.fromisoformat(data['asOf'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Istanbul')).strftime('%d.%m.%Y')}", "",
         f"Faiz ortamı: **{CFG['faiz_ortami']}** · Piyasa medyanı F/K {num(piyasa['fk'],1)}, PD/DD {num(piyasa['pddd'],2)}, FAVÖK marjı {pct(piyasa['favok'],1)}", "",
         "| Hisse | Karar | Fiyat | Hedef | Potansiyel | NİS fazla | Nakit karş. | Özkaynak/Varlık | FAVÖK marjı (sektör) | Özk/Sermaye |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        if r["karar"] == "VERİ YOK":
            L.append(f"| {r['kod']} | VERİ YOK | {num(r.get('fiyat'))} | | | | | | | |"); continue
        L.append(f"| {r['kod']} | {r['karar']} | {num(r.get('fiyat'))} | {num(r['hedef'])} | {pct(r['potansiyel'])} | "
                 f"{pct(r['nis_fazla'])} ({r['m1']}) | {pct(r['nakit_karsilama'])} ({r['m2']}) | {pct(r['ozkaynak_orani'])} ({r['m3']}) | "
                 f"{pct(r['favok_marji'],1)} ({pct(r['sektor_favok_marji'],1)}) | {kat(r['ozk_sermaye_kat'])} |")
    L += ["", "## Notlar"]
    for r in res:
        n = r.get("notlar") or ([r["hata"]] if r.get("hata") else [])
        if n:
            L.append(f"- **{r['kod']}** ({r.get('sektor','')}, mali tablo {r.get('mali_donem','—')}): " + " ".join(n))
    L += ["", "_Bu rapor belirlenen kuralların mekanik uygulamasıdır; yatırım tavsiyesi değildir._"]
    open(os.path.join(out, "rapor.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    main()
