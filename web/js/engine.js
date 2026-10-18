/*
 * Tarayıcı içi taklit motor.
 * core/ hattının (BERTurk -> hibrit RAG -> TabPFN -> Gemma) davranışını kurallarla taklit eder.
 * Backend hazır olduğunda analyze() yalnızca fetch("/api/chat") çağrısına dönüşecek;
 * döndürdüğü şekil aynı kalmalı.
 */
window.ED_ENGINE = (function () {
  "use strict";

  const P = window.ED_POLICIES;

  const norm = (t) => t.toLocaleLowerCase("tr")
    .replace(/ç/g, "c").replace(/ğ/g, "g").replace(/ı/g, "i").replace(/ö/g, "o").replace(/ş/g, "s").replace(/ü/g, "u")
    .replace(/[^a-z0-9?\s]/g, " ").replace(/\s+/g, " ").trim();

  // core/nlu_berturk.py içindeki sözlüklerin genişletilmiş hali
  const CAT_KW = {
    kargo: ["kargo", "kurye", "teslimat", "paket", "sube", "takip", "transfer", "gelmedi", "nerede", "ezil", "kutu", "adres", "dagitim"],
    iade: ["iade", "cayma", "para iadesi", "geri gonder", "vazgectim", "parami", "hesaba", "kartima", "etiket", "kullandim", "iade kodu"],
    urun: ["beden", "numara", "defolu", "kusurlu", "bozuk", "garanti", "kalite", "dikis", "taban", "yirtik", "ayipli", "dar geldi", "buyuk geldi", "kucuk geldi", "degisim", "renk"],
    teknik: ["odeme", "sms", "sifre", "kupon", "uygulama", "site", "hesap", "giris", "iki kere", "cift", "cekildi", "3d", "indirim"],
    genel: ["mesai", "iletisim", "telefon", "calisma saat", "hafta sonu", "tesekkur", "harika", "memnun"]
  };
  const NEG_STRONG = ["rezalet", "magdur", "berbat", "parami verin", "dolandirici", "hirsiz", "lanet", "sikayet", "hakem heyeti", "rezil", "savci"];
  const NEG_SOFT = ["gecikti", "gelmedi", "kirik", "kirilmis", "bozuk", "olmadi", "hata", "ezil", "ayrildi", "uzuldum", "yirtik", "hala"];
  const POS = ["tesekkur", "harika", "memnun", "sagol", "mukemmel", "eline saglik", "begendim", "bayildim", "super", "cok guzel"];
  const QUESTION = ["?", "nasil", "nerede", "ne zaman", "kac gun", "ogrenebilir", "sart", "mumkun mu", "miyim", "miyiz", "var mi", "olur mu"];

  const hits = (text, list) => list.reduce((n, kw) => n + (text.includes(kw) ? 1 : 0), 0);

  function classify(text, mode, stars) {
    const t = norm(text);
    let category = "genel";
    let best = 0;
    for (const [cat, list] of Object.entries(CAT_KW)) {
      const policyKw = Object.values(P).filter((p) => p.category === cat).flatMap((p) => p.keywords);
      const score = hits(t, list) * 1.0 + hits(t, policyKw) * 0.6;
      if (score > best) { best = score; category = cat; }
    }

    let intent = "bilgi_talebi";
    let sentiment = 0;
    let confidence = Math.min(0.97, 0.7 + best * 0.08);

    if (mode === "review" && stars) {
      intent = stars >= 4 ? "tesekkur" : stars <= 2 ? "sikayet" : "bilgi_talebi";
      sentiment = (stars - 3) / 2.2;
    }
    if (hits(t, NEG_STRONG)) { intent = "sikayet"; sentiment = Math.min(sentiment, -0.9); }
    else if (hits(t, POS) && !hits(t, NEG_SOFT)) { intent = "tesekkur"; sentiment = Math.max(sentiment, 0.85); }
    else if (mode !== "review" && hits(t, QUESTION)) { intent = "bilgi_talebi"; sentiment = hits(t, NEG_SOFT) ? -0.35 : 0; }
    else if (hits(t, NEG_SOFT)) { intent = "sikayet"; sentiment = Math.min(sentiment, -0.6); }

    if (intent === "tesekkur" && best < 1) category = "genel";
    return { category, intent, confidence: Math.round(confidence * 100) / 100, sentiment: Math.round(sentiment * 100) / 100 };
  }

  // policies.json anahtar kelimelerinin konuşma dilindeki çekimleri
  const EXTRA_KW = {
    POL_KARGO_01: ["gelmedi", "transfer", "hareket yok", "kargom nerede", "gunduz", "gundur"],
    POL_KARGO_02: ["ezik", "ezilmis", "kirik geldi", "kirilmis", "kutu"],
    POL_IADE_01: ["iade etmek", "geri vermek", "vazgec"],
    POL_IADE_03: ["kullandim", "giydim", "yikadim", "etiketini kestim", "etiketi kestim", "etiketini kopardim", "bir kere kullandim"],
    POL_IADE_05: ["hesabima", "ne zaman gecer", "param ne zaman", "iadem", "yatmadi"],
    POL_URUN_01: ["dikisi", "dikis", "sokuldu", "tabani", "kopuk", "yirtik"],
    POL_URUN_03: ["beden", "dar geldi", "bol geldi", "numara"],
    POL_TEKNIK_01: ["iki kere", "iki kez", "cift cekim", "fazla cekildi"]
  };

  function pickPolicy(text, category, intent) {
    const t = norm(text);
    if (intent === "tesekkur") return "POL_GENEL_02";
    let bestId = null;
    let best = 0;
    for (const [id, p] of Object.entries(P)) {
      const score = hits(t, p.keywords) + hits(t, EXTRA_KW[id] || []) * 1.5 + (p.category === category ? 0.5 : 0);
      if (score > best) { best = score; bestId = id; }
    }
    if (best < 1) {
      return { kargo: "POL_KARGO_01", iade: "POL_IADE_01", urun: "POL_URUN_01", teknik: "POL_TEKNIK_01", genel: "POL_GENEL_01" }[category];
    }
    return bestId;
  }

  // dispute=false: iade/hasar uyuşmazlığı olmayan mesajlarda risk etkisi zayıflatılır
  function risk(order, sentiment, text, dispute = true) {
    const t = norm(text || "");
    const rate = order.pastOrders ? order.pastReturns / order.pastOrders : 0;
    const used = /kullandim|giydim|yikadim|etiket/.test(t) && /iade/.test(t);
    let s = 0.05;
    s += Math.min(0.3, rate * 0.35);
    s += order.amount > 3000 ? 0.15 : order.amount > 1200 ? 0.07 : 0;
    s += order.unboxingVideo ? -0.06 : 0.08;
    s += order.boxDamaged ? 0.08 : 0;
    s += order.deliveryDays > 4 ? 0.04 : 0;
    s += sentiment < -0.6 ? 0.12 : 0;
    s += used ? 0.2 : 0;
    if (!dispute) s = 0.02 + s * 0.25;
    s = Math.max(0.01, Math.min(0.97, s));

    const drivers = [];
    if (rate >= 0.5) drivers.push({ label: `İade oranı %${Math.round(rate * 100)} (${order.pastReturns}/${order.pastOrders})`, dir: "up" });
    else drivers.push({ label: `${order.pastOrders} sipariş, ${order.pastReturns} iade`, dir: "down" });
    if (order.amount > 1200) drivers.push({ label: `Yüksek tutar · ${Math.round(order.amount).toLocaleString("tr-TR")} TL`, dir: "up" });
    drivers.push({ label: order.unboxingVideo ? "Açılış videosu var" : "Açılış videosu yok", dir: order.unboxingVideo ? "down" : "up" });
    if (order.boxDamaged) drivers.push({ label: "Paket hasarlı bildirildi", dir: "up" });
    if (used) drivers.push({ label: "Kullanım izi beyan edildi", dir: "up" });
    if (sentiment < -0.6) drivers.push({ label: "Sert dil", dir: "up" });

    return { score: s, level: s >= 0.6 ? "red" : s >= 0.25 ? "yellow" : "green", drivers };
  }

  // Politika başına: esnafa aksiyon + adımlar, müşteriye tam yanıt.
  // Yanıtlar yalnızca politika metnindeki süre ve koşulları kullanır.
  const PLAYBOOK = {
    POL_KARGO_01: {
      action: "Kargo takip şikayeti aç, müşteriye konum bilgisi ver",
      steps: ["Kargo sisteminden takip şikayeti oluşturun.", "Aktarma merkezinden paketin konumunu isteyin.", "24 saatte dönüş yoksa yeni gönderim veya iade teklif edin."],
      reply: (c) => `Merhaba ${c.first}, ${c.order.id} numaralı siparişiniz için kargo firmasında takip kaydı açtık. Standart teslimat 1-3 iş günü; bu süre aşıldığı için konumu 24 saat içinde netleştiriyoruz. O sürede hareket olmazsa dilerseniz ürünü ücretsiz yeniden gönderiyor ya da ücretinizi iade ediyoruz.`
    },
    POL_KARGO_02: {
      action: "Hasar fotoğrafı iste, kargoya itiraz aç",
      steps: ["Kutunun ve ürünün net fotoğraflarını isteyin (24 saat).", "Kuryenin hasar tespit tutanağı tutup tutmadığını sorun.", "Kargo şubesine hasar itirazı açın.", "Fotoğraflar doğrulanınca yeni ürünü gönderin."],
      reply: (c) => `Merhaba ${c.first}, yaşadığınız durum için çok üzgünüz. Hemen çözebilmemiz için kutunun ve ürünün birkaç net fotoğrafını 24 saat içinde buradan gönderebilir misiniz? Teslim alırken kuryeye hasar tutanağı tutturduysanız onu da eklemeniz süreci hızlandırır.`,
      escalate: true
    },
    POL_KARGO_03: {
      action: "Şube adresini ve takip numarasını ilet",
      steps: ["Kargo sisteminde 'adreste bulunamadı' notunu kontrol edin.", "Şube adresini ve takip numarasını müşteriye gönderin.", "3 iş günü içinde alınmazsa paketin iade döneceğini hatırlatın."],
      reply: (c) => `Merhaba ${c.first}, kurye size ulaşamadığı için paketiniz en yakın dağıtım şubesinde 3 iş günü bekletiliyor. Takip numaranız ve şube adresi sipariş detayınızda; bu süre içinde şubeden teslim alabilirsiniz, aksi halde paket bize geri döner.`
    },
    POL_IADE_01: {
      action: "Cayma talebini onayla, iade kodunu gönder",
      steps: ["Teslimden itibaren 14 gün içinde olduğunu doğrulayın.", "Ürünün tekrar satılabilir durumda olduğunu teyit edin.", "Anlaşmalı kargo iade kodunu iletin."],
      reply: (c) => `Merhaba ${c.first}, teslimden itibaren 14 gün içinde gerekçe göstermeden iade hakkınız var. Ürünün tekrar satılabilir durumda, aksesuarları ve faturasıyla birlikte olması yeterli. Anlaşmalı kargo iade kodunuzu sipariş sayfanıza tanımladık; bu kodla gönderim ücretsizdir.`
    },
    POL_IADE_02: {
      action: "Hijyen kapsamını açıkla, ayıp varsa incele",
      steps: ["Ürünün hijyen kapsamında olup olmadığını kontrol edin.", "Koruma bandının açılıp açılmadığını sorun.", "Üretim hatası iddiası varsa fotoğraf isteyin."],
      reply: (c) => `Merhaba ${c.first}, hijyen kapsamındaki ürünlerde koruma bandı açıldığında mevzuat gereği cayma hakkı sona eriyor. Ancak üründe bir üretim hatası varsa iade elbette kabul edilir; fotoğrafını paylaşırsanız hemen inceleriz.`
    },
    POL_IADE_03: {
      action: "Kullanılmış ürün iadesini nazikçe reddet, alternatif öner",
      steps: ["Kullanılmış veya etiketi sökülmüş ürünün iade kapsamı dışında olduğunu açıklayın.", "Alternatif olarak indirim veya değişim önerin.", "Ürün yine de gelirse kamera kaydında açıp tutanak tutun."],
      reply: (c) => `Merhaba ${c.first}, açık yazdığınız için teşekkür ederiz. Dışarıda kullanılmış ya da orijinal etiketi sökülmüş ürünler tekrar satılamadığı için iade kapsamına girmiyor. Size yardımcı olabilmek için mağaza sahibimiz durumunuzu ayrıca değerlendirecek.`,
      escalate: true
    },
    POL_IADE_04: {
      action: "İade kodunu ve anlaşmalı kargoyu ilet",
      steps: ["9 haneli iade kodunu müşteriye iletin.", "Yalnızca anlaşmalı kargo ile gönderilmesi gerektiğini hatırlatın."],
      reply: (c) => `Merhaba ${c.first}, iadenizi yalnızca anlaşmalı kargo firmamızla, size özel 9 haneli iade koduyla göndermeniz yeterli; bu kodla kargo ücreti bize ait. Kodunuz sipariş detayınızda yer alıyor. Başka bir firmayla karşı ödemeli gönderilen paketleri teslim alamıyoruz.`
    },
    POL_IADE_05: {
      action: "İade onayını kontrol et, yansıma süresini bildir",
      steps: ["Depo kaydında iadenin onaylandığını kontrol edin.", "Banka talimat tarihini müşteriye iletin."],
      reply: (c) => `Merhaba ${c.first}, iade ürün depomuza ulaşıp onaylandıktan sonra 24 saat içinde bankaya iade talimatı veriyoruz. Tutarın yansıması kredi kartlarında 1-3 iş günü, banka kartlarında 2-7 iş günü sürebilir; taksitli alışverişlerde iade ekstreye taksitli yansıyabilir.`
    },
    POL_URUN_01: {
      action: "Ayıplı ürün için fotoğraf iste, değişim veya iade başlat",
      steps: ["Kusurun yakın plan fotoğrafını isteyin.", "Aynı ürünü stoktan ayırın.", "Ücretsiz değişim veya iade sürecini başlatın."],
      reply: (c) => `Merhaba ${c.first}, üründe üretimden kaynaklı bir kusur varsa hiçbir kargo ücreti ödemeden birebir değişim ya da iade hakkınız var. Kusurlu bölgenin yakın plan bir fotoğrafını buradan paylaşır mısınız? Fotoğraf gelir gelmez süreci başlatıyoruz.`,
      escalate: true
    },
    POL_URUN_02: {
      action: "Yetkili servis sürecini anlat",
      steps: ["Garanti belgesinin geçerliliğini kontrol edin.", "Yetkili servis adresini iletin.", "Servis raporu 'iade uygun' derse iadeyi tamamlayın."],
      reply: (c) => `Merhaba ${c.first}, ürün 2 yıl distribütör garantisi altında. Arıza için yetkili servise başvurmanız gerekiyor; servis 'Değişim/İade Uygundur' raporu verirse iadenizi hemen tamamlıyoruz.`
    },
    POL_URUN_03: {
      action: "Stoku kontrol et, ücretsiz değişim kodunu gönder",
      steps: ["İstenen bedenin stokta olduğunu doğrulayın.", "Ücretsiz değişim kargo kodunu iletin.", "Eski ürün gelince yenisini aynı gün gönderin."],
      reply: (c) => `Merhaba ${c.first}, beden değişimi elbette mümkün. İstediğiniz beden stoktaysa ücretsiz kargo koduyla değişim yapıyoruz; stok tükenmişse aynı tutarda indirim kuponu ya da ücret iadesi seçebilirsiniz. Hangi bedeni istediğinizi yazmanız yeterli.`
    },
    POL_TEKNIK_01: {
      action: "Provizyonu kontrol et, iptal süresini bildir",
      steps: ["Ödeme panelinde ikinci provizyonun referansını bulun.", "Askıdaki tutarın 24 saatte iptal edildiğini doğrulayın."],
      reply: (c) => `Merhaba ${c.first}, ödeme sırasında bağlantı koptuğunda bankanızda ikinci bir provizyon görünebiliyor. Askıda kalan bu tutar 24 saat içinde otomatik olarak iptal edilir; siparişiniz tek ve geçerli.`
    },
    POL_TEKNIK_02: {
      action: "Giriş bağlantısı gönder",
      steps: ["Operatör SMS engelini kontrol ettirin.", "Kayıtlı e-postaya tek kullanımlık giriş bağlantısı gönderin."],
      reply: (c) => `Merhaba ${c.first}, SMS kodu gelmiyorsa önce operatörünüzdeki SMS engelini ve spam klasörünü kontrol etmenizi rica ederiz. Sorun sürerse kayıtlı e-posta adresinize tek kullanımlık güvenli giriş bağlantısı gönderiyoruz.`
    },
    POL_TEKNIK_03: {
      action: "Kupon şartlarını açıkla",
      steps: ["Kuponun alt limit ve kategori şartlarını kontrol edin.", "Birden fazla kupon kullanılmaya çalışılıyor mu bakın."],
      reply: (c) => `Merhaba ${c.first}, kupon kodları belirli sepet alt limiti ve kategori şartlarına bağlı, ayrıca aynı sepette birden fazla kupon birleştirilemiyor. Sepetinizi bu şartlara göre kontrol ederseniz kupon uygulanacaktır.`
    },
    POL_GENEL_01: {
      action: "Mesai bilgisini ilet",
      steps: ["Sorunun içeriğini netleştirin.", "Gerekirse mesai içinde telefonla dönün."],
      reply: (c) => `Merhaba ${c.first}, destek ekibimiz hafta içi ve Cumartesi 09:00-19:00 arasında çalışıyor; mesai dışında gelen mesajlar ilk iş günü sabahı öncelik sırasıyla yanıtlanıyor. Siparişinizle ilgili sorunuzu biraz daha açarsanız hemen yardımcı olalım.`
    },
    POL_GENEL_02: {
      action: "Teşekkür et, değerlendirme rica et",
      steps: ["Kısa ve samimi bir teşekkür gönderin.", "Değerlendirme bırakmasını rica edin."],
      reply: (c) => `${c.first}, güzel sözleriniz için çok teşekkür ederiz; emeğimizin karşılık bulması bizi gerçekten mutlu ediyor. Bir sonraki siparişinizde de aynı özeni göstereceğiz.`
    }
  };

  const rand = (a, b) => Math.round(a + Math.random() * (b - a));

  function analyze(text, ctx) {
    const { order, mode = "question", stars = 0, customer = "Müşteri", shop = "Usta Deri" } = ctx;
    const c = { first: customer.split(" ")[0], order, shop };

    const nlu = classify(text, mode, stars);
    const policyId = pickPolicy(text, nlu.category, nlu.intent);
    const dispute = nlu.intent !== "tesekkur" && (["iade", "urun"].includes(nlu.category) || policyId === "POL_KARGO_02");
    const r = risk(order, nlu.sentiment, text, dispute);
    const book = PLAYBOOK[policyId];

    const priority = r.level === "red" || nlu.sentiment <= -0.85 ? "acil"
      : r.level === "yellow" || nlu.intent === "sikayet" ? "yuksek"
      : nlu.intent === "bilgi_talebi" ? "orta" : "dusuk";

    const escalate = !!book.escalate || r.level === "red" || nlu.sentiment <= -0.85 || (mode === "review" && nlu.intent === "sikayet");
    const fullReply = `${book.reply(c)} ${shop}`;

    let customerReply = fullReply;
    if (mode === "review") {
      customerReply = nlu.intent === "tesekkur"
        ? `${c.first}, değerlendirmeniz için çok teşekkür ederiz. Ürününüzü güzel günlerde kullanmanızı dileriz. ${shop}`
        : `${c.first}, yaşadığınız sorun için özür dileriz. Konuyu çözmek için size özel mesajla ulaştık; mağaza sahibimiz bizzat ilgileniyor. ${shop}`;
    } else if (escalate && !["POL_KARGO_02", "POL_URUN_01"].includes(policyId)) {
      // Kanıt istenebilecek durumlar dışında ret/onay kararını satıcı verir
      customerReply = `Merhaba ${c.first}, mesajınızı aldım ve mağaza sahibimize öncelikli olarak ilettim. ${P[policyId].title} kapsamında değerlendirilecek; destek saatlerimiz içinde (09:00-19:00) size buradan dönüş yapılacak. ${shop}`;
    }

    return {
      category: nlu.category,
      intent: nlu.intent,
      confidence: nlu.confidence,
      sentiment: nlu.sentiment,
      risk: r,
      priority,
      action: book.action,
      steps: book.steps.slice(),
      policyId,
      reply: fullReply,
      customerReply,
      escalate,
      timings: { nlu: rand(28, 45), rag: rand(70, 120), risk: rand(11, 20), llm: rand(780, 1300) }
    };
  }

  return { analyze, classify, risk };
})();
