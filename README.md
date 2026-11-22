# hissetakip

Takip edilen BIST hisselerinin belirlenen temel analiz kriterlerinden geçip geçmediğini her gün kontrol eden robot ve sonuçları gösteren site. Teknik analiz ileride aynı akışa eklenecek.

## Akış

```
İş Yatırım ──(yerleşik tarayıcı, fetch_isyatirim.js)──► veri.json
     veri.json ──(robot/calistir.sh → temel_analiz.py)──► site/data/sonuc.json + raporlar/son-rapor.md
     main'e push ──► Cloudflare Workers ──► telefonda/masaüstünde açılan site
```

1. **Veri:** `robot/fetch_isyatirim.js`, İş Yatırım "Temel Değerler ve Oranlar" sayfasında tarayıcıda çalışır. Tüm BIST'in fiyat, F/K, PD/DD, FD/FAVÖK, FD/Satış ve sektör bilgisini, ayrıca listedeki hisselerin son bilançosunu alır.
2. **Analiz:** `bash robot/calistir.sh veri.json` komutu `yontem.md` kurallarını uygular. `site/data/sonuc.json`, `site/data/gecmis/GG.json` ve `raporlar/son-rapor.md` dosyalarını yazar.
3. **Site:** `site/index.html` dosyası `data/sonuc.json` verisini okur. Cloudflare'de `wrangler.jsonc` ile statik site olarak yayınlanır. Telefonda "Ana ekrana ekle" ile uygulama gibi açılır.

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `yontem.md` | Temel analiz kuralları (Hisse Seçimi Maddeleri) |
| `hisse-listesi.md` | Takip edilen hisseler (`HISSELER:` satırı) |
| `robot/temel_analiz.py` | Hesaplama motoru. Eşikler dosyanın başındaki `CFG` bölümünde |
| `robot/fetch_isyatirim.js` | Veri çekme kodu (tarayıcıda çalışır) |
| `robot/calistir.sh` | Analiz, arşiv ve site verisi adımları |
| `robot/build_site.py` | Veri gömülü tek dosyalık site üretir (Claude yan paneli için) |
| `site/` | Yayınlanan site |
| `raporlar/son-rapor.md` | Son günün metin raporu |

_Kuralların mekanik uygulamasıdır; yatırım tavsiyesi değildir._
