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
5. Commit ("veri: GG.AA.YYYY") ve `main`'e push.
6. Kullanıcıya kısa özet gönder. Hata olursa veri uydurma ve push yapma.

## Teknik analiz (sonraki aşama)
`sonuc.json` içindeki her hisseye şu alan eklenecek:
`teknik: {sinyal, ozet, gostergeler:[{ad, deger, yorum}], birlesik}`. Site bu alanı kod değişmeden gösterir.
Fiyat geçmişi kaynağı kullanıcıyla birlikte seçilecek.
