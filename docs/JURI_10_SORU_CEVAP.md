# 🏆 EsnafDoktor — Fırat Üniversitesi Jürisi İçin 10 Altın Soru ve Cevap Rehberi
**Hacktoberfest Elazığ 2026 · Week 2 "Side Hustle" Final Savunması**

Bu belge, jüri üyelerinin (Arş. Gör. Mehmet Arzu, Öğr. Gör. Semih Yücel, Arş. Gör. Diyar Güzelses, Arş. Gör. Muhammed Veysi Güler, Arş. Gör. Mert İncidelen) sunum esnasında soracağı en kritik 10 soruya verilecek profesyonel, bilimsel ve net cevapları içerir.

---

### Soru 1: Çözdüğünüz problem tam olarak ne, kime hitap ediyor?
> **Cevap:**  
> "Elazığ Kapalı Çarşı'da ve yerel sanayide Trendyol, Hepsiburada ve WhatsApp üzerinden online satış yapan küçük butik ve esnafı hedefliyoruz. Mehmet Usta gibi esnaflar her akşam 18:00 - 22:00 arasında paketleme yaparken 150'den fazla uyuşmazlık mesajı alıyor ('Kargom nerede?', 'Kutu ezik paramı verin!'). Geç cevap verirse pazar yeri puanı düşüyor; her iadeyi körü körüne kabul ederse sahte/kullanılmış ürün iadeleri kârını yok ediyor. EsnafDoktor, esnafın dükkandaki laptopunda 0 TL API maliyetiyle saniyeler içinde doğru kararı veren yapay zekâ asistanıdır."

---

