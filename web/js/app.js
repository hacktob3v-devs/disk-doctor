(function () {
  "use strict";

  const { POLICIES, CASES, SOURCES } = window.ED_DATA;

  const CATEGORY = { kargo: "Kargo", iade: "İade", urun: "Ürün", teknik: "Ödeme", genel: "Genel" };
  const INTENT = { sikayet: "Şikâyet", bilgi_talebi: "Bilgi talebi", tesekkur: "Teşekkür" };
  const PRIORITY = { acil: "Acil", yuksek: "Yüksek öncelik", orta: "Normal", dusuk: "Düşük" };
  const LEVEL = { green: "Güvenli", yellow: "İncele", red: "Yüksek risk" };
  const API = window.ED_API;
  const modelName = () => API.prettyModel(state.model) || "Yerel model";

  const ICON = {
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/>',
    speak: '<path d="M4 10v4h4l5 4V6L8 10H4z"/><path d="M16.5 9a4 4 0 0 1 0 6M19 6.5a7.5 7.5 0 0 1 0 11"/>',
    chat: '<path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4.2A8 8 0 1 1 20 12z"/>',
    redo: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 5v6h-6"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    check: '<path d="m5 12 4.5 4.5L19 7"/>'
  };
  const icon = (name) => `<svg viewBox="0 0 24 24" class="ico" aria-hidden="true">${ICON[name]}</svg>`;

  const tl = { format: (n) => `${Math.round(n).toLocaleString("tr-TR")} TL` };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const $ = (sel) => document.querySelector(sel);

  const SHARED = window.ED_SHARED;

  const hydrate = (c) => ({
    ...c,
    order: { ...c.order },
    analysis: { ...c.analysis, risk: { ...c.analysis.risk } },
    done: !!c.done,
    ts: c.ts || (String(c.id).startsWith("w") ? Number(String(c.id).slice(1)) : 0),
    draft: c.auto ? c.sentReply : c.analysis.reply,
    checks: []
  });

  const state = {
    // Müşteri sayfasından gelenler önce, demo vakaları sonra
    cases: SHARED.readInbox().map(hydrate).concat(CASES.map(hydrate)),
    selectedId: null,
    filter: "all",
    query: "",
    editing: false,
    model: window.ED_API.preferredModel() || "",
    runToken: 0
  };

  const current = () => state.cases.find((c) => c.id === state.selectedId);

  /* ---------------- Gelen kutusu ---------------- */

  function visibleCases() {
    const q = state.query.trim().toLocaleLowerCase("tr");
    return state.cases
      .filter((c) => {
        if (state.filter === "acil" && c.analysis.priority !== "acil") return false;
        if (["iade", "kargo", "urun"].includes(state.filter) && c.analysis.category !== state.filter) return false;
        if (!q) return true;
        return [c.customer, c.order.id, c.message, c.order.product].join(" ").toLocaleLowerCase("tr").includes(q);
      })
      .sort((a, b) => (a.done - b.done) || (b.ts - a.ts) || b.time.localeCompare(a.time));
  }

  function renderQueue() {
    const list = visibleCases();
    const open = state.cases.filter((c) => !c.done).length;
    $("#openCount").textContent = open ? `${open} açık` : "hepsi yanıtlandı";

    if (!list.length) {
      $("#queue").innerHTML = `<li class="empty-q">Bu filtrede mesaj yok.</li>`;
      return;
    }

    $("#queue").innerHTML = list.map((c) => {
      const a = c.analysis;
      const src = SOURCES[c.source];
      const statusTag = c.auto
        ? `<span class="tag auto">${icon("check")} Otomatik yanıtlandı</span>`
        : c.done
        ? `<span class="tag done">${icon("check")} Yanıtlandı</span>`
        : `<span class="tag ${a.risk.level}"><span class="dot"></span>${LEVEL[a.risk.level]}</span>`;
      return `
        <li class="q-item${c.id === state.selectedId ? " is-selected" : ""}${c.done ? " is-done" : ""}" data-id="${c.id}" tabindex="0">
          ${c.unread && !c.done ? '<span class="unread-dot" aria-label="Okunmadı"></span>' : ""}
          <span class="src" title="${src.label}">${src.short}</span>
          <div>
            <div class="q-top">
              <span class="q-name">${esc(c.customer)}</span>
              <span class="q-time num">${c.time}</span>
            </div>
            <p class="q-preview">${esc(c.message)}</p>
            <div class="q-meta">
              ${statusTag}
              <span class="tag">${CATEGORY[a.category]}</span>
              ${a.priority === "acil" && !c.done ? '<span class="tag red">Acil</span>' : ""}
            </div>
          </div>
        </li>`;
    }).join("");
  }

  /* ---------------- Vaka ---------------- */

  function ledgerRow(label, value, input) {
    return `<div class="ledger-row"><dt>${label}</dt><span class="leader"></span><dd>${state.editing && input ? input : value}</dd></div>`;
  }

  function yn(key, val) {
    return `<span class="yn" data-key="${key}">
      <button type="button" data-v="1" class="${val ? "is-on" : ""}">Var</button>
      <button type="button" data-v="0" class="${!val ? "is-on" : ""}">Yok</button>
    </span>`;
  }

  function renderCase() {
    const c = current();
    const pane = $("#casePane");
    if (!c) {
      pane.innerHTML = `<div class="all-done"><div><p class="eyebrow">Gelen kutusu</p><h2>Bugünlük bu kadar, usta.</h2><p>Bekleyen mesaj kalmadı.</p></div></div>`;
      return;
    }
    const o = c.order;
    const a = c.analysis;
    const src = SOURCES[c.source];
    const returnRate = o.pastOrders ? Math.round((o.pastReturns / o.pastOrders) * 100) : 0;

    pane.innerHTML = `
      <article class="case">
        <button class="btn btn-ghost back" type="button" data-act="back">${icon("back")} Gelen kutusu</button>

        <header class="case-head">
          <div>
            <p class="eyebrow">${src.label} · ${INTENT[a.intent]}</p>
            <h1 class="case-name">${esc(c.customer)}</h1>
            <div class="case-sub">
              <span class="mono">${esc(o.id)}</span><span class="sep">/</span>
              <span>${esc(o.product)}</span><span class="sep">/</span>
              <span class="num">Bugün ${c.time}</span>
            </div>
          </div>
        </header>

        <div class="letter">
          <p>${esc(c.message)}</p>
          <div class="letter-foot"><span>${src.label} üzerinden</span><span class="num">${c.message.length} karakter</span></div>
        </div>

        <div class="section-h">
          <h3>Sipariş defteri</h3>
          <button class="link-btn" type="button" data-act="edit">${state.editing ? "Kaydet ve yeniden değerlendir" : "Düzenle"}</button>
        </div>
        <dl class="ledger">
          ${ledgerRow("Tutar", `<span class="num">${tl.format(o.amount)}</span>`, `<input type="number" data-field="amount" value="${o.amount}" step="50" min="0">`)}
          ${ledgerRow("Kargoda geçen süre", `<span class="num">${o.deliveryDays ? o.deliveryDays + " gün" : "Henüz kargoda değil"}</span>`, `<input type="number" data-field="deliveryDays" value="${o.deliveryDays}" min="0">`)}
          ${ledgerRow("Paket hasarlı bildirildi", o.boxDamaged ? "Evet" : "Hayır", yn("boxDamaged", o.boxDamaged))}
          ${ledgerRow("Açılış videosu", o.unboxingVideo ? "Var" : "Yok", yn("unboxingVideo", o.unboxingVideo))}
          ${ledgerRow("Geçmiş sipariş / iade", `<span class="num">${o.pastOrders} / ${o.pastReturns}</span>`,
            `<input type="number" data-field="pastOrders" value="${o.pastOrders}" min="0" style="width:56px"> / <input type="number" data-field="pastReturns" value="${o.pastReturns}" min="0" style="width:56px">`)}
        </dl>

        <div class="section-h"><h3>Müşteri geçmişi</h3></div>
        <div class="history">
          <div class="stat"><div class="stat-label">Sipariş</div><div class="stat-value num">${o.pastOrders}</div></div>
          <div class="stat"><div class="stat-label">İade</div><div class="stat-value num">${o.pastReturns}</div></div>
          <div class="stat"><div class="stat-label">İade oranı</div><div class="stat-value num">%${returnRate}</div><div class="bar"><span style="width:${Math.min(100, returnRate)}%"></span></div></div>
        </div>

        <div class="section-h"><h3>Değerlendirme adımları</h3><span class="muted" style="font-size:12px">bu bilgisayarda</span></div>
        <ol class="trace" id="trace">${traceItems(c, -1)}</ol>
      </article>`;
  }

  function traceSteps(c) {
    const a = c.analysis;
    const p = POLICIES[a.policyId];
    return [
      { name: "Mesajı anlama", detail: `${CATEGORY[a.category]} · ${INTENT[a.intent]} · güven %${Math.round(a.confidence * 100)}`, ms: a.timings.nlu, model: "BERTurk" },
      { name: "Mağaza kuralını bulma", detail: `${a.policyId} · ${p.title}`, ms: a.timings.rag, model: "BM25 + E5" },
      { name: "Sipariş riskini hesaplama", detail: `%${Math.round(a.risk.score * 100)} · ${LEVEL[a.risk.level]}`, ms: a.timings.risk, model: "TabPFN" },
      { name: "Karar ve yanıt taslağı", detail: `${modelName()} · Ollama`, ms: a.timings.llm, model: modelName() }
    ];
  }

  // doneUpTo: -1 hepsi tamam, aksi halde o indekse kadar tamam ve sıradaki çalışıyor
  function traceItems(c, doneUpTo) {
    return traceSteps(c).map((s, i) => {
      let cls = "is-done";
      if (doneUpTo >= 0) cls = i < doneUpTo ? "is-done" : i === doneUpTo ? "is-run" : "is-pending";
      const ms = cls === "is-done" ? `${s.ms.toLocaleString("tr-TR")} ms` : cls === "is-run" ? "çalışıyor…" : "";
      return `<li class="${cls}"><div class="t-row"><span class="t-name">${s.name}</span><span class="t-ms num">${ms}</span></div><div class="t-detail">${esc(s.detail)}</div></li>`;
    }).join("");
  }

  /* ---------------- Karar ---------------- */

  function renderDecision(loading) {
    const c = current();
    const pane = $("#decisionPane");
    if (!c) { pane.innerHTML = ""; return; }
    const a = c.analysis;
    const p = POLICIES[a.policyId];
    const score = Math.round(a.risk.score * 100);
    const checked = c.checks.filter(Boolean).length;
    const total = a.steps.length;

    pane.innerHTML = `
      <div class="decision${loading ? " is-loading" : ""}">
        <div class="verdict reveal">
          <div>
            <p class="eyebrow">Önerilen karar</p>
            <h2 class="verdict-title">${esc(a.action)}</h2>
            <div class="verdict-meta">
              <span class="tag ${a.priority === "acil" ? "red" : a.priority === "yuksek" ? "yellow" : ""}">${PRIORITY[a.priority]}</span>
              <span class="tag">${CATEGORY[a.category]}</span>
            </div>
          </div>
          <div class="stamp ${a.risk.level}${loading ? "" : " pop"}" title="Sipariş risk skoru">
            <div><div class="stamp-score num">%${loading ? "–" : score}</div><div class="stamp-label">${LEVEL[a.risk.level]}</div></div>
          </div>
        </div>

        <section class="card reveal">
          <div class="card-h"><h4>Riski etkileyenler</h4></div>
          <ul class="drivers">
            ${a.risk.drivers.map((d) => `<li><span class="arrow ${d.dir}">${d.dir === "up" ? "▲" : "▼"}</span>${esc(d.label)}</li>`).join("")}
          </ul>
        </section>

        <section class="card reveal">
          <div class="card-h"><h4>Yapılacaklar</h4><span class="progress num">${checked}/${total}</span></div>
          <ol class="checklist">
            ${a.steps.map((s, i) => `<li><label><input type="checkbox" data-step="${i}" ${c.checks[i] ? "checked" : ""}><span>${esc(s)}</span></label></li>`).join("")}
          </ol>
        </section>

        <section class="card reveal">
          <div class="rule">
            <div class="rule-id">${a.policyId}</div>
            <div class="rule-title">${esc(p.title)}</div>
            <button class="link-btn" type="button" data-act="rule" style="margin-top:8px">Kural metnini göster</button>
            <blockquote class="rule-text" id="ruleText" hidden>${esc(p.text)}</blockquote>
          </div>
        </section>

        <section class="card reply-wrap reveal">
          <div class="card-h">
            <h4>${c.auto ? "Müşteriye gönderilen yanıt" : "Müşteriye yanıt"}</h4>
            ${c.auto ? "" : `<button class="link-btn" type="button" data-act="regen">${icon("redo")} Yeniden yaz</button>`}
          </div>
          <textarea class="reply" id="reply" spellcheck="false" aria-label="Müşteriye gidecek yanıt"${c.auto ? " readonly" : ""}>${esc(loading ? "" : c.draft)}</textarea>
          <div class="reply-foot">
            <span class="hint num" id="replyCount">${loading ? "Taslak hazırlanıyor…" : c.auto ? "Mağaza sitesinde otomatik gönderildi" : c.draft.length + " karakter"}</span>
            <div class="reply-actions">
              <button class="icon-btn" type="button" data-act="speak" title="Kararı sesli oku">${icon("speak")}</button>
              <button class="icon-btn" type="button" data-act="whatsapp" title="WhatsApp'ta aç">${icon("chat")}</button>
              <button class="icon-btn" type="button" data-act="copy" title="Kopyala (C)">${icon("copy")}</button>
            </div>
          </div>
        </section>

        <div class="decide reveal">
          <button class="btn btn-primary" type="button" data-act="approve"${c.done ? " disabled" : ""}>${c.auto ? "Otomatik yanıtlandı" : c.done ? "Yanıtlandı" : "Onayla, sıradakine geç"} <kbd>E</kbd></button>
        </div>
        <p class="disclaimer">Bu bir öneridir. Gönderilen her yanıtı siz onaylarsınız.</p>
      </div>`;
  }

  /* ---------------- Değerlendirme animasyonu ---------------- */

  // Gerçek süreleri sahnede okunabilir kılmak için sıkıştırır.
  const STAGE_MS = [180, 240, 160, 520];

  function runAnalysis() {
    const c = current();
    if (!c) return;
    const token = ++state.runToken;
    renderDecision(true);
    let i = 0;
    const tick = () => {
      if (token !== state.runToken) return;
      const trace = $("#trace");
      if (trace) trace.innerHTML = traceItems(c, i);
      if (i >= STAGE_MS.length) {
        if (trace) trace.innerHTML = traceItems(c, -1);
        renderDecision(false);
        if (SHARED.getPref("autoSpeakSeller", false) && !c.done) speak();
        return;
      }
      setTimeout(() => { i++; tick(); }, STAGE_MS[i]);
    };
    tick();
  }

  /* ---------------- Yerel sunucu ile yeniden değerlendirme ---------------- */

  async function reevaluate(c) {
    renderCase();
    const a = await API.analyze(c.message, { order: c.order, customer: c.customer, shop: "Usta Deri" });
    if (a.backend) {
      c.analysis = { ...a, risk: { ...a.risk } };
      if (!c.auto) c.draft = a.reply;
      c.checks = [];
    } else {
      recomputeRisk(c);
    }
    if (current() !== c) return;
    renderCase();
    runAnalysis();
    toast("Sipariş bilgisi güncellendi, yeniden değerlendirildi");
  }

  async function regenerate(c) {
    const box = $("#reply");
    const count = $("#replyCount");
    box.value = "";
    count.textContent = "Yerel model yazıyor, kural denetleniyor…";
    const p = POLICIES[c.analysis.policyId];
    const res = await API.generateReply({
      message: c.message, policyTitle: p.title, policyText: p.text,
      customer: c.customer, merchant: "Usta Deri", audience: "merchant_draft", model: state.model || null
    });
    const ok = res && res.text;
    c.draft = ok ? res.text : c.analysis.reply;
    if (current() !== c) return;
    box.value = c.draft;
    count.textContent = ok
      ? `${API.prettyModel(res.model)} · kural denetimi ✓`
      : res && res.model ? "Model kural dışı bilgi yazdı · şablon yanıt" : "Model kapalı · şablon yanıt";
  }

  /* ---------------- Risk yeniden hesap (sunucusuz önizleme) ---------------- */

  function recomputeRisk(c) {
    const o = c.order;
    const rate = o.pastOrders ? o.pastReturns / o.pastOrders : 0;
    let s = 0.05;
    s += Math.min(0.3, rate * 0.35);
    s += o.amount > 3000 ? 0.15 : o.amount > 1200 ? 0.07 : 0;
    s += o.unboxingVideo ? -0.06 : 0.08;
    s += o.boxDamaged ? 0.08 : 0;
    s += o.deliveryDays > 4 ? 0.04 : 0;
    s += c.analysis.sentiment < -0.6 ? 0.12 : 0;
    s = Math.max(0.01, Math.min(0.97, s));

    const drivers = [];
    if (rate >= 0.5) drivers.push({ label: `İade oranı %${Math.round(rate * 100)} (${o.pastReturns}/${o.pastOrders})`, dir: "up" });
    else drivers.push({ label: `${o.pastOrders} sipariş, ${o.pastReturns} iade`, dir: "down" });
    if (o.amount > 1200) drivers.push({ label: `Yüksek tutar · ${tl.format(o.amount)}`, dir: "up" });
    drivers.push({ label: o.unboxingVideo ? "Açılış videosu var" : "Açılış videosu yok", dir: o.unboxingVideo ? "down" : "up" });
    if (o.boxDamaged) drivers.push({ label: "Paket hasarlı bildirildi", dir: "up" });

    c.analysis.risk = { score: s, level: s >= 0.6 ? "red" : s >= 0.25 ? "yellow" : "green", drivers };
  }

  /* ---------------- Seçim ve gezinme ---------------- */

  function select(id, opts = {}) {
    state.selectedId = id;
    state.editing = false;
    const c = current();
    if (c) c.unread = false;
    document.body.classList.toggle("has-case", !!c && !opts.silentMobile);
    renderQueue();
    renderCase();
    if (c) runAnalysis(); else renderDecision();
    $("#casePane").scrollTop = 0;
    $("#decisionPane").scrollTop = 0;
    const el = document.querySelector(`.q-item[data-id="${id}"]`);
    if (el) el.scrollIntoView({ block: "nearest" });
  }

  function move(delta) {
    const list = visibleCases();
    if (!list.length) return;
    const idx = list.findIndex((c) => c.id === state.selectedId);
    const next = list[Math.max(0, Math.min(list.length - 1, idx + delta))];
    if (next && next.id !== state.selectedId) select(next.id);
  }

  function approve() {
    const c = current();
    if (!c || c.done) return;
    c.done = true;
    toast(`${c.customer.split(" ")[0]} için yanıt onaylandı`);
    const list = visibleCases().filter((x) => !x.done || x.id === c.id);
    const idx = list.findIndex((x) => x.id === c.id);
    const next = list.slice(idx + 1).concat(list.slice(0, idx)).find((x) => !x.done);
    if (next) select(next.id);
    else { state.selectedId = null; renderQueue(); renderCase(); renderDecision(); document.body.classList.remove("has-case"); }
  }

  async function copyReply() {
    const c = current();
    if (!c) return;
    try { await navigator.clipboard.writeText(c.draft); toast("Yanıt panoya kopyalandı"); }
    catch { toast("Kopyalanamadı; metni elle seçin"); }
  }

  // Esnafa yalnızca karar özetini okur; kural kodu, sipariş no ve yanıt metni okunmaz.
  const SPOKEN_LEVEL = { green: "Risk düşük.", yellow: "İnceleme gerekli", red: "Yüksek risk" };
  const SPOKEN_PRIORITY = { acil: "Acil.", yuksek: "Öncelikli.", orta: "", dusuk: "" };

  function speak() {
    const c = current();
    if (!c) return;
    const a = c.analysis;
    const text = `${c.customer.split(" ")[0]}, ${CATEGORY[a.category].toLocaleLowerCase("tr")}. ${SPOKEN_PRIORITY[a.priority]} `
      + `Öneri: ${a.action}. ${SPOKEN_LEVEL[a.risk.level]}${a.risk.level === "green" ? "" : `, yüzde ${Math.round(a.risk.score * 100)}.`}`;
    if (!SHARED.speak(text)) toast("Bu tarayıcı sesli okumayı desteklemiyor");
  }

  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("is-on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("is-on"), 2200);
  }

  /* ---------------- Nasıl çalışıyor ---------------- */

  function renderHow() {
    const handled = 2184;
    $("#howBody").innerHTML = `
      <h3>Bir mesaj geldiğinde</h3>
      <ol class="pipeline">
        <li><div><div class="p-name">Mesajı anlama</div><div class="p-desc">Kategori ve niyet; Türkçe e-ticaret verisiyle ince ayarlı.</div></div><div class="p-model">BERTurk</div></li>
        <li><div><div class="p-name">Mağaza kuralını bulma</div><div class="p-desc">Anahtar kelime ve anlam araması birleştirilir, en uygun kural seçilir.</div></div><div class="p-model">BM25 + E5<br>RRF · rerank</div></li>
        <li><div><div class="p-name">Sipariş riskini hesaplama</div><div class="p-desc">Tutar, iade geçmişi, açılış videosu ve kargo verisinden olasılık.</div></div><div class="p-model">TabPFN</div></li>
        <li><div><div class="p-name">Karar ve yanıt taslağı</div><div class="p-desc">Yalnızca bulunan kurala dayanır; kuralda olmayan süre veya tutar yazmaz.</div></div><div class="p-model">${modelName()}<br>Ollama</div></li>
      </ol>

      <h3>Bu ay</h3>
      <div class="figures">
        <div class="figure"><b class="num">${handled.toLocaleString("tr-TR")}</b><span>mesaj değerlendirildi</span></div>
        <div class="figure"><b class="num">0,00 TL</b><span>API maliyeti</span></div>
        <div class="figure"><b class="num">0</b><span>dışarı giden müşteri verisi</span></div>
      </div>

      <h3>Neden bulut API değil</h3>
      <table class="compare">
        <thead><tr><th></th><th>Kapalı bulut API</th><th>EsnafDoktor</th></tr></thead>
        <tbody>
          <tr><td>Maliyet</td><td>Mesaj başına ücret, ayda ≈ 15.000 TL</td><td>Sıfır; dükkân bilgisayarında</td></tr>
          <tr><td>İnternet</td><td>Kesilince durur</td><td>Wi-Fi kapalıyken çalışır</td></tr>
          <tr><td>Müşteri verisi</td><td>Yurt dışı sunuculara gider</td><td>Bu diskten çıkmaz (KVKK)</td></tr>
          <tr><td>Kilitlenme</td><td>Fiyat ve model sağlayıcıda</td><td>Model üstten değiştirilir</td></tr>
        </tbody>
      </table>

      <h3>Demo</h3>
      <p>Müşteri sayfasından gelen mesajlar bu tarayıcıda saklanır. Sunumdan önce temizleyin.</p>
      <button class="btn btn-secondary" type="button" id="resetDemo">Demo verisini sıfırla</button>`;
  }

  function openHow() {
    renderHow();
    $("#scrim").hidden = false;
    $("#howDrawer").classList.add("is-open");
    $("#howDrawer").setAttribute("aria-hidden", "false");
    $("#closeHow").focus();
  }
  function closeHow() {
    $("#scrim").hidden = true;
    $("#howDrawer").classList.remove("is-open");
    $("#howDrawer").setAttribute("aria-hidden", "true");
  }

  /* ---------------- Olaylar ---------------- */

  $("#queue").addEventListener("click", (e) => {
    const li = e.target.closest(".q-item");
    if (li) select(li.dataset.id);
  });
  $("#queue").addEventListener("keydown", (e) => {
    const li = e.target.closest(".q-item");
    if (li && e.key === "Enter") select(li.dataset.id);
  });

  $("#filters").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    state.filter = b.dataset.filter;
    document.querySelectorAll("#filters button").forEach((x) => x.classList.toggle("is-active", x === b));
    renderQueue();
  });

  $("#search").addEventListener("input", (e) => { state.query = e.target.value; renderQueue(); });

  $("#casePane").addEventListener("click", (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    const c = current();
    if (act === "back") { document.body.classList.remove("has-case"); window.scrollTo(0, 0); return; }
    if (act === "edit" && c) {
      if (state.editing) {
        document.querySelectorAll("#casePane input[data-field]").forEach((inp) => { c.order[inp.dataset.field] = Math.max(0, Number(inp.value) || 0); });
        state.editing = false;
        reevaluate(c);
      } else {
        state.editing = true;
        renderCase();
      }
      return;
    }
    const ynBtn = e.target.closest(".yn button");
    if (ynBtn && c) {
      const key = ynBtn.parentElement.dataset.key;
      c.order[key] = ynBtn.dataset.v === "1";
      ynBtn.parentElement.querySelectorAll("button").forEach((b) => b.classList.toggle("is-on", b === ynBtn));
    }
  });

  $("#decisionPane").addEventListener("click", (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    const c = current();
    if (!act || !c) return;
    if (act === "approve") approve();
    if (act === "copy") copyReply();
    if (act === "speak") speak();
    if (act === "whatsapp") window.open(`https://wa.me/?text=${encodeURIComponent(c.draft)}`, "_blank", "noopener");
    if (act === "rule") {
      const box = $("#ruleText");
      box.hidden = !box.hidden;
      e.target.textContent = box.hidden ? "Kural metnini göster" : "Kural metnini gizle";
    }
    if (act === "regen") regenerate(c);
  });

  $("#decisionPane").addEventListener("change", (e) => {
    const c = current();
    if (!c || !e.target.matches("input[data-step]")) return;
    c.checks[Number(e.target.dataset.step)] = e.target.checked;
    const p = document.querySelector(".progress");
    if (p) p.textContent = `${c.checks.filter(Boolean).length}/${c.analysis.steps.length}`;
  });

  $("#decisionPane").addEventListener("input", (e) => {
    const c = current();
    if (!c || e.target.id !== "reply") return;
    c.draft = e.target.value;
    $("#replyCount").textContent = `${c.draft.length} karakter`;
  });

  $("#modelSelect").addEventListener("change", (e) => {
    state.model = e.target.value;
    API.setPreferredModel(state.model);
    toast(`Yanıt modeli: ${modelName()}`);
  });

  // Kurulu yerel modelleri seçiciye doldur
  API.health().then((h) => {
    const sel = $("#modelSelect");
    if (!h || !h.llm.available) {
      sel.innerHTML = `<option value="">${h ? "Model kapalı" : "Sunucusuz önizleme"}</option>`;
      sel.disabled = true;
      return;
    }
    if (!h.llm.installed.includes(state.model)) state.model = h.llm.model;
    sel.innerHTML = h.llm.installed.map((m) => `<option value="${esc(m)}"${m === state.model ? " selected" : ""}>${esc(API.prettyModel(m))}</option>`).join("");
    if (current()) { const t = $("#trace"); if (t) t.innerHTML = traceItems(current(), -1); }
  });

  $("#openHow").addEventListener("click", openHow);
  $("#closeHow").addEventListener("click", closeHow);
  $("#howBody").addEventListener("click", (e) => {
    if (e.target.id !== "resetDemo") return;
    SHARED.clearInbox();
    location.reload();
  });
  $("#scrim").addEventListener("click", closeHow);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeHow(); return; }
    const typing = e.target.closest("input, textarea, select");
    if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === "j") { e.preventDefault(); move(1); }
    else if (k === "k") { e.preventDefault(); move(-1); }
    else if (k === "e") { e.preventDefault(); approve(); }
    else if (k === "c") { e.preventDefault(); copyReply(); }
    else if (k === "/") { e.preventDefault(); $("#search").focus(); }
  });

  function updateNet() {
    const online = navigator.onLine;
    $("#netStatus").classList.toggle("is-online", online);
    $("#netLabel").textContent = online ? "Yerel · ağ çağrısı yok" : "Çevrimdışı · tamamen yerel";
  }
  window.addEventListener("online", updateNet);
  window.addEventListener("offline", updateNet);
  updateNet();

  // Müşteri sayfasından yeni mesaj geldiğinde (aynı tarayıcı, başka sekme)
  SHARED.onInboxChange((items) => {
    const known = new Set(state.cases.map((c) => c.id));
    const fresh = items.filter((x) => !known.has(x.id)).map(hydrate);
    if (!fresh.length) return;
    state.cases = fresh.concat(state.cases);
    renderQueue();
    const open = fresh.filter((x) => !x.done).length;
    toast(open ? `Yeni mesaj: ${fresh[0].customer} · size iletildi` : `${fresh[0].customer} otomatik yanıtlandı`);
    if (!state.selectedId) select(fresh[0].id, { silentMobile: true });
  });

  const autoSpeakEl = $("#autoSpeakSeller");
  autoSpeakEl.checked = SHARED.getPref("autoSpeakSeller", false);
  autoSpeakEl.addEventListener("change", () => {
    SHARED.setPref("autoSpeakSeller", autoSpeakEl.checked);
    if (autoSpeakEl.checked) speak(); else if ("speechSynthesis" in window) speechSynthesis.cancel();
  });

  /* ---------------- Başlat ---------------- */
  const first = visibleCases()[0];
  renderQueue();
  // Mobilde açılışta gelen kutusu görünsün
  if (first) select(first.id, { silentMobile: true });
})();
