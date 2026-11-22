// Hisse Takip — Cloudflare Worker
// /api/altin : Altınkaynak'ın herkese açık altın servisinden (https://www.altinkaynak.com/Araclar/Servisler)
//              gram altın, çeyrek ve 22 ayar hurda fiyatlarını döndürür. 60 sn önbellekli.
// Diğer tüm adresler: site/ klasöründeki statik dosyalar.

const KAYNAK = "https://static.altinkaynak.com/public/Gold";
const SECILI = [
  { kod: "GA", ad: "Gram altın" },
  { kod: "C", ad: "Çeyrek altın" },
  { kod: "B_T", ad: "22 ayar hurda" },
];

// "6.013" → 6013, "63,06" → 63.06
const sayi = (s) => {
  const v = parseFloat(String(s ?? "").replace(/\./g, "").replace(",", "."));
  return Number.isFinite(v) ? v : null;
};

const json = (obj, status = 200, extra = {}) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...extra },
  });

async function altin(req, ctx) {
  const cache = caches.default;
  const key = new Request(new URL("/api/altin", req.url).toString());
  const hit = await cache.match(key);
  if (hit) return hit;
  let up;
  try {
    up = await fetch(KAYNAK, { headers: { accept: "application/json" } });
  } catch (e) {
    return json({ hata: "Altınkaynak'a ulaşılamadı" }, 502);
  }
  if (!up.ok) return json({ hata: `Altınkaynak yanıtı ${up.status}` }, 502);
  const liste = await up.json();
  const kalemler = SECILI.map(({ kod, ad }) => {
    const x = liste.find((i) => i.Kod === kod);
    return x
      ? { kod, ad, alis: sayi(x.Alis), satis: sayi(x.Satis), degisim: x.Change ?? null, guncelleme: x.GuncellenmeZamani }
      : { kod, ad, alis: null, satis: null, degisim: null, guncelleme: null };
  });
  const res = json({ kaynak: "Altınkaynak", kalemler }, 200, { "cache-control": "public, max-age=60" });
  ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}

export default {
  async fetch(req, env, ctx) {
    const { pathname } = new URL(req.url);
    if (pathname === "/api/altin") return altin(req, ctx);
    return env.ASSETS.fetch(req);
  },
};
