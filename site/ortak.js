// Hisse Takip — ortak yardımcılar (biçimlendirme + altın verisi)
window.HT = (() => {
  const tr = (x, d = 0) => x == null || isNaN(x) ? "—" : x.toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const pc = (x, d = 0) => x == null ? "—" : (x < 0 ? "-%" : "%") + tr(Math.abs(x) * 100, d);
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const parseTR = s => { const m = /(\d+)\.(\d+)\.(\d+) (\d+):(\d+)/.exec(s || ""); return m ? new Date(`${m[3]}-${m[2]}-${m[1]}T${m[4].padStart(2, "0")}:${m[5]}:00+03:00`) : null; };
  // Sıra kullanıcı isteğine göre: çeyrek, gram, hurda
  const TURLER = [["C", "Çeyrek altın"], ["GA", "Gram altın"], ["B_T", "22 ayar hurda"]];
  const altin = { hist: [], canli: null };

  // Bir türün zaman serisi: geçmiş kayıtlar + (daha yeniyse) canlı fiyat. tahmini=true → Altınkaynak dışı geçmiş (dosya / EVDS)
  function seri(kod, gun) {
    const s = altin.hist.map(k => ({ t: new Date(k.t), a: k[kod]?.[0], s: k[kod]?.[1], tahmini: !!k.kaynak, kaynak: k.kaynak || "altinkaynak" })).filter(p => p.s != null);
    const c = altin.canli?.kalemler?.find(x => x.kod === kod), t = parseTR(c?.guncelleme);
    if (c && c.satis != null && t && (!s.length || t > s[s.length - 1].t)) s.push({ t, a: c.alis, s: c.satis, tahmini: false, kaynak: "altinkaynak" });
    if (!gun) return s;
    const sinir = Date.now() - gun * 864e5;
    return s.filter(p => p.t.getTime() >= sinir);
  }
  // Son fiyatın 24 saat önceki (en yakın önceki) kayda göre değişimi
  function degisim(kod) {
    const s = seri(kod); if (s.length < 2) return null;
    const son = s[s.length - 1], hedef = son.t.getTime() - 864e5;
    let ref = null; for (const p of s) if (p.t.getTime() <= hedef) ref = p;
    return ref ? son.s / ref.s - 1 : null;
  }
  function son(kod) {
    const c = altin.canli?.kalemler?.find(x => x.kod === kod);
    if (c && c.satis != null) return { a: c.alis, s: c.satis, t: parseTR(c.guncelleme) };
    const s = seri(kod); const p = s[s.length - 1];
    return p ? { a: p.a, s: p.s, t: p.t } : null;
  }
  async function altinYukle(cb) {
    try { altin.hist = (await fetch("data/altin-gecmis.json", { cache: "no-store" }).then(r => r.json())).kayitlar || []; } catch (e) { altin.hist = []; }
    cb();
    const canli = async () => {
      try { const r = await fetch("api/altin", { cache: "no-store" }); const j = r.ok ? await r.json() : null; altin.canli = j && j.kalemler ? j : null; } catch (e) { altin.canli = null; }
      cb();
    };
    canli(); setInterval(canli, 60000);
  }
  // KPI kartı. link verilirse <a>, verilmezse seçilebilir <button>
  function kpi(kod, ad, { link, secili } = {}) {
    const p = son(kod), d = degisim(kod);
    const ic = `<span class="ad"><span>${ad}</span>${link ? '<span class="chev">›</span>' : ""}</span>
      <span class="fiyat">${p ? tr(p.s) + " ₺" : "—"}</span>
      <span class="alt"><span>Alış ${p ? tr(p.a) + " ₺" : "—"}</span>${d == null ? "" : `<span class="pill ${d >= 0 ? "up" : "down"}">${d >= 0 ? "+" : "−"}${tr(Math.abs(d) * 100, 2)}%</span>`}</span>`;
    return link ? `<a class="kpi" href="${link}">${ic}</a>` : `<button class="kpi" data-k="${kod}" aria-pressed="${!!secili}">${ic}</button>`;
  }
  function zaman() {
    const p = son("GA"); if (!p || !p.t) return "";
    return `Altınkaynak · ${p.t.toLocaleString("tr-TR", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" })}${altin.canli ? "" : " (son kayıt)"}`;
  }
  return { tr, pc, esc, parseTR, TURLER, altin, seri, degisim, son, altinYukle, kpi, zaman };
})();
