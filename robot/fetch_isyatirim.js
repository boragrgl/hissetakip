// İş Yatırım "Temel Değerler ve Oranlar" sayfasında (yerleşik tarayıcıda) çalıştırılır.
// Kullanım: TICKERS dizisini doldurup javascript_tool ile çalıştır; çıktı JSON metnidir.
// Çıktı: {asOf, market:[[kod,ad,sektor,kapanis,fk,fdfavok,fdsatis,pddd,sonDonem],...], fin:{KOD:{period,items:{kod:deger}}}}
const TICKERS = __TICKERS__;
const ITEMS = ["1A","1AA","1AB","1AC","1BL","2A","2AA","2BA","2N","2O","2OA","3C","3DF","4B","3Z"];
const num = s => { s = (s||"").trim(); if (!s || s === "A/D" || s === "-") return null;
  const v = parseFloat(s.replace(/\./g,"").replace(",", ".")); return isNaN(v) ? null : v; };
const cellsOf = t => [...t.tBodies[0].rows].map(r => [...r.cells].map(c => c.textContent.trim()));
const rowsOf = id => { const t = document.getElementById(id); return t && t.tBodies.length ? cellsOf(t) : []; };
// Tablolar sayfa yüklenince dolar; gerekirse bekle
for (let i = 0; i < 20 && rowsOf("summaryBasicData").length < 100; i++) await new Promise(r => setTimeout(r, 500));
const basic = Object.fromEntries(rowsOf("summaryBasicData").map(r => [r[0], r]));
const valTable = [...document.querySelectorAll("table")].find(t => t.tBodies.length && t.tHead && /FD\/Satışlar/.test(t.tHead.textContent) && /Son Dönem/.test(t.tHead.textContent));
if (!valTable) throw new Error("Değerleme tablosu bulunamadı — sayfa yapısı değişmiş olabilir");
const vals = cellsOf(valTable);
const market = vals.map(v => { const b = basic[v[0]] || []; return [v[0], b[1]||"", b[2]||"", num(v[1]), num(v[2]), num(v[3]), num(v[4]), num(v[5]), v[6]]; });
const mk = Object.fromEntries(market.map(m => [m[0], m]));
const fin = {};
for (const t of TICKERS) {
  const m = mk[t];
  if (!m) { fin[t] = {error: "Oran tablosunda bulunamadı"}; continue; }
  const [p, y] = (m[8]||"").split("/").map(Number);
  if (!p || !y) { fin[t] = {error: "Son dönem bilgisi yok"}; continue; }
  // İlgili dönem + bir önceki yılın aynı dönemi
  const u = `/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo?companyCode=${t}&exchange=TRY&financialGroup=XI_29&year1=${y}&period1=${p}&year2=${y-1}&period2=${p}&year3=${y-1}&period3=12&year4=${y-2}&period4=12`;
  try {
    const j = await fetch(u).then(r => r.json());
    const items = {}, prev = {};
    for (const x of (j.value||[])) if (ITEMS.includes(x.itemCode)) {
      items[x.itemCode] = x.value1 == null ? null : Number(x.value1);
      prev[x.itemCode] = x.value2 == null ? null : Number(x.value2);
    }
    fin[t] = items["1BL"] ? {period: `${y}/${p}`, items, prev} : {error: "Sanayi formatında mali tablo yok (banka/sigorta/aracı kurum olabilir)"};
  } catch (e) { fin[t] = {error: "Mali tablo alınamadı: " + e.message}; }
}
JSON.stringify({asOf: new Date().toISOString(), market, fin});
