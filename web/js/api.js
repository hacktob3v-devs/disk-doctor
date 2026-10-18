/*
 * Yerel sunucu (server.py) istemcisi.
 * Sunucu yoksa (ör. dosya statik açıldıysa) taklit motora (engine.js) düşer.
 */
window.ED_API = (function () {
  "use strict";

  const MODEL_KEY = "ed_pref_model";

  async function health() {
    try {
      const r = await fetch("/api/health", { cache: "no-store" });
      if (!r.ok) throw new Error(r.status);
      return await r.json();
    } catch {
      return null;
    }
  }

  function preferredModel() {
    try { return localStorage.getItem(MODEL_KEY) || null; } catch { return null; }
  }
  function setPreferredModel(name) {
    try { localStorage.setItem(MODEL_KEY, name); } catch { /* depolama kapalı */ }
  }

  // Sunucudaki çekirdek hattı çalıştırır; ulaşılamazsa taklit motoru kullanır.
  async function analyze(text, ctx) {
    try {
      const r = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          order: ctx.order,
          mode: ctx.mode || "question",
          stars: ctx.stars || 0,
          customer: ctx.customer || "",
          merchant: ctx.shop || "Usta Deri"
        })
      });
      if (!r.ok) throw new Error(r.status);
      const a = await r.json();
      a.backend = true;
      return a;
    } catch {
      const a = window.ED_ENGINE.analyze(text, ctx);
      const p = window.ED_POLICIES[a.policyId];
      a.policyTitle = p.title;
      a.policyText = p.text;
      a.backend = false;
      return a;
    }
  }

  // Yerel modelden kurala dayalı yanıt ister. Sunucu, kuralda geçmeyen sayı içeren
  // yanıtları reddeder. Dönüş: { text, model, grounded, attempts } ya da sunucu yoksa null.
  // text null ise çağıran kurala dayalı şablon yanıta düşer.
  async function generateReply(payload) {
    try {
      const r = await fetch("/api/reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, model: payload.model || preferredModel() })
      });
      if (!r.ok) return null;
      return await r.json();
    } catch {
      return null;
    }
  }

  // "qwen2.5:7b-instruct-q4_K_M" -> "Qwen 2.5 7B"
  function prettyModel(name) {
    if (!name) return "";
    const [base, tag = ""] = name.split(":");
    const fam = base.replace(/^([a-z]+)(\d[\d.]*)?$/i, (_, f, v) => f.charAt(0).toUpperCase() + f.slice(1) + (v ? " " + v : ""));
    const size = (tag.match(/(\d+(\.\d+)?)b/i) || [])[1];
    return size ? `${fam} ${size}B` : fam;
  }

  return { health, analyze, generateReply, preferredModel, setPreferredModel, prettyModel };
})();
