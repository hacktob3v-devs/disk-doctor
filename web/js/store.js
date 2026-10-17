(function () {
  "use strict";

  const ENGINE = window.ED_ENGINE;
  const SHARED = window.ED_SHARED;
  const P = window.ED_POLICIES;

  const CUSTOMER = "Deniz Arslan";
  const HISTORY = { pastOrders: 6, pastReturns: 1 };

  const ORDERS = [
    { id: "TR-330417", product: "Deri el çantası · konyak", amount: 3400, status: "Teslim edildi · 2 gün önce", deliveryDays: 2, unboxingVideo: false, boxDamaged: false },
    { id: "TR-559311", product: "Erkek klasik ayakkabı · 43", amount: 2150, status: "Kargoda · 5 gündür", deliveryDays: 5, unboxingVideo: false, boxDamaged: false },
    { id: "TR-602540", product: "Deri cüzdan · kahve", amount: 540, status: "Teslim edildi · 9 gün önce", deliveryDays: 2, unboxingVideo: true, boxDamaged: false }
  ];

  const SUGGESTIONS = [
    "Kargom 5 gündür gelmedi, nerede?",
    "Çantayı iade etmek istiyorum, nasıl yapabilirim?",
    "Kartımdan iki kere çekildi",
    "Dikişi söküldü, değişim mümkün mü?",
    "İadem ne zaman hesabıma geçer?"
  ];

  const REVIEWS = [
    { name: "Ayşe K.", stars: 5, text: "Deri kalitesi fotoğraftakinden de güzel, dikişleri çok düzgün. Kokusu bile ayrı.", reply: "Ayşe Hanım, güzel sözleriniz için teşekkür ederiz. Çantanızı uzun yıllar keyifle kullanmanızı dileriz. Usta Deri", when: "3 gün önce" },
    { name: "Murat E.", stars: 4, text: "Kargo bir gün gecikti ama ürün beklediğimden iyi çıktı.", reply: "Murat Bey, gecikme için özür dileriz; kargo firmasıyla görüştük. Ürünü beğenmenize çok sevindik. Usta Deri", when: "1 hafta önce" }
  ];

  const CATEGORY = { kargo: "Kargo", iade: "İade", urun: "Ürün", teknik: "Ödeme", genel: "Genel" };
  const INTENT = { sikayet: "Şikâyet", bilgi_talebi: "Bilgi talebi", tesekkur: "Teşekkür" };
  const LEVEL = { green: "Güvenli", yellow: "İncele", red: "Yüksek risk" };
  const PRIORITY = { acil: "Acil", yuksek: "Yüksek", orta: "Normal", dusuk: "Düşük" };

  const state = { orderId: ORDERS[0].id, mode: "question", stars: 0, busy: false, latencies: [] };

  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const order = () => ORDERS.find((o) => o.id === state.orderId);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const thread = $("#thread");

  /* ---------------- Sol sütun ---------------- */

  function renderOrders() {
    $("#orders").innerHTML = ORDERS.map((o) => `
      <button type="button" role="radio" aria-checked="${o.id === state.orderId}" class="order${o.id === state.orderId ? " is-on" : ""}" data-id="${o.id}">
        <span class="order-radio" aria-hidden="true"></span>
        <span class="order-body">
          <span class="order-name">${esc(o.product)}</span>
          <span class="order-meta"><span class="mono">${o.id}</span> · ${esc(o.status)}</span>
        </span>
        <span class="order-amt num">${o.amount.toLocaleString("tr-TR")} TL</span>
      </button>`).join("");
    $("#composerCtx").textContent = `${order().id} hakkında`;
  }

  function starStr(n) { return "★★★★★".slice(0, n) + "☆☆☆☆☆".slice(0, 5 - n); }

  function renderReviews() {
    $("#reviews").innerHTML = REVIEWS.map((r) => `
      <li class="review${r.fresh ? " is-fresh" : ""}">
        <div class="review-top"><span class="review-name">${esc(r.name)}</span><span class="stars sm" aria-label="${r.stars} yıldız">${starStr(r.stars)}</span><span class="muted review-when">${r.when}</span></div>
        <p class="review-text">${esc(r.text)}</p>
        ${r.reply ? `<div class="review-reply"><span class="review-reply-h">Satıcının yanıtı</span>${esc(r.reply)}</div>` : ""}
      </li>`).join("");
  }

  function renderAvg() {
    const l = state.latencies;
    $("#avgReply").textContent = l.length
      ? `Bu oturumda ortalama yanıt: ${(l.reduce((a, b) => a + b, 0) / l.length / 1000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sn`
      : "Birkaç saniye içinde yanıt verir";
  }

  /* ---------------- Sohbet ---------------- */

  function scrollDown() { thread.scrollTop = thread.scrollHeight; }

  function addDayMark() {
    thread.insertAdjacentHTML("beforeend", `<div class="day-mark"><span>Bugün</span></div>`);
  }

  function addShop(html, opts = {}) {
    const el = document.createElement("div");
    el.className = "msg msg-shop";
    el.innerHTML = `
      <span class="seller-mark sm" aria-hidden="true">UD</span>
      <div class="msg-col">
        <div class="bubble">${html}</div>
        <div class="msg-foot">${opts.foot ? opts.foot + '<span class="sep">·</span>' : ""}<button type="button" class="listen" title="Yanıtı sesli dinle"><svg viewBox="0 0 24 24" class="ico" aria-hidden="true"><path d="M4 10v4h4l5 4V6L8 10H4z"/><path d="M16.5 9a4 4 0 0 1 0 6"/></svg>Dinle</button></div>
      </div>`;
    thread.appendChild(el);
    scrollDown();
    return el;
  }

  function addCustomer(text, stars) {
    const el = document.createElement("div");
    el.className = "msg msg-me";
    el.innerHTML = `
      <div class="msg-col">
        ${stars ? `<div class="msg-kind">Yorum · <span class="stars sm">${starStr(stars)}</span></div>` : ""}
        <div class="bubble">${esc(text)}</div>
        <div class="analysis" hidden></div>
        <div class="msg-foot">${SHARED.nowHHMM()} · ${esc(order().id)}</div>
      </div>`;
    thread.appendChild(el);
    scrollDown();
    return el;
  }

  function typing() {
    const el = document.createElement("div");
    el.className = "msg msg-shop";
    el.innerHTML = `<span class="seller-mark sm" aria-hidden="true">UD</span><div class="msg-col"><div class="bubble typing"><span></span><span></span><span></span></div><div class="msg-foot" data-stage>Mesaj okunuyor…</div></div>`;
    thread.appendChild(el);
    scrollDown();
    return el;
  }

  function analysisHtml(a) {
    const score = Math.round(a.risk.score * 100);
    return `
      <span class="an-chip">${CATEGORY[a.category]}</span>
      <span class="an-chip">${INTENT[a.intent]}</span>
      <span class="an-chip">güven %${Math.round(a.confidence * 100)}</span>
      <span class="an-chip ${a.risk.level}">risk %${score} · ${LEVEL[a.risk.level]}</span>
      <span class="an-rule mono">${a.policyId}</span>`;
  }

  async function streamInto(el, text) {
    const words = text.split(" ");
    el.textContent = "";
    for (let i = 0; i < words.length; i++) {
      el.textContent += (i ? " " : "") + words[i];
      if (i % 3 === 0) scrollDown();
      await sleep(18 + Math.random() * 22);
    }
    scrollDown();
  }

  async function send(text) {
    text = text.trim();
    if (!text || state.busy) return;
    if (state.mode === "review" && !state.stars) { toast("Önce puan verin"); return; }

    state.busy = true;
    $("#sendBtn").disabled = true;
    const mode = state.mode;
    const stars = state.stars;
    const o = order();
    const meEl = addCustomer(text, mode === "review" ? stars : 0);
    $("#input").value = "";
    autosize();

    const t0 = performance.now();
    const a = ENGINE.analyze(text, {
      order: { ...o, ...HISTORY },
      mode, stars, customer: CUSTOMER, shop: "Usta Deri"
    });

    // Hattın aşamalarını kısaca göster
    const tEl = typing();
    const stage = tEl.querySelector("[data-stage]");
    await sleep(260); stage.textContent = `Sınıflandırıldı: ${CATEGORY[a.category]} · ${INTENT[a.intent]}`;
    const an = meEl.querySelector(".analysis");
    an.innerHTML = analysisHtml(a);
    an.hidden = !$("#showAnalysis").checked;
    await sleep(300); stage.textContent = `Kural bulundu: ${P[a.policyId].title}`;
    await sleep(260); stage.textContent = "Yanıt yazılıyor…";
    await sleep(380);
    tEl.remove();

    const latency = performance.now() - t0;
    state.latencies.push(latency);

    const foot = [
      `<span>Dayanak: ${esc(P[a.policyId].title)}</span>`,
      `<span class="num">${(latency / 1000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sn</span>`
    ].join("<span class=\"sep\">·</span>");
    const reply = addShop("", { foot });
    await streamInto(reply.querySelector(".bubble"), a.customerReply);
    if ($("#autoSpeak").checked) SHARED.speak(a.customerReply);

    if (a.escalate) {
      thread.insertAdjacentHTML("beforeend", `
        <div class="handoff">
          <span class="handoff-dot"></span>
          <span>Mağaza sahibine iletildi · Öncelik: <b>${PRIORITY[a.priority]}</b></span>
        </div>`);
      scrollDown();
    }

    if (mode === "review") {
      REVIEWS.unshift({ name: "Deniz A.", stars, text, reply: a.customerReply, when: "az önce", fresh: true });
      renderReviews();
      setMode("question");
    }

    // Satıcı masasına düşür
    SHARED.pushInbox({
      id: "w" + Date.now(),
      source: "site",
      customer: CUSTOMER,
      time: SHARED.nowHHMM(),
      unread: a.escalate,
      message: text,
      order: { id: o.id, product: o.product, amount: o.amount, deliveryDays: o.deliveryDays, unboxingVideo: o.unboxingVideo, boxDamaged: o.boxDamaged, ...HISTORY },
      analysis: { ...a, reply: a.escalate ? a.reply : a.customerReply },
      done: !a.escalate,
      auto: !a.escalate,
      sentReply: a.customerReply,
      kind: mode
    });

    renderAvg();
    state.busy = false;
    $("#sendBtn").disabled = false;
    $("#input").focus();
  }

  /* ---------------- Yazma alanı ---------------- */

  function autosize() {
    const t = $("#input");
    t.style.height = "auto";
    t.style.height = Math.min(160, t.scrollHeight) + "px";
  }

  function setMode(mode) {
    state.mode = mode;
    state.stars = 0;
    document.querySelectorAll("#modeSeg button").forEach((b) => b.classList.toggle("is-on", b.dataset.mode === mode));
    $("#starInput").hidden = mode !== "review";
    $("#input").placeholder = mode === "review" ? "Ürünle ilgili deneyiminizi yazın…" : "Satıcıya sorunuzu yazın…";
    $("#sendBtn").textContent = mode === "review" ? "Yorumu gönder" : "Gönder";
    renderStars();
  }

  function renderStars() {
    $("#starInput .star-btns").innerHTML = [1, 2, 3, 4, 5].map((n) =>
      `<button type="button" role="radio" aria-checked="${n === state.stars}" aria-label="${n} yıldız" data-n="${n}" class="${n <= state.stars ? "is-on" : ""}">★</button>`).join("");
  }

  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("is-on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("is-on"), 2200);
  }

  /* ---------------- Olaylar ---------------- */

  $("#orders").addEventListener("click", (e) => {
    const b = e.target.closest(".order");
    if (!b) return;
    state.orderId = b.dataset.id;
    renderOrders();
  });

  $("#suggestions").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) send(b.textContent);
  });

  $("#composer").addEventListener("submit", (e) => { e.preventDefault(); send($("#input").value); });
  $("#input").addEventListener("input", autosize);
  $("#input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send($("#input").value); }
  });

  $("#modeSeg").addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) { setMode(b.dataset.mode); $("#input").focus(); }
  });
  $("#starInput").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-n]");
    if (b) { state.stars = Number(b.dataset.n); renderStars(); }
  });
  $("#writeReview").addEventListener("click", () => { setMode("review"); $("#input").focus(); });

  thread.addEventListener("click", (e) => {
    const b = e.target.closest(".listen");
    if (!b) return;
    const text = b.closest(".msg-col").querySelector(".bubble").textContent;
    if (!SHARED.speak(text)) toast("Bu tarayıcı sesli okumayı desteklemiyor");
  });

  $("#autoSpeak").checked = SHARED.getPref("autoSpeakCustomer", false);
  $("#autoSpeak").addEventListener("change", (e) => {
    SHARED.setPref("autoSpeakCustomer", e.target.checked);
    if (!e.target.checked && "speechSynthesis" in window) speechSynthesis.cancel();
  });

  $("#showAnalysis").addEventListener("change", (e) => {
    document.querySelectorAll(".analysis").forEach((el) => { el.hidden = !e.target.checked; });
  });

  // Sesle yazma
  const dictation = SHARED.createDictation({
    onStart: () => { $("#micBtn").classList.add("is-on"); $("#composerNote").textContent = "Dinliyorum… Türkçe konuşun."; },
    onResult: (text) => { $("#input").value = text; autosize(); },
    onEnd: () => { $("#micBtn").classList.remove("is-on"); $("#composerNote").textContent = "Konuşmanız metne çevrildi; göndermeden önce düzenleyebilirsiniz."; },
    onError: (err) => toast(err === "not-allowed" ? "Mikrofon izni verilmedi" : "Ses algılanamadı")
  });
  $("#micBtn").addEventListener("click", () => {
    if (!dictation) return toast("Bu tarayıcı sesle yazmayı desteklemiyor (Chrome veya Edge deneyin)");
    dictation.toggle();
  });

  /* ---------------- Başlat ---------------- */

  renderOrders();
  renderReviews();
  renderAvg();
  setMode("question");
  $("#suggestions").innerHTML = SUGGESTIONS.map((s) => `<button type="button">${esc(s)}</button>`).join("");
  addDayMark();
  addShop("Merhaba Deniz, Usta Deri'ye hoş geldiniz. Siparişiniz, iade, değişim ya da kargo hakkında ne sormak isterseniz yazın; mesai dışında da hemen yanıtlıyoruz.");
})();
