# 🏆 EsnafDoktor — Fırat Üniversitesi Jürisi İçin 10 Soru ve Cevap Rehberi
**Hacktoberfest Elazığ 2026 · Week 2 "Side Hustle" Final Savunması**

Bu belge, jüri sunumu sırasında gelebilecek en kritik 10 soruya verilecek doğrudan, teknik ve net yanıtları içerir.

---

### Soru 1: Çözdüğünüz problem nedir ve kime hitap ediyor?
> **Cevap:**  
> - **Problem:** E-ticaret yapan KOBİ ve satıcılar her gün onlarca iade, kargo hasarı ve uyuşmazlık mesajı alıyor. Yanıt vermekte gecikirlerse pazar yeri puanları düşüyor; haksız veya sahte iadeleri körü körüne onaylarlarsa doğrudan maddi zarar ediyorlar.  
> - **Çözüm:** EsnafDoktor; gelen mesajı NLU ile anlayan, mağaza politikalarıyla eşleştiren, sipariş verilerinden suistimal riskini hesaplayan ve satıcıya anında aksiyon planı + hazır müşteri yanıtı sunan yerel bir asistandır.

---

### Soru 2: Google DeepMind Gemma 4 burada tam olarak nerede ve nasıl kullanılıyor?
> **Cevap:**  
> Gemma 4 sistemin **Akıl Yürütme ve Karar Motoru**dur (Reasoning Hub):
> 1. BERTürk'ün çıkardığı niyet ve kategoriyi alır.
> 2. Hibrit RAG motorunun getirdiği resmi mağaza politikasını okur.
> 3. TabPFN'in hesapladığı sipariş risk olasılığını değerlendirir.
> 4. Satıcı için 3 somut çıktı üretir:
>    - **Aksiyon Kartı:** Satıcının atması gereken adım adım kontrol listesi.
>    - **Müşteri Yanıtı:** WhatsApp veya pazar yeri için hazır, kurallara uygun Türkçe yanıt.
>    - **Sesli Özet:** Satıcının işini aksatmadan dinleyebileceği 1 cümlelik sesli durum özeti.

---

### Soru 3: Neden kapalı bir bulut API (GPT-4o / Claude) değil de yerel açık kaynak?
> **Cevap:**  
> 1. **0 TL API Maliyeti:** Küçük işletmeler için değişken token faturaları sürdürülebilir değildir.  
> 2. **Veri Gizliliği (KVKK):** Müşteri adresleri, telefonları ve sipariş verileri dış sunuculara gitmez; cihazda kalır.  
> 3. **Çevrimdışı Çalışma:** İnternet kesilse bile yerel donanımda kesintisiz çalışır.  
> 4. **Çok Modlu Hibrit Yapı:** Yalnızca metin değil, TabPFN ile tabüler sipariş riskini de yerelde birleştirir.

---

### Soru 4: TabPFN burada ne iş yapıyor, LLM'den farkı ne ve hangi verilere dayanıyor?
> **Cevap:**  
> 1. **Resmi Kategori:** Yarışma şartnamesinde (Sayfa 20) doğrudan **200$ ödüllü 'Best Use of TabPFN'** partner kategorisi bulunmaktadır.  
> 2. **Hangi Güvenilir Veriler?:** LLM'ler metin okur ama arka plandaki gerçeği bilmez. TabPFN ise sipariş sistemindeki 5 doğrulanmış tablo verisini inceler:
>    - `Sipariş Tutarı`: 100 TL'lik kupa mı, 5.800 TL'lik mont mu?
>    - `Teslimat Süresi`: Taze teslimat mı, 14 günlük yasal sürenin son dakikası mı?
>    - `Müşteri Geçmiş İade Oranı`: Sadık müşteri mi, sistematik iade istismarcısı mı?
>    - `Kutu Açılış Videosu`: Var mı, yok mu?
>    - `Kargo Hasar Tutanağı`: Var mı, yok mu?
> 3. **Karar Farkı:** TabPFN bu parametreleri CPU üzerinde 18 milisaniyede işleyerek matematiksel risk skoru üretir. Gemma bu risk kırmızı çıktığında müşteriye körü körüne para iadesi yapmaz; satıcıyı sahte iadelerden koruyacak inceleme adımlarını devreye sokar.

