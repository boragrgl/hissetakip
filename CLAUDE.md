# hissetakip: Claude için proje notları

Yanıtlar Türkçe. Kullanıcı: boragrgl. Commit author: `boragrgl <ibit_@hotmail.com>`.

## Kurallar
- **Veri kaynağı: İş Yatırım.** Fintables kullanılmaz, çünkü kullanım koşulları scraping ve bot erişimini yasaklıyor.
- İş Yatırım'ın MaliTablo uç noktası sunucudan doğrudan erişime kapalı (robots, proxy). Veri, kullanıcının bilgisayarındaki Claude yerleşik tarayıcısından `robot/fetch_isyatirim.js` ile çekilir. Günde tek çalıştırma, yalnız listedeki hisseler.
- Kurallar `yontem.md` ile `robot/temel_analiz.py` içindeki `CFG` arasında tutarlı kalmalı. Biri değişirse diğeri de güncellenir.
- Eşik, yöntem ve site tasarımı değişiklikleri **kullanıcı onayı olmadan yapılmaz**. Günlük veri güncellemesi onaylı akıştır: `site/data/`, `raporlar/` ve `main`'e push.
- Bankalar, sigorta ve aracı kurumlar yöntem kapsamı dışındadır ("VERİ YOK").
- Rapor ve site her zaman "yatırım tavsiyesi değildir" notunu taşır.

