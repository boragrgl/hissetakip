// Hisse Takip — ortak yardımcılar (biçimlendirme + altın verisi)
window.HT = (() => {
  const tr = (x, d = 0) => x == null || isNaN(x) ? "—" : x.toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const pc = (x, d = 0) => x == null ? "—" : (x < 0 ? "-%" : "%") + tr(Math.abs(x) * 100, d);
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const parseTR = s => { const m = /(\d+)\.(\d+)\.(\d+) (\d+):(\d+)/.exec(s || ""); return m ? new Date(`${m[3]}-${m[2]}-${m[1]}T${m[4].padStart(2, "0")}:${m[5]}:00+03:00`) : null; };
  // [kod, ad, para birimi, ondalık]. Sıra: çeyrek, gram, 22 ayar hurda, ons
  const TURLER = [["C", "Çeyrek altın", "₺", 0], ["GA", "Gram altın", "₺", 0], ["B_T", "22 ayar hurda", "₺", 0], ["XAUUSD", "Ons altın", "$", 2]];
  const tur = kod => TURLER.find(t => t[0] === kod) || TURLER[0];
  const para = (kod, v) => { const [, , b, d] = tur(kod); return v == null ? "—" : b === "$" ? "$" + tr(v, d) : tr(v, d) + " ₺"; };
  const altin = { hist: [], canli: null };
  const gunu = t => t.toLocaleDateString("sv-SE", { timeZone: "Europe/Istanbul" });

  // Bir türün zaman serisi: geçmiş kayıtlar + (daha yeniyse) canlı fiyat. tahmini=true → Altınkaynak dışı geçmiş (dosya / EVDS)
  function seri(kod, gun) {
    const s = altin.hist.map(k => ({ t: new Date(k.t), a: k[kod]?.[0], s: k[kod]?.[1], tahmini: !!k.kaynak, kaynak: k.kaynak || "altinkaynak" })).filter(p => p.s != null);
    const c = altin.canli?.kalemler?.find(x => x.kod === kod), t = parseTR(c?.guncelleme);
    if (c && c.satis != null && t && (!s.length || t > s[s.length - 1].t)) s.push({ t, a: c.alis, s: c.satis, tahmini: false, kaynak: "altinkaynak" });
    if (!gun) return s;
    const sinir = Date.now() - gun * 864e5;
    return s.filter(p => p.t.getTime() >= sinir);
  }
  // Son fiyatın bir önceki günün son fiyatına göre değişimi
  function degisim(kod) {
    const s = seri(kod); if (s.length < 2) return null;
    const son = s[s.length - 1], g = gunu(son.t);
    let ref = null; for (const p of s) if (gunu(p.t) < g) ref = p;
    return ref ? son.s / ref.s - 1 : null;
  }
  // Son fiyatın olduğu günün en yüksek / en düşük satış fiyatı (Altınkaynak kayıtları + canlı)
  function gunAraligi(kod) {
    const s = seri(kod).filter(p => !p.tahmini); if (!s.length) return null;
    const g = gunu(s[s.length - 1].t), bugun = s.filter(p => gunu(p.t) === g).map(p => p.s);
    return { yuksek: Math.max(...bugun), dusuk: Math.min(...bugun), n: bugun.length, gun: s[s.length - 1].t };
  }
  function son(kod) {
    const c = altin.canli?.kalemler?.find(x => x.kod === kod);
    if (c && c.satis != null) return { a: c.alis, s: c.satis, t: parseTR(c.guncelleme) };
    const s = seri(kod).filter(p => !p.tahmini); const p = s[s.length - 1];
    return p ? { a: p.a, s: p.s, t: p.t } : null;
  }
  async function altinYukle(cb) {
    try { altin.hist = (await fetch("data/altin-gecmis.json", { cache: "no-store" }).then(r => r.json())).kayitlar || []; } catch (e) { altin.hist = []; }
    cb();
    const canli = async () => {
      try { const r = await fetch(window.HT_API || "api/altin", { cache: "no-store" }); const j = r.ok ? await r.json() : null; altin.canli = j && j.kalemler ? j : null; } catch (e) { altin.canli = null; }
      cb();
    };
    canli(); setInterval(canli, 60000);
  }
  function zaman() {
    const p = son("GA"); if (!p || !p.t) return "";
    return p.t.toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }
  const degisimHtml = d => d == null ? `<span class="pct">—</span>` : `<span class="pct ${d >= 0 ? "up" : "down"}">${d < 0 ? "-" : ""}%${tr(Math.abs(d) * 100, 2)}</span>`;
  return { tr, pc, esc, parseTR, TURLER, tur, para, altin, seri, degisim, gunAraligi, son, altinYukle, zaman, degisimHtml };
})();