---

### Soru 5: RAG mimariniz neden 'eski usul RAG' değil, 2026 seviyesinde ne farkı var?
> **Cevap:**  
> Standart RAG sistemleri yalnızca basit vektör benzerliği kullanır; bu da Türkçe eklemeli dilde ve 9 haneli kargo takip kodlarında başarısız olur.  
> **İki Aşamalı Hibrit RAG Mimarimiz:**
> - **1. Aşama (Hibrit Arama):** Türkçe Okapi BM25 (anahtar kelime) + Multilingual-E5 (anlamsal vektör) paralel çalışır.
> - **2. Aşama (Rank Füzyonu):** Reciprocal Rank Fusion (RRF $k=60$) ile iki getirme listesi adil biçimde birleştirilir.
> - **3. Aşama (Cross-Encoder):** Aday politikalar sorgu-doküman tam örtüşmesine göre yeniden sıralanır (Rerank).
> - **4. Aşama (Self-RAG Guard):** Kural metninde dayanağı olmayan hiçbir sürenin veya bilginin üretilmesine izin verilmez.

---

### Soru 6: Veri setiniz sentetik mi, gerçek mi? Veri sızıntısı (leakage) var mı?
> **Cevap:**  
> 1. BERTürk sınıflandırıcımız 18.000+ gerçek Türkçe e-ticaret ve şikayet verisiyle eğitilmiştir.
> 2. Sentetik veri motorumuzda robotik şablonlar yerine 8 farklı kullanıcı davranışı ve mobil klavye yazım hatası (typo) içeren 3.000 satırlık gerçekçi bir set oluşturduk.
> 3. Modeli tamamen izole edilmiş 20 zorlu sınır vakası (Held-Out Gold Set) üzerinde test ettik. Sonuçlarımız yapay bir %100 değil; gerçek dünya şartlarını yansıtan dürüst %73.2 - %88.0 F1 bandındadır.

---

### Soru 7: Sistem kural uydurur veya yanlış bilgi (halüsinasyon) verirse ne olur?
> **Cevap:**  
> - Sistem satıcının yerine karar almaz; 'Öneri ve Kontrol Adımları' sunar.
> - Self-RAG denetimi sayesinde Gemma'nın kararları doğrulanmış 16 mağaza politikasıyla birebir eşleştirilir; dayanağı olmayan süre (örn. 14 gün yerine 30 gün) üretilemez.
> - Müşteriye gönderilecek mesaja ve nihai aksiyona her zaman satıcı onay verir.

---

### Soru 8: İnternet tamamen kopsa bu sistem gerçekten çalışır mı?
> **Cevap:**  
> Evet. BERTürk, TabPFN, E5 embedding ve Gemma modellerinin tümü bilgisayarın kendi donanımında yerel olarak çalışır. Sıfır dış ağ veya bulut API çağrısı vardır.

---

### Soru 9: Bu sistemin işletmeye somut ekonomik faydası nedir? (İş Modeli)
> **Cevap:**  
> - Haksız kabul edilen tek bir sahte iade veya tutanaksız kargo hasarı doğrudan satıcının kâr marjını yok eder.
> - EsnafDoktor, ayda birkaç hatalı iadeyi veya kargo tazminat hakkını kurtararak işletmeye doğrudan binlerce liralık nakit koruma sağlar ve mağaza puanının düşmesini engeller.

---

### Soru 10: Açık kaynak dünyasına ve topluluğa somut katkınız nedir?
> **Cevap:**  
> 1. MIT lisanslı, uçtan uca çalışan açık kaynak bir repo.
> 2. Türk e-ticaret ekosistemi için 16 maddelik standart hukuki ve operasyonel politika veri seti.
> 3. Gerçekçi davranışlar ve yazım hataları içeren açık kaynak sentetik veri üretim motoru.
> 4. Gemma 4 akıl yürütmesi ile TabPFN tabüler risk modelini yerelde birleştiren ilk mimari referansı.
