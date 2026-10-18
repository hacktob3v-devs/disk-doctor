# 🏆 EsnafDoktor — Fırat Üniversitesi Jürisi İçin 10 Soru ve Cevap Rehberi
**Hacktoberfest Elazığ 2026 · Week 2 "Side Hustle" Final Savunması**

Bu belge, jüri sunumu sırasında gelebilecek en kritik 10 soruya verilecek doğrudan, teknik ve net yanıtları içerir. Buradaki her sayı repodaki betiklerle yeniden üretilebilir (`docs/metrics.md`).

---

### Soru 1: Çözdüğünüz problem nedir ve kime hitap ediyor?
> **Cevap:**  
> - **Problem:** E-ticaret sitelerinde satıcıya sorulan sorular ("kargom nerede?", "beden değişebilir mi?", "iki kere çekildi") çoğu zaman saatlerce cevapsız kalıyor. Küçük satıcı siparişi de paketliyor, günde yüzlerce mesaja da yetişemiyor. Geç cevap mağaza puanını düşürüyor; aceleyle her iadeyi onaylamak ise sahte iadelere kapı açıyor.  
> - **Çözüm:** EsnafDoktor gelen mesajı sınıflandırıyor, mağazanın kendi kuralıyla eşleştiriyor, sipariş verisinden risk hesaplıyor ve rutin soruları saniyeler içinde yerel modelle yanıtlıyor. Riskli olanları ise önerilen karar, kontrol listesi ve taslak yanıtla satıcıya iletiyor.

---

### Soru 2: Gemma burada tam olarak nerede ve nasıl kullanılıyor?
> **Cevap:**  
> **Gemma 3 4B** (açık ağırlıklı), Ollama ile satıcının kendi bilgisayarında çalışan **yanıt yazarıdır**:
> 1. Hattın bulduğu mağaza kuralını ve müşterinin mesajını alır.
> 2. Yalnızca o kurala dayanarak 3 cümleyi geçmeyen, "siz" diye hitap eden Türkçe bir yanıt yazar (müşteri sayfası) ya da satıcı için taslak hazırlar ("Yeniden yaz").
> 3. Yazdığı yanıt bir **dayanak denetiminden** geçer (bkz. Soru 7).
> 
> Isınmış hâlde yanıt süresi ortalama **~1,4 sn**, GPU belleği **2,9 GB**. Karar (iade onayı/reddi) Gemma'ya bırakılmaz; o satıcıdadır. Model satıcı masasından tek tıkla değiştirilebilir (Qwen, Llama…).

---

### Soru 3: Neden kapalı bir bulut API (GPT-4o / Claude) değil de yerel açık kaynak?
> **Cevap:**  
> 1. **0 TL değişken maliyet:** Mesaj başına ödenen token faturası küçük işletme için sürdürülebilir değil; yerel model bilgisayar açık olduğu sürece bedava.  
> 2. **Veri gizliliği (KVKK):** Müşteri adı, adresi, sipariş bilgisi yurt dışı sunuculara gitmez; diskte kalır.  
> 3. **İnternetsiz çıkarım:** Modeller bir kez indirildikten sonra çıkarım tamamen yerelde yapılır.  
> 4. **Kilitlenme yok:** Model ve fiyat sağlayıcıya bağlı değil; daha iyi bir açık model çıkınca değiştirilir.

---

### Soru 4: TabPFN burada ne iş yapıyor, LLM'den farkı ne ve hangi verilere dayanıyor?
> **Cevap:**  
> 1. **Resmi kategori:** Yarışma şartnamesinde (Sayfa 20) **200$ ödüllü 'Best Use of TabPFN'** partner kategorisi var.  
> 2. **Hangi veriler?** LLM metin okur ama sipariş geçmişini bilmez. Risk modeli 5 tablo verisine bakar:
>    - `Sipariş Tutarı`: 100 TL'lik kupa mı, 5.800 TL'lik mont mu?
>    - `Teslimat Süresi`
>    - `Müşteri Geçmiş İade Oranı`: Sadık müşteri mi, sistematik iade istismarcısı mı?
>    - `Kutu Açılış Videosu`: Var mı, yok mu?
>    - `Kargo Hasar Bildirimi`: Var mı, yok mu?
> 3. **Bugünkü durum (dürüst):** TabPFN entegrasyonu kodda hazır; ancak güncel TabPFN sürümü ağırlıkları indirmek için PriorLabs lisans onayı istiyor. Onay verildikten sonra `ED_USE_TABPFN=1` ile açılıyor. O zamana kadar aynı 5 özellikten kalibre edilmiş bir lojistik formül kullanılıyor ve `/api/health` bunu açıkça `calibrated_rf_fallback` olarak gösteriyor.  
> 4. **Karar farkı:** Risk yüksek çıktığında asistan müşteriye para iadesi sözü vermez; mesaj satıcıya "Acil" olarak düşer ve inceleme adımları önerilir.

---

