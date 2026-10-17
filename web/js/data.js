/*
 * Prototip verisi. İleride /api/analyze yanıtı aynı şekli döndürecek;
 * arayüz yalnızca bu şekle bağlıdır.
 */
window.ED_DATA = (function () {
  const POLICIES = window.ED_POLICIES;

  const CASES = [
    {
      id: "c1",
      source: "trendyol",
      customer: "Ayşe Karaman",
      time: "18:42",
      unread: true,
      message: "Kargom az önce geldi ama kutu resmen ezilmiş, içindeki porselen takım da kırılmış! Kurye kapıya bırakıp kaçtı hemen, ne yapmam gerekiyor acil dönüş bekliyorum?",
      order: { id: "TR-982341", product: "Porselen kahve takımı · 6 kişilik", amount: 1450, deliveryDays: 3, pastOrders: 4, pastReturns: 0, unboxingVideo: false, boxDamaged: true },
      analysis: {
        category: "kargo", intent: "sikayet", confidence: 0.91, sentiment: -0.72,
        risk: { score: 0.34, level: "yellow", drivers: [
          { label: "Tutanak tutulmamış", dir: "up" },
          { label: "Açılış videosu yok", dir: "up" },
          { label: "Geçmiş iade yok", dir: "down" },
          { label: "Sadık müşteri (4 sipariş)", dir: "down" }
        ] },
        priority: "acil",
        action: "Hasar fotoğrafı iste, kargoya itiraz aç",
        steps: [
          "Müşteriden kutunun ve kırık parçaların net fotoğraflarını isteyin (24 saat).",
          "Kuryenin hasar tespit tutanağı tutup tutmadığını teyit edin.",
          "Kargo şubesine hasar itiraz bildirimi açın.",
          "Fotoğraflar doğrulanınca yeni takımı bekletmeden kargolayın."
        ],
        policyId: "POL_KARGO_02",
        reply: "Merhaba Ayşe Hanım, yaşadığınız durum için gerçekten çok üzgünüz. Sorunu hemen çözebilmemiz için ezilen kutunun ve kırık parçaların birkaç net fotoğrafını bu mesaja yanıt olarak gönderebilir misiniz? Fotoğrafları aldığımız gün kargo firmasına itirazımızı açıyor ve yeni takımınızı beklemeden yola çıkarıyoruz. Usta Deri",
        timings: { nlu: 38, rag: 112, risk: 17, llm: 1180 }
      }
    },
    {
      id: "c2",
      source: "hepsiburada",
      customer: "Burak Tunç",
      time: "18:31",
      unread: true,
      message: "Aldığım 5800 liralık deri ceketin dikişleri berbat, hemen paramı kartıma iade edin yoksa Tüketici Hakem Heyetine gidip sizi rezil ederim!",
      order: { id: "TR-441092", product: "El dikimi kuzu derisi ceket · L", amount: 5800, deliveryDays: 7, pastOrders: 2, pastReturns: 2, unboxingVideo: false, boxDamaged: false },
      analysis: {
        category: "iade", intent: "sikayet", confidence: 0.84, sentiment: -0.93,
        risk: { score: 0.81, level: "red", drivers: [
          { label: "İade oranı %100 (2/2)", dir: "up" },
          { label: "Yüksek tutar · 5.800 TL", dir: "up" },
          { label: "Açılış videosu yok", dir: "up" },
          { label: "Sert dil, tehdit", dir: "up" }
        ] },
        priority: "acil",
        action: "İadeyi ön incelemeye al, fotoğraf ve etiket kontrolü iste",
        steps: [
          "Dikiş hatasının yakın plan fotoğraflarını isteyin.",
          "Orijinal etiketin ve koruma bandının yerinde olup olmadığını sorun.",
          "Ürün depoya gelince paketi kamera kaydı altında açın, tutanak tutun.",
          "Ayıp doğrulanırsa iadeyi onaylayın; kullanım izi varsa reddetme hakkınız saklıdır."
        ],
        policyId: "POL_URUN_01",
        reply: "Merhaba Burak Bey, ceketinizle ilgili yaşadığınız sorun için üzgünüz. Üretim kaynaklı bir kusur varsa değişim ya da iade hakkınız eksiksiz geçerlidir. Süreci hızla başlatabilmemiz için dikiş bölgesinin yakın plan fotoğraflarını ve etiketin göründüğü bir kareyi iletmenizi rica ederiz. Ürün bize ulaştığında inceleme aynı gün tamamlanır. Usta Deri",
        timings: { nlu: 41, rag: 98, risk: 19, llm: 1240 }
      }
    },
    {
      id: "c3",
      source: "instagram",
      customer: "Elif Sarı",
      time: "18:17",
      unread: true,
      message: "Merhabalar kolay gelsin, aldığım keten pantolonun bedeni biraz dar geldi. 14 günlük sürem dolmadan 42 beden ile değişim yapabilir miyiz acaba?",
      order: { id: "TR-128955", product: "Keten pantolon · 40 beden", amount: 620, deliveryDays: 2, pastOrders: 14, pastReturns: 1, unboxingVideo: true, boxDamaged: false },
      analysis: {
        category: "urun", intent: "bilgi_talebi", confidence: 0.88, sentiment: 0.31,
        risk: { score: 0.06, level: "green", drivers: [
          { label: "14 sipariş, 1 iade", dir: "down" },
          { label: "Açılış videosu var", dir: "down" },
          { label: "Düşük tutar", dir: "down" }
        ] },
        priority: "orta",
        action: "Değişimi onayla, ücretsiz kargo kodunu gönder",
        steps: [
          "Stokta 42 beden olduğunu doğrulayın.",
          "Ücretsiz değişim kargo kodunu müşteriye iletin.",
          "Eski ürün depoya ulaşınca 42 bedeni aynı gün gönderin."
        ],
        policyId: "POL_URUN_03",
        reply: "Merhaba Elif Hanım, elbette! 42 beden stokta mevcut. Değişim için ücretsiz kargo kodunuz: 418 552 907. Ürünü en yakın anlaşmalı şubeye bırakmanız yeterli; elimize ulaştığı gün yeni bedeninizi kargoya veriyoruz. Her zaman bekleriz. Usta Deri",
        timings: { nlu: 35, rag: 87, risk: 14, llm: 960 }
      }
    },
    {
      id: "c4",
      source: "trendyol",
      customer: "Kaan Aydın",
      time: "17:58",
      unread: false,
      message: "Siparişim 5 gündür Malatya transfer merkezinde bekliyor, hiç hareket yok. Takip numarası da güncellenmiyor, ne zaman gelecek?",
      order: { id: "TR-559210", product: "Erkek klasik ayakkabı · 43", amount: 2150, deliveryDays: 5, pastOrders: 3, pastReturns: 0, unboxingVideo: false, boxDamaged: false },
      analysis: {
        category: "kargo", intent: "bilgi_talebi", confidence: 0.94, sentiment: -0.35,
        risk: { score: 0.12, level: "green", drivers: [
          { label: "Geçmiş iade yok", dir: "down" },
          { label: "Teslimat 5 gün (eşik 4)", dir: "up" }
        ] },
        priority: "yuksek",
        action: "Kargo şikayeti aç, müşteriye tahmini teslimat bildir",
        steps: [
          "Kargo sisteminden takip şikayeti oluşturun (4 iş günü aşıldı).",
          "Malatya aktarma merkezini arayıp paketin konumunu sorun.",
          "24 saat içinde dönüş yoksa yeni gönderim veya iade teklif edin."
        ],
        policyId: "POL_KARGO_01",
        reply: "Merhaba Kaan Bey, gecikme için özür dileriz. Paketiniz için kargo firmasında öncelikli takip kaydı açtık ve aktarma merkeziyle görüşüyoruz. 24 saat içinde size net konum bilgisi vereceğiz; o süre içinde hareket olmazsa yeni ayakkabınızı hemen yola çıkaracağız. Usta Deri",
        timings: { nlu: 33, rag: 91, risk: 15, llm: 1010 }
      }
    },
    {
      id: "c5",
      source: "whatsapp",
      customer: "Zehra Doğan",
      time: "17:44",
      unread: false,
      message: "Çantayı iade etmek istiyorum. Bir kere düğünde kullandım ama rengi elbiseyle olmadı. Etiketini de yanlışlıkla kesmişim, sorun olur mu?",
      order: { id: "TR-330417", product: "Deri el çantası · konyak", amount: 3400, deliveryDays: 2, pastOrders: 5, pastReturns: 3, unboxingVideo: false, boxDamaged: false },
      analysis: {
        category: "iade", intent: "bilgi_talebi", confidence: 0.9, sentiment: -0.05,
        risk: { score: 0.68, level: "red", drivers: [
          { label: "Ürün dışarıda kullanılmış", dir: "up" },
          { label: "Etiket sökülmüş", dir: "up" },
          { label: "İade oranı %60 (3/5)", dir: "up" }
        ] },
        priority: "yuksek",
        action: "İadeyi nazikçe reddet, alternatif öner",
        steps: [
          "Kullanılmış ve etiketi sökülmüş ürünün iade kapsamı dışında olduğunu açıklayın.",
          "Alternatif olarak bir sonraki alışverişte geçerli indirim önerin.",
          "Müşteri yine de gönderirse paketi kamera kaydında açıp tutanak tutun."
        ],
        policyId: "POL_IADE_03",
        reply: "Merhaba Zehra Hanım, açık yazdığınız için teşekkür ederiz. Kullanılmış ve etiketi kesilmiş ürünler, tekrar satılabilirliği kalmadığı için ne yazık ki iade kapsamına girmiyor. Bunun yerine bir sonraki alışverişinizde geçerli %15 indirim tanımlayabiliriz; rengine uygun bir model bulmanıza da memnuniyetle yardımcı oluruz. Usta Deri",
        timings: { nlu: 37, rag: 104, risk: 18, llm: 1130 }
      }
    },
    {
      id: "c6",
      source: "hepsiburada",
      customer: "Mert Yılmaz",
      time: "17:20",
      unread: false,
      message: "Ödeme sırasında sayfa dondu, kartımdan iki kere çekildi ama tek sipariş görünüyor. Fazla çekilen parayı ne zaman alırım?",
      order: { id: "TR-774503", product: "Deri kemer · siyah", amount: 690, deliveryDays: 0, pastOrders: 1, pastReturns: 0, unboxingVideo: false, boxDamaged: false },
      analysis: {
        category: "teknik", intent: "bilgi_talebi", confidence: 0.86, sentiment: -0.28,
        risk: { score: 0.04, level: "green", drivers: [
          { label: "Provizyon kaydı mevcut", dir: "down" }
        ] },
        priority: "orta",
        action: "Provizyonu kontrol et, iptal süresini bildir",
        steps: [
          "Ödeme panelinde ikinci provizyonun referans kodunu bulun.",
          "Askıdaki tutarın 24 saat içinde otomatik iptal edileceğini doğrulayın.",
          "Müşteriye referans koduyla birlikte bilgi verin."
        ],
        policyId: "POL_TEKNIK_01",
        reply: "Merhaba Mert Bey, merak etmeyin, siparişiniz tek ve geçerli. İkinci çekim bankanızda provizyon olarak görünüyor ve 24 saat içinde otomatik olarak iptal edilecek. Kartınıza yansıması bankanıza göre birkaç gün sürebilir. Usta Deri",
        timings: { nlu: 31, rag: 79, risk: 12, llm: 890 }
      }
    },
    {
      id: "c7",
      source: "trendyol",
      customer: "Selin Özkan",
      time: "16:52",
      unread: false,
      message: "Ayakkabının tabanı ikinci gün ayrıldı, daha 3 kere giydim. Çok üzüldüm açıkçası, değişim mümkün mü?",
      order: { id: "TR-602118", product: "Kadın loafer · taba · 38", amount: 1890, deliveryDays: 2, pastOrders: 7, pastReturns: 0, unboxingVideo: true, boxDamaged: false },
      analysis: {
        category: "urun", intent: "sikayet", confidence: 0.92, sentiment: -0.46,
        risk: { score: 0.09, level: "green", drivers: [
          { label: "7 sipariş, iade yok", dir: "down" },
          { label: "Açılış videosu var", dir: "down" }
        ] },
        priority: "yuksek",
        action: "Ayıplı ürün için birebir değişim başlat",
        steps: [
          "Tabandaki ayrılmanın fotoğrafını isteyin.",
          "Aynı numarayı stoktan ayırın.",
          "Ücretsiz değişim kodunu gönderin; yeni ürünü bekletmeden kargolayın."
        ],
        policyId: "POL_URUN_01",
        reply: "Merhaba Selin Hanım, bu bizim için de üzücü; böyle olmamalıydı. Tabandaki ayrılmanın bir fotoğrafını göndermeniz yeterli, 38 numaranızı şimdiden ayırdık. Ücretsiz değişim kodunuzu iletiyoruz, yenisini bekletmeden kargoya vereceğiz. Usta Deri",
        timings: { nlu: 36, rag: 85, risk: 13, llm: 990 }
      }
    },
    {
      id: "c8",
      source: "instagram",
      customer: "Hakan Bulut",
      time: "16:30",
      unread: false,
      message: "İadeyi geçen hafta gönderdim, sizin depoya ulaştı diye gözüküyor ama param hâlâ yatmadı.",
      order: { id: "TR-218840", product: "Deri cüzdan · kahve", amount: 540, deliveryDays: 3, pastOrders: 2, pastReturns: 1, unboxingVideo: false, boxDamaged: false },
      analysis: {
        category: "iade", intent: "bilgi_talebi", confidence: 0.89, sentiment: -0.31,
        risk: { score: 0.15, level: "green", drivers: [
          { label: "İade depoya ulaşmış", dir: "down" },
          { label: "Düşük tutar", dir: "down" }
        ] },
        priority: "orta",
        action: "İade onayını kontrol et, yansıma süresini bildir",
        steps: [
          "Depo kaydında iadenin onaylanıp onaylanmadığını kontrol edin.",
          "Onaylıysa banka talimat tarihini müşteriye iletin.",
          "Onay bekliyorsa bugün onaylayın."
        ],
        policyId: "POL_IADE_05",
        reply: "Merhaba Hakan Bey, iadeniz depomuza ulaştı ve onaylandı; bankaya iade talimatı verildi. Kredi kartlarında 1-3 iş günü, banka kartlarında 2-7 iş günü içinde hesabınıza yansıyacaktır. Anlayışınız için teşekkür ederiz. Usta Deri",
        timings: { nlu: 34, rag: 82, risk: 13, llm: 940 }
      }
    },
    {
      id: "c9",
      source: "trendyol",
      customer: "Derya Çelik",
      time: "15:48",
      unread: false,
      message: "Siparişim 24 saat geçmeden Elazığ'a ulaştı, özenli paketleme ve hediyeniz için çok teşekkürler, harika esnafsınız!",
      order: { id: "TR-872134", product: "Deri anahtarlık seti", amount: 480, deliveryDays: 1, pastOrders: 6, pastReturns: 0, unboxingVideo: false, boxDamaged: false },
      analysis: {
        category: "genel", intent: "tesekkur", confidence: 0.97, sentiment: 0.92,
        risk: { score: 0.02, level: "green", drivers: [
          { label: "Olumlu geri bildirim", dir: "down" }
        ] },
        priority: "dusuk",
        action: "Teşekkür et, değerlendirme rica et",
        steps: [
          "Kısa ve samimi bir teşekkür gönderin.",
          "Ürün sayfasında değerlendirme bırakmasını rica edin."
        ],
        policyId: "POL_GENEL_02",
        reply: "Merhaba Derya Hanım, güzel sözleriniz için çok teşekkür ederiz, gününüzü güzelleştirdiysek ne mutlu bize. Deneyiminizi ürün sayfasında paylaşırsanız diğer alıcılara da yol göstermiş olursunuz. Yine bekleriz! Usta Deri",
        timings: { nlu: 29, rag: 71, risk: 11, llm: 820 }
      }
    }
  ];

  const SOURCES = {
    trendyol: { label: "Trendyol", short: "TY" },
    hepsiburada: { label: "Hepsiburada", short: "HB" },
    instagram: { label: "Instagram", short: "IG" },
    whatsapp: { label: "WhatsApp", short: "WA" },
    site: { label: "Mağaza sitesi", short: "MS" }
  };

  return { POLICIES, CASES, SOURCES };
})();