## Günlük akış (zamanlanmış görev, hafta içi 20:17 TR)
1. `hisse-listesi.md` içindeki `HISSELER:` satırından kodları al. `robot/fetch_isyatirim.js` içindeki `__TICKERS__` yerine JSON dizisi olarak yaz.
2. Yerleşik tarayıcıda https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx sayfasını aç ve kodu `javascript_tool` ile çalıştır. Çıktı büyük olduğu için dosyaya kaydedilir. O dosyayı `veri.json` yap (bu dosya git'e girmez).
3. `bash robot/calistir.sh veri.json`
4. Önceki `raporlar/son-rapor.md` (git'teki hali) ile karşılaştır: kategori değişimleri, 10 puanı aşan potansiyel değişimleri, yeni mali dönemler.
5. Commit ("veri: GG.AA.YYYY"), `git pull --rebase` (altın kaydı Action'ı da push ediyor) ve `main`'e push.
6. Kullanıcıya kısa özet gönder. Hata olursa veri uydurma ve push yapma.

## Site
- Tasarım Apple tarzı: ortak stiller `site/stil.css`, ortak altın kodu `site/ortak.js`. Üst menü: Ana sayfa · Altın · Hisse Senetleri.
- `site/index.html` ana sayfa: iki eşit kart. Solda "Altın fiyatları" tablosu (çeyrek, gram, 22 ayar hurda, ons; alış/satış/%), satıra tıklayınca `altin.html#KOD` açılır. Sağda en iyi 5 hisse (karar sırası, sonra potansiyel) ve özet satırı. Grafik ana sayfada yok, ok işaretleri yok.
- `site/altin.html` altın ayrıntı sayfası: sol üstte tür adı, sağ üstte Çeyrek/Gram/Hurda/Ons seçici (varsayılan çeyrek). Alış/Satış(+%)/Yüksek/Düşük kutuları, düşük–yüksek çubuğu, 1 aylık grafik. Yüksek/düşük, son günün Altınkaynak kayıtlarından hesaplanır (servis vermiyor).
- `site/hisseler.html` hisse senetleri ekranıdır (tüm ayrıntılar).
- `src/worker.js` (Cloudflare Worker): `/api/altin` Altınkaynak'ın herkese açık servisinden (https://static.altinkaynak.com/public/Gold, bkz. altinkaynak.com/Araclar/Servisler) gram altın (GA), çeyrek (C), 22 ayar hurda (B_T) ve ons (XAUUSD, $) fiyatlarını 60 sn önbellekle döndürür.
- Altın grafiği `site/data/altin-gecmis.json` dosyasından çizilir. `.github/workflows/altin.yml` 08:07–23:07 TR arası saatlik kayıt ekler (`robot/altin_kaydet.py`). Altınkaynak'ın arşiv uç noktası (eb.altinkaynak.com) kendi uygulama anahtarıyla çalışır, kullanılmaz. Geçmiş bu yüzden kendi kayıtlarımızla birikir.
- Geriye dönük kısım kullanıcının verdiği Excel dosyasından: `veri/Altin_Gunluk_Fiyatlar_01Eylul_21Kasim2026.xlsx` (1 Eylül – 21 Kasım 2026, günlük kapanış; 22 ayar hurda gösterge değeri). `robot/dosya_aktar.py` ile `kaynak: "dosya"` olarak eklenir. Alış yok, grafikte kesikli çizilir. Yeni bir dosya gelirse aynı betikle eklenir.
- Yedek yol (şu an kullanılmıyor) TCMB EVDS: `robot/evds_aktar.py`, elle çalıştırılan `.github/workflows/evds.yml` (secret `EVDS_API_KEY`). EVDS serisi ilk gerçek Altınkaynak kaydına ölçeklenir ve `kaynak: "evds"` olarak işaretlenir. Grafikte kesikli çizilir ve "tahmini" diye gösterilir. Altınkaynak kayıtları ondan sonra saatlik devam eder.

## Durum ve sıradaki işler (23.11.2026)
- Canlı site: https://hissetakip.bybora.workers.dev (Cloudflare Workers, `main`'e push = yayın). Kullanıcı yeni tasarım değişikliklerini önce önizlemede görmek ister: değişikliği ayrı dalda yap, claude.ai artifact olarak göster ("Hisse Takip Önizleme"), onaydan sonra `main`'e al.
- Claude yan paneli ("Hisse Takip" artifact, https://claude.ai/artifact/Dr5rGEfJAD7xrkXt1QZ3BD): `/hisse-takip` becerisi `python3 robot/panel_hazirla.py` ile sitenin çok dosyalı kopyasını üretir ve bu artifact'e yayınlar. Altın fiyatı olarak son Altınkaynak kaydı kullanılır.
- Zamanlanmış görev "BIST günlük temel analiz" (hafta içi 20:17 TR, kullanıcının bilgisayarında): repoyu klonlar, bu dosyadaki günlük akışı uygular, push eder, "borsa analizi" projesine `temel-analiz/sonuc.json` ve `son-rapor.md` yazar.
- **Sıradaki iş: hisse fiyatını siteye girildiği anda güncellemek.** Karar: fiyat Google E-Tablolar'daki `GOOGLEFINANCE("IST:KOD";"price")` formülüyle alınacak. Tablo kullanıcının Google hesabında açılıp "web'de yayınla" ile CSV yapılacak. Worker bu CSV'yi okuyup F/K, PD/DD, hedef ve potansiyeli kayıtlı bilançoyla yeniden hesaplayacak. Dört madde fiyattan bağımsız. #N/A dönen hisselerde günlük İş Yatırım fiyatı kullanılır. Kullanıcı Google Drive bağlantısı ekleyebilir ya da tabloyu kendisi açar.
- Elenen fiyat kaynakları: Fintables (koşullar scraping'i yasaklıyor), Bloomberg HT (robots piyasa verisi yollarını kapatıyor, veriler lisanslı), Google Finance sitesi (resmi API yok).
- Bekleyen diğer işler: teknik analiz kuralları (kullanıcı verecek), yeni hisseler (`hisse-listesi.md`), altın grafiği için ileride 3 ay seçeneği.

## Teknik analiz (sonraki aşama)
`sonuc.json` içindeki her hisseye şu alan eklenecek:
`teknik: {sinyal, ozet, gostergeler:[{ad, deger, yorum}], birlesik}`. Site bu alanı kod değişmeden gösterir.
Fiyat geçmişi kaynağı kullanıcıyla birlikte seçilecek.
