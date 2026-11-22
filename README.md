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

## Altın
- **Canlı fiyatlar:** Ana sayfadaki ve Altın sayfasındaki çeyrek, gram ve 22 ayar hurda fiyatları Altınkaynak'tan canlı gelir (`/api/altin`, `src/worker.js`).
- **Grafik:** Altın sayfasındaki grafik `site/data/altin-gecmis.json` dosyasından çizilir. GitHub Actions bu dosyaya saat başı Altınkaynak kaydı ekler.
- **Geriye dönük kısım:** 1 Eylül – 21 Kasım 2026 arasındaki günlük kapanışlar `veri/` klasöründeki Excel dosyasından gelir. Dosya `python3 robot/dosya_aktar.py veri/<dosya>.xlsx` komutuyla eklenir. Grafikte kesikli çizgiyle gösterilir.
- **Yedek yol (EVDS, şu an kullanılmıyor):** TCMB EVDS'den aktarım. Adımlar:
  1. https://evds2.tcmb.gov.tr adresinde ücretsiz üye ol, *Profil → API Anahtarı* bölümünden anahtarını kopyala.
  2. GitHub'da *Settings → Secrets and variables → Actions → New repository secret* ekranına git. Adı `EVDS_API_KEY`, değeri anahtarın olsun.
  3. *Actions → "EVDS geçmiş altın aktarımı" → Run workflow* adımlarıyla çalıştır.

  EVDS'de Altınkaynak'ın çeyrek, gram ve hurda fiyatları yok. Bu yüzden EVDS altın serisi ilk Altınkaynak kaydına ölçeklenir ve grafikte kesikli "tahmini" çizgiyle gösterilir.

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `yontem.md` | Temel analiz kuralları (Hisse Seçimi Maddeleri) |
| `hisse-listesi.md` | Takip edilen hisseler (`HISSELER:` satırı) |
| `robot/temel_analiz.py` | Hesaplama motoru. Eşikler dosyanın başındaki `CFG` bölümünde |
| `robot/fetch_isyatirim.js` | Veri çekme kodu (tarayıcıda çalışır) |
| `robot/calistir.sh` | Analiz, arşiv ve site verisi adımları |
| `robot/build_site.py` | Veri gömülü tek dosyalık site üretir (Claude yan paneli için) |
| `site/index.html` | Ana sayfa (altın KPI'ları + hisse özeti) |
| `site/altin.html` | Altın sayfası (grafik) |
| `site/stil.css`, `site/ortak.js` | Ortak tasarım ve altın verisi kodu |
| `site/hisseler.html` | Hisse senetleri ekranı |
| `src/worker.js` | Canlı altın fiyatı uç noktası (`/api/altin`) |
| `robot/altin_kaydet.py`, `.github/workflows/altin.yml` | Saatlik altın fiyat kaydı |
| `robot/evds_aktar.py`, `.github/workflows/evds.yml` | EVDS'den geriye dönük altın aktarımı (elle) |
| `raporlar/son-rapor.md` | Son günün metin raporu |

_Kuralların mekanik uygulamasıdır; yatırım tavsiyesi değildir._
