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
- `site/index.html` ana sayfadır: solda altın, sağda hisse özeti. `site/hisseler.html` hisse senetleri ekranıdır.
- `src/worker.js` (Cloudflare Worker): `/api/altin` Altınkaynak'ın herkese açık servisinden (https://static.altinkaynak.com/public/Gold, bkz. altinkaynak.com/Araclar/Servisler) gram altın (GA), çeyrek (C) ve 22 ayar hurda (B_T) fiyatlarını 60 sn önbellekle döndürür.
- Altın grafiği `site/data/altin-gecmis.json` dosyasından çizilir. `.github/workflows/altin.yml` 08:07–23:07 TR arası saatlik kayıt ekler (`robot/altin_kaydet.py`). Altınkaynak'ın arşiv uç noktası (eb.altinkaynak.com) kendi uygulama anahtarıyla çalışır, kullanılmaz. Geçmiş bu yüzden kendi kayıtlarımızla birikir.

## Teknik analiz (sonraki aşama)
`sonuc.json` içindeki her hisseye şu alan eklenecek:
`teknik: {sinyal, ozet, gostergeler:[{ad, deger, yorum}], birlesik}`. Site bu alanı kod değişmeden gösterir.
Fiyat geçmişi kaynağı kullanıcıyla birlikte seçilecek.
