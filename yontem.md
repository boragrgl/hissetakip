# Temel Analiz Yöntemi — Hisse Seçimi Maddeleri

Kaynak: kullanıcının "Hisse Seçimi Maddeleri" dokümanı. Robot bu kuralları `robot/temel_analiz.py` ile mekanik olarak uygular. Eşikler kodun başındaki `CFG` bölümündedir. Bu doküman ile kod uyumlu tutulmalıdır.

## Veri
- **Mali tablolar:** İş Yatırım MaliTablo verisi (sanayi formatı XI_29), son açıklanan dönem. Gelir tablosu kalemleri yıl başından kümülatiftir.
- **Fiyat ve oranlar:** İş Yatırım "Temel Değerler ve Oranlar" sayfası. Kapanış, F/K, PD/DD, FD/FAVÖK, FD/Satış ve sektör bilgisi tüm BIST için alınır.
- **Sektör ortalaması:** Aynı sektördeki şirketlerin **medyanı**. Negatif ve hesaplanamayan (A/D) değerler dışarıda bırakılır. Geçerli şirket sayısı 3'ten azsa piyasa medyanı kullanılır.
- **Sektör FAVÖK marjı:** FD/Satış ÷ FD/FAVÖK formülüyle her şirket için hesaplanır, sonra sektör medyanı alınır.
- **Kapsam dışı:** Bankalar, sigorta şirketleri ve aracı kurumlar. Bilanço yapıları bu maddelere uymaz, raporda "VERİ YOK" olarak görünürler.

## Maddeler
| # | Madde | Hesap | Geçme kuralı |
|---|---|---|---|
| 1 | Net işletme sermayesi | (Dönen varlıklar − KV yükümlülükler) / KV yükümlülükler | ≥ %20 → GEÇTİ · %0–20 → SINIRDA · < %0 → KALDI. İdeal: dönen varlıklar ≥ 2 × KVB |
| 2 | Nakit durumu | (Nakit + KV finansal yatırımlar) / KV finansal borçlar | ≥ %50 → GEÇTİ. KV finansal borç yoksa GEÇTİ. Ticari alacak / dönen varlık > %40 ise dipnot uyarısı |
| 3 | Mali yapı | Özkaynaklar / Toplam varlıklar | ≥ %60 GÜÇLÜ · %40–60 DENGELİ · ≤ %40 GÜÇSÜZ |
| 4 | Kârlılık | FAVÖK marjı = (Faaliyet kârı + Amortisman) / Net satışlar | Sektör medyanından yüksekse GEÇTİ |
| ★ | Bonus (bedelsiz potansiyeli) | Özkaynaklar / Ödenmiş sermaye | ≥ 10x VAR · ≥ 40x GÜÇLÜ · ≥ 100x ZİRVE ("al yaslan") |

FAVÖK marjı %100'ü aşarsa marj güvenilmez sayılır ve kârlılık maddesi değerlendirilmez. Bu durum genellikle satışı çok düşük holding ve GYO'larda görülür.

## Hedef fiyat
- PD/DD hedef = (Sektör PD/DD / Şirket PD/DD) × Fiyat
- F/K hedef = (Sektör F/K / Şirket F/K) × Fiyat. Şirket zarardaysa F/K hesaplanmaz ve hedef yalnız PD/DD'ye göre belirlenir.
- Ana hedef = (PD/DD hedef + F/K hedef) / 2
- Fark = Hedef − Fiyat · Potansiyel = Fark / Fiyat × 100

## Karar (yüksek faiz ortamı)
Kurallar sırayla uygulanır. İlk tutan kural kararı belirler.
1. **UZAK DUR:** Mali yapı güçsüz ve FAVÖK negatif ya da sektör marjının %90'ının altında.
2. **İZLEME (BSA FIRSATI):** Madde 1 veya 2'den kalan şirketler. Bunlar alınmaz, izleme listesinde tutulur. Bedelli sermaye artışı onayından sonraki sert düşüş olası giriş noktasıdır.
3. **ALIM ADAYI:** Madde 1 ve 2'yi geçmiş, mali yapısı güçlü ya da dengeli ve FAVÖK marjı sektörün üstünde. Mali yapı dengeliyse borcun "iyi borç" olup olmadığı kontrol edilir.
4. **KOŞULLU:** Geri kalanlar. Örnek: Madde 1 sınırda, FAVÖK marjı sektörün altında ya da mali yapı güçsüz ama FAVÖK sektör civarında.

Her kategori kendi içinde FAVÖK marjına göre sıralanır (Madde 4: marjı yüksek olan tercih edilir).

## Robotun yapamadıkları (elle kontrol)
- Ticari alacak dipnotlarında teminatlı ve şüpheli alacak ayrımı
- Borcun "iyi borç" mu "kötü borç" mu olduğu (finansman gideri trendi, yatırım geliri)
- Takas durumu ve teknik görünüm (teknik analiz modülü ayrıca eklenecek)

_Bu robot kuralların mekanik uygulamasıdır; yatırım tavsiyesi değildir._