### Soru 2: Google DeepMind Gemma 4 burada tam olarak nerede ve nasıl kullanılıyor?
> **Cevap:**  
> "Gemma 4 projemizin **'Akıl Yürütme ve Karar Motoru'**dur (Focal Intelligence Hub). Sistemde sadece metin tamamlama yapmaz:
> 1. BERTurk'ün çıkardığı niyet ve kategoriyi alır,
> 2. 2026 Hibrit RAG motorunun bulduğu mağaza politikasını bağlam olarak okur,
> 3. TabPFN'in hesapladığı sayısal iade riskini değerlendirir,
> 4. Ve esnaf için 4 adımlı şeffaf akıl yürütme (Chain-of-Thought) ile:
>    - **Esnaf Aksiyon Kartı** (Adım adım ne yapmalı?),
>    - **Müşteriye Hazır Türkçe Yanıt** (WhatsApp'a kopyalanacak metin),
>    - **Seslendirilebilir Esnaf Özeti** üretir."

---

### Soru 3: Neden kapalı bir API (OpenAI GPT-4o / Claude) değil de yerel açık kaynak?
> **Cevap:**  
> *(Sunum slayt 18'e doğrudan atıf yaparak:)*  
> "1. **Sıfır Değişken Maliyet (0.00 TL):** Günde 200 mesaj alan küçük esnaf ayda ~15.000 TL OpenAI token faturası ödeyemez.  
> 2. **%100 Çevrimdışı Çalışma:** Kapalı Çarşı'nın taş tonozlu dükkanlarında internet kopsa bile sistem kesintisiz çalışır. (Birazdan Wi-Fi'ı kapatıp göstereceğiz).  
> 3. **Müşteri Verisi ve KVKK:** Alıcının adresi, telefonu ve sepet tutarı yabancı bulutlara gitmez; dükkan bilgisayarında kalır.  
> 4. **Niş Tablo Yeteneği:** GPT-4o sayısal sipariş parametrelerinden arıza/suistimal riski hesaplayamaz; bunu TabPFN ile yerelde çözüyoruz."

---

### Soru 4: TabPFN burada ne iş yapıyor, LLM'den farkı ne?
> **Cevap:**  
> "Büyük Dil Modelleri (LLM) metin anlama için mükemmeldir ancak continuous/tabular telemetride (sipariş tutarı, teslimat günü, müşterinin geçmiş iade oranı, kutu açılış videosu varlığı) güvenilir olasılık dağılımı üretemez, sayı uydurur. TabPFN, Prior Labs'in geliştirdiği tabular temel modeldir. Dükkandaki CPU üzerinde 18 milisaniyede çalışarak siparişin iade suistimali riskini (Yeşil/Sarı/Kırmızı) matematiksel olarak kalibre eder ve esnafı uyarır."

---

### Soru 5: RAG mimariniz neden 'eski usul RAG' değil, 2026 seviyesinde ne farkı var?
> **Cevap:**  
> "Geçen yılın projelerindeki RAG'ler basit bir ChromaDB'ye metin gömüp düz kosinüs benzerliği yapıyordu. Bu yapı Türkçe eklemeli dilde ve 9 haneli kargo kodlarında başarısız oluyordu. Biz 2026 seviyesinde **Two-Stage Agentic Hybrid RAG** kurduk:
> - **Aşama 1 (Hibrit Getirme):** Türkçe Okapi BM25 (anahtar kelime) + Multilingual-E5 (anlamsal yoğun vektör) paralel çalışır.
> - **Aşama 2 (Rank Füzyonu):** Reciprocal Rank Fusion (RRF $k=60$) ile skorlar adil birleştirilir.
> - **Aşama 3 (Cross-Encoder):** Adaylar yerel Cross-Encoder ile anlamsal tam örtüşmeye göre yeniden puanlanır.
> - **Aşama 4 (Self-RAG Guard):** Kuralda dayanağı olmayan hiçbir bilginin üretilmesine izin verilmez."

---

### Soru 6: Veri setiniz sentetik mi, gerçek mi? Veri sızıntısı (leakage) var mı?
> **Cevap:**  
> "Hocam, jürimizin veri bilimi hassasiyetini bildiğimiz için projemizde 3 katmanlı dürüst bir veri mimarisi kurduk:
> 1. BERTurk modellerimiz 18.000+ gerçek Google Play / Şikayetvar incelemelerinden eğitilmiş ağırlıklardır.
> 2. Sentetik tarafımızda robotik şablonları çöpe attık; 8 farklı gerçekçi insan personası (öfkeli, aceleci genç, yaşlı, pazarlıkçı) ve mobil klavye typo enjeksiyonu içeren 3.000 satırlık zengin bir veri seti ürettik.
> 3. En önemlisi: **Held-Out Gold Test Setimiz** (20 zorlu sınır ve çoklu niyet vakası) modelin daha önce hiç görmediği gerçek kullanıcı ifadeleridir. Skorlarımızın yapay %100 değil, dürüst %73.2 - %88.0 bandında olması sızıntısız validasyonumuzun açık kanıtıdır."

---

### Soru 7: Sistem yanlış veya halüsinasyon bir kural söylerse esnafa zararı ne olur?
> **Cevap:**  
> "EsnafDoktor ustanın yerine geçmez; ustaya 'Öneri ve Kontrol Adımları' sunar. Halüsinasyonu önlemek için Self-RAG politikamız devrededir: Gemma'nın ürettiği karar getirilen 16 doğrulanmış mağaza politikasının token desteğiyle doğrulanır. Dayanağı olmayan hiçbir süre (örn. '14 gün' yerine '30 gün') söylenemez. Son karar ve WhatsApp gönderim onayı her zaman esnaftadır."

---

### Soru 8: Dükkanda internet tamamen kopsa bu sistem gerçekten çalışır mı?
> **Cevap:**  
> "Kesinlikle evet. Şu anda laptopumuzun Wi-Fi bağlantısını tamamen kapatıyoruz. Üst bantta 'Tamamen Çevrimdışı' rozetini görüyorsunuz. BERTurk, TabPFN, E5 embedding ve Gemma modellerinin tümü bilgisayarımızın SSD'sinde yerel çalışmaktadır. Sıfır dış ağ çağrısı vardır."

---

### Soru 9: Esnaf bu araca gerçekten para verir mi? (Side Hustle İş Modeli)
> **Cevap:**  
> "Elazığ Kapalı Çarşı'daki esnafımızla yaptığımız görüşmede şu rakam çıktı: Haksız kabul edilen tek bir deri ceket iadesi esnafa 5.800 TL doğrudan zarar yazıyor. Kargo hasarında tutanak tutturulmadığı için kargo firmasının ödemediği tazminat esnafın cebinden çıkıyor. EsnafDoktor, ayda yalnızca 2 sahte iadeyi ve 3 kargo tazminatını kurtardığında esnafa ayda en az 10.000 - 15.000 TL doğrudan nakit koruma sağlıyor. Esnaf bu sistem için tek seferlik 1.500 TL veya aylık 250 TL bakım ücretini seve seve ödeyeceğini teyit etmiştir."

---

### Soru 10: Açık kaynak dünyasına ve topluluğa somut katkınız nedir?
> **Cevap:**  
> "1. MIT lisanslı, uçtan uca çalışan açık kaynak bir repo sunduk.  
> 2. Türk e-ticaret esnafı için 16 kapsamlı hukuki ve operasyonel politika metnini açık veri olarak paylaştık.  
> 3. 8 persona ve typo gürültüsü içeren açık kaynaklı sentetik veri üretim motorunu literatüre sunduk.  
> 4. Google DeepMind Gemma 4 ve Prior Labs TabPFN'i gerçek bir mikro-işletme probleminde birleştiren ilk yerel mimariyi oluşturduk."