### Soru 5: RAG mimariniz neden 'eski usul RAG' değil, ne farkı var?
> **Cevap:**  
> Yalnızca vektör benzerliği kısa Türkçe kural metinlerinde yetersiz kalıyor. Bunu ölçtük:
> - **BM25 (Türkçe normalize)** tek başına: kural Hit@1 **%81,0**
> - **multilingual-e5-small** tek başına: **%71,4**
> - **Hibrit BM25 + E5 + RRF (k=60):** **%81,0**
> - **Bizim son aşama** — RRF + kuralın anahtar kelimeleri + Cross-Encoder'ı (mmarco mMiniLMv2) *yalnızca ağırlık* olarak kullanan yeniden sıralama: **%95,2** (21 mesajda 20)
> 
> Cross-Encoder'ı tek başına karar verici yaptığımızda başarı **17/21**'e düşüyordu; kısa Türkçe kurallarda skorları çok birbirine yakın. Bu yüzden onu sıralamayı ince ayarlayan bir sinyal olarak kullanıyoruz. Ablasyon: `python scripts/evaluate_honest_metrics.py`.

---

### Soru 6: Veri setiniz sentetik mi, gerçek mi? Veri sızıntısı (leakage) var mı?
> **Cevap:**  
> 1. Değerlendirme, eğitimde hiç kullanılmamış **20 zorlu sınır vakasından** oluşan ayrılmış bir sette yapıldı (`data/holdout_gold.jsonl`).
> 2. Sistemin kategori doğruluğu bu sette **%95,0** (macro F1 %93,8).
> 3. İnce ayarlı BERTurk modellerimiz bu repoda değil; repoda çalışan NLU anahtar kelime yedeği ve tek başına %60 doğrulukta kalıyor. Bu yüzden arayüzde kategoriyi daha isabetli olan kural eşleşmesinden alıyoruz. BERTurk dosyaları `models/` klasörüne konduğunda otomatik devreye giriyor.
> 4. Sentetik veri motoru, 8 farklı kullanıcı davranışı ve mobil klavye yazım hataları içeren 3.000 satırlık bir set üretiyor (`scripts/generate_realistic_synthetic.py`).

---

### Soru 7: Sistem kural uydurur veya yanlış bilgi (halüsinasyon) verirse ne olur?
> **Cevap:**  
> - **Dayanak denetimi:** Gemma'nın yanıtındaki her sayı (gün, tutar, kod) eşleşen kural metninde ya da müşterinin mesajında geçmek zorunda. Geçmiyorsa yanıt daha katı bir talimatla bir kez yeniden yazdırılır; yine geçmezse kurala dayalı şablon yanıt gönderilir. Geliştirme sırasında Qwen'in "iade süreniz 7 gün" diye uydurduğu bir yanıtı bu denetim yakaladı.
> - Test ettiğimiz 8 örnek soru ve yorumda Gemma 3 4B'nin 8 yanıtının 8'i denetimden ilk denemede geçti.
> - **Sistem satıcının yerine karar almaz:** Kullanılmış ürün iadesi, öfkeli dil ya da yüksek risk gibi durumlarda müşteriye yalnızca "mağaza sahibine ilettim" yanıtı gider; kararı satıcı verir. Hasar ve ayıplı ürün durumunda model yalnızca fotoğraf ister.

---

### Soru 8: İnternet tamamen kopsa bu sistem gerçekten çalışır mı?
> **Cevap:**  
> Evet, modeller bir kez indirildikten sonra. Gemma (Ollama), E5, Cross-Encoder, NLU ve risk modeli bilgisayarın kendi donanımında çalışıyor; hiçbir bulut API çağrısı yok.  
> İki istisnayı açıkça söylüyoruz: tarayıcının **sesle yazma** özelliği (Chrome/Edge) sesi bulut servisine gönderiyor, sayfa yazı tipleri de internetsizken sistem yazı tiplerine düşüyor. Yanıtları sesli okuma ise tamamen yerel.

---

### Soru 9: Bu sistemin işletmeye somut ekonomik faydası nedir? (İş Modeli)
> **Cevap:**  
> - Rutin soruların (kargo, beden, iade süresi, çift çekim) cevabı saatler yerine **~2 saniyede** gidiyor; mağaza puanı korunuyor.
> - Haksız kabul edilen tek bir sahte iade ya da tutanaksız kargo hasarı satıcının kâr marjını yok eder. Riskli vakaların satıcıya gerekçesiyle düşmesi bu kaybı önler.
> - Mesaj başına API ücreti olmadığı için maliyet mesaj sayısıyla artmıyor.

---

### Soru 10: Açık kaynak dünyasına ve topluluğa somut katkınız nedir?
> **Cevap:**  
> 1. MIT lisanslı, uçtan uca çalışan açık kaynak bir repo (FastAPI + sade HTML/CSS/JS arayüz).
> 2. Türk e-ticareti için 16 maddelik hukuki ve operasyonel politika veri seti.
> 3. Kural düzeyinde ölçülen, ablasyonu yeniden üretilebilir bir Türkçe hibrit RAG.
> 4. Küçük açık modellerin kural uydurmasını yakalayan basit, açıklanabilir bir dayanak denetimi.
> 5. Gerçekçi davranışlar ve yazım hataları içeren açık kaynak sentetik veri üretim motoru.
