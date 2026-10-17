# DiskDoctor - Projeyi Anlama ve Jüriye Hazırlık

17 Ekim 2026 | Türkçe sunum ve konuşmacı rehberi

Bu belge, güncel kodun ne yaptığını ve hedef ürünün ne yapacağını ayrı anlatır. Teknik denetim tabanı: GitHub main `a0944ba`. Önceki Kişi 1 dalı main'e birleştirilmiştir. Sonraki ekip değişiklikleri ayrıca kontrol edilmelidir.

**Önerilen ürün cümlesi:** DiskDoctor, küçük bilgisayar servislerinin müşteri şikâyetlerini kaynaklı kontrol adımlarına ve anlaşılır servis raporuna dönüştürmesini hedefleyen yerel bir asistandır. Disk sağlık değerlendirmesi, gerektiğinde eklenen bir kanıt kaynağıdır.

**Bugünkü dürüst durum:** Disk veri/model modülleri ölçülmüştür; arayüz eklenmiştir. Gerçek RAG, Gemma, ön teşhis ve üretken rapor modülleri bu sürümde mevcut değildir. Arayüz bu bölümlerde mock kullanır. Bu PDF bir tamamlanmış ürün beyanı değil, mevcut kanıtları ve önerilen geliştirme yönünü açıklayan hazırlık dosyasıdır.

**Nasıl kullanılır?** İlk bölümler projeyi öğretir; son bölümler üç dakikalık anlatımı, demo planını, jüri sorularını ve teslim kontrolünü içerir. Her sayfayı sahnede okumak gerekmez. Kısa konuşma ve soru-cevap hazırlığı aynı dosyada toplanmıştır.

**Kanıt dili:** Ölçüldü = kayıtlı deney var. Uygulandı = kod var. Plan = henüz çalışan özellik değil. Varsayım = kullanıcı veya saha verisiyle sınanması gerekiyor.

## 01 | Hangi problemi çözüyoruz?

Küçük bir bilgisayar servisine gelen şikâyet çoğunlukla teknik değildir: “Yavaşladı”, “Görüntü gelmiyor”, “Bir süre sonra kapanıyor.” Tek cümle, arızanın nedenini belirlemez. Servis çalışanı eksik bilgiyi toplar, muhtemel nedenleri araştırır, uygun kontrolleri seçer ve müşteriye yapılan işi açıklar.

**Hedeflediğimiz tekrar eden iş:** Şikâyeti tutarlı sorulara, kaynaklı kontrol listesine ve anlaşılır servis notuna dönüştürmek. Özellikle deneyimi az çalışanların bilgi aramasını ve kayıt hazırlamasını kolaylaştırmak istiyoruz. Bunun her serviste büyük zaman kaybı yarattığı henüz ölçülmüş değildir; ilk kullanıcı görüşmesinin konusu budur.

Örnek: “Laptop donuyor.” Önce ne zaman donduğu, hata mesajı, yeni donanım veya yazılım değişikliği sorulur. Disk şüphesi oluşursa SMART sağlık kaydı eklenir. Sıcaklık şüphesi varsa uygun kontroller önerilir. Bütün şikâyetler disk arızası olarak yorumlanmaz.

**Beklenen fayda:** Daha düzenli bilgi toplama, unutulan soruların azalması, kaynak aramaya daha az zaman ayırma ve müşteriye daha anlaşılır açıklama. Bunlar ürün hedefleridir; henüz ölçülmüş tasarruf oranları değildir.

**Sınır:** Ürün fiziksel arızayı kendi başına kesin teşhis etmez, bilgisayarı otomatik onarmaz, silinmiş dosyaları kurtarmaz. Kontrolü uygulayan ve sonucu doğrulayan kişi teknisyendir. Veri kaybını önleme garantisi verilmez.

**Jüriye kısa cevap:** “Tamircinin şikâyeti sistemli şekilde inceleme ve müşteriye açıklama işini kolaylaştırıyoruz. Başarıyı, kaynaklı doğru kontrol önerileri ve ölçülen iş süresiyle göstermek istiyoruz.”

## 02 | Kim kullanır, kim satın alır?

**İlk hedef kullanıcı:** Tek veya birkaç çalışanı olan bilgisayar tamircisi ve bağımsız teknik servis. Günlük kullanıcı teknisyen; satın alma kararını muhtemelen dükkân sahibi verir. Bu müşteri seçimi henüz görüşmeyle doğrulanmış değildir.

**Neye para verebilir?** İnternetten tek bir cevap bulmaya değil; yerel kuruluma, dükkânın kendi bilgi birikimini aramaya, tekrar kullanılabilen servis kayıtlarına ve müşteriye verilecek tutarlı rapora. Satılabilir değer, ücretsiz bileşenlerin iş akışına güvenilir biçimde yerleştirilmesidir.

**Önerilen iş modeli:** Açık kaynak çekirdeğin yanında ücretli kurulum, veri hazırlama, güncelleme ve destek. Dükkâna özel bilgi tabanı ve yedekleme desteği daha sonraki hizmetler olabilir. Abonelik veya tek seferlik ücret seçimi, müşterinin tercihine göre sınanmalıdır. Henüz fiyat, müşteri, satış veya gelir yoktur.

**Ucuz doğrulama:** Bir servis sahibine mevcut işini uygulama kullanmadan yaptır; kaç dakika sürdüğünü kaydet. Aynı tür görevleri asistanla yaptır; kaynak doğruluğunu, rapor düzeltmelerini ve süreyi karşılaştır. Sonra “Kullanır mısınız?”, “Hangi koşulda ödeme yaparsınız?” diye sor. Olumlu söz, ödeme yapılmış satış sayılmaz.

**Ekonomik örnek - yalnızca varsayım:** Bir görevde 3 dakika, günde 10 görev ve ayda 22 gün kazanılsa 11 saat eder. Bu bizim sonucumuz değildir. Gerçek kullanımda bu üç sayı ölçülmeden fiyat gerekçesi yapılamaz.

**Jüriye kısa cevap:** “İlk müşterimiz küçük teknik servis sahibi. Ödeme isteğini henüz doğrulamadık; önce kurulum ve raporlama hizmetinin gerçek iş süresini azaltıp azaltmadığını ölçeceğiz.”

## 03 | RAG ana ürün, disk ek özellik olsun mu?

**Önerim: Evet, ürünün ana girişi şikâyet ve kaynaklı yardım olsun.** Çünkü görüntü gelmemesi, ısınma ve açılmama gibi birçok servis şikâyeti disk problemi değildir. Her müşteriden SMART çıktısı istemek gereksiz bir giriş engeli yaratır. Disk değerlendirmesi, ilgili vakalarda isteğe bağlı ek kanıt olarak kullanılabilir.

**İki yönün karşılaştırması:** Disk odaklı ürün daha dar kapsamlıdır; mevcut ölçülmüş modüllerle gösterilmesi daha kolaydır. RAG odaklı ürün daha fazla servis şikâyetini kapsar, fakat bilgi tabanı kalitesi ve yanlış öneri denetimi için ek iş gerektirir. Daha geniş kapsam otomatik olarak daha iyi ürün anlamına gelmez.

**Küçük başlangıç kapsamı:** Açılış/görüntü, ısınma/kapanma ve yavaşlık/depolama olmak üzere üç şikâyet ailesi. Her konuda her soruya cevap verme hedefi koymayalım. Hedef; ilgili kaynak, eksik bilgi sorusu, kontrol listesi ve servis notudur.

**Disk çalışması boşa gitmez:** Hazırladığımız parser, HDD modeli, NVMe kuralları ve ölçümler gerektiğinde çağrılan ayrı bir modül olur. Ödül kategorisi için gereksiz şekilde her soruya TabPFN bağlanmaz; gerçek görevi olan sayısal disk verisinde kullanılır.

**İlk prototip kapsamı:** Metin girişi ve metin çıkışı. STT ve TTS dahil değil. Cihaz geçmişi, ses, otomatik donanım tarama ve kapsamlı ilişki grafiği sonraki adaylardır.

Bu belgede önerilen ürün yönü açıklanmıştır; kodun bu akışa dönüştürüldüğü anlamına gelmez. Önce Kişi 2'nin gerçek RAG/Gemma akışı, ardından Kişi 3'ün bu akışı arayüze bağlaması gerekir.

## 04 | Kullanıcı uygulamada ne yapacak?

**Hedef akış - henüz tamamlanmadı:**

1. Teknisyen müşteri şikâyetini ve varsa cihaz modelini yazar.
2. Asistan eksik bilgiyi sorar: Ne zaman başladı? Açılışta mı? Hata mesajı var mı? Son değişiklik neydi?
3. Yerel bilgi tabanından ilgili vakalar bulunur. Kaynak başlığı ve bağlantısı gösterilir.
4. Yerel dil modeli, kaynakları ve verilen bilgileri kullanarak olası nedenler ile kontrol sırasını yazar.
5. Teknisyen kontrolleri yapar; sonuçları kaydeder. Asistanın önerisi, yapılmış işlem gibi rapora yazılmaz.
6. Gerekliyse SMART JSON eklenir; disk modülü ölçülen değerleri ve değerlendirmeyi sağlar.
7. Müşteriye şikâyet, gözlem, yapılan kontrol ve önerilen işlem ayrımıyla servis raporu hazırlanır.

**Örnek A - görüntü yok:** “Fanlar dönüyor ama ekran siyah.” Harici ekran sonucu ve hata/bip bilgisi sorulur. Kaynaklı kontrol önerilir. SMART eklemek zorunlu değildir. “Kesin ekran kartı arızası” denmez.

**Örnek B - yavaşlık ve disk sesi:** Şikâyet alınır, veri önemi sorulur. Veri kaybı şüphesinde gereksiz yük oluşturan testler yerine yedekleme veya uzman değerlendirmesi önceliklendirilir. Uygun durumdaysa sağlık raporu eklenir. SMART bulgusu tek başına kesin teşhis sayılmaz.

Bu örnekler ürün davranışını açıklamak için hazırlanmıştır; gerçek kullanıcı görüşmesi, doğrulanmış arıza kaydı veya çalışan RAG çıktısı değildir.

## 05 | Mimariyi basitçe anlayalım

**Ana kol:** Şikâyet -> yerel arama -> bulunan kaynaklar -> yerel Gemma -> teknisyenin kontrol listesi -> teknisyenin doğruladığı sonuç -> servis raporu.

**İsteğe bağlı kol:** Seçilmiş fiziksel disk -> smartctl sağlık çıktısı -> JSON doğrulama -> HDD için TabPFN/RF veya NVMe için kurallar -> disk bulguları -> aynı servis raporu.

**RAG ne yapar?** Soruya ilgili bilgi parçalarını bulur ve dil modeline sunar. Modelin bütün belgeleri ezberlemesini beklemeyiz. Belgeler güncellendiğinde bilgi tabanı ve arama indeksi güncellenir; bunun için mutlaka yeniden model eğitmek gerekmez.

**Gemma ne yapar?** Bulunan kaynakları ve kullanıcının verdiği bilgiyi anlaşılır Türkçe sorulara ve önerilere dönüştürür. Donanıma fiziksel erişim sağlamaz. Sonuçları doğrulayan bir ölçüm cihazı değildir.

**Sınıflandırıcı ne yapar?** SMART sayaçları gibi sayısal özelliklerden deneysel bir skor üretir. Soru-cevap belgelerini aramaz. RAG ve sınıflandırma birbirinin yerine yapılmış iki seçenek değil, farklı görevlerdir.

**Kod neyi kontrol eder?** Girdi doğrulama, hangi disk yönteminin çalışacağı, gerçek sayaç değerleri ve raporun ölçüm alanları. Dil modeli sıcaklık, çalışma saati veya model skoru gibi sayıları üretmemelidir. Yine de açıklama metninin sayı uydurmadığı ayrıca kontrol edilmelidir.

**İnsan neyi kontrol eder?** Kaynağın uygunluğu, fiziksel kontrolün uygulanması, gerçek arızanın değerlendirilmesi, müşteriyle iletişim ve onarım kararı. Kaynak metni uygulamaya talimat olarak değil, değerlendirilmesi gereken veri olarak verilir.

## 06 | RAG veri seti nasıl hazırlanır?

Planlanan başlangıç kaynağı Super User soru-cevap vakalarıdır. Kapsam daraltılarak ilgili etiketler ve yeterli açıklama içeren vakalar seçilir. Kabul edilmiş cevap, o vakada yararlı bulunmuş olabilir; her cihaz için doğru veya güncel olduğu anlamına gelmez. Seçilen içerik teknik açıdan gözden geçirilmelidir.

**Bir vaka kaydında ne bulunmalı?** Soru başlığı, belirti, önemli cihaz bağlamı, ilgili cevap, kaynak URL'si, yazar atfı, içerik/revizyon tarihi, lisans bilgisi ve vaka kimliği. HTML ve gereksiz tekrarlar temizlenir. Cihaz modeli ile hata kodu gibi belirleyici bilgiler korunur.

**Parçalara ayırma:** Soru ile cevabın bağlantısı kaybolmamalı. Uzun içerikler anlamlı bölümlere ayrılır; her parça özgün vakaya bağlı kalır. Parça boyutu bir ürün kararıdır; küçük bir sorgu seti üzerinde denenmeden “en iyi boyut” ilan edilmez.

**Arama ve cevap:** Türkçe şikâyet için uygun arama ifadesi hazırlanır; kaynaklar İngilizceyse dil farkı ele alınır. En ilgili birkaç kayıt seçilir. Cevap, kaynak kimliklerine bağlanır. Uygun kaynak yoksa model bunu söylemeli ve gerekli bilgiyi sormalıdır.

**Lisans ayrıntısı:** Tüm eski Super User içeriklerini otomatik CC BY-SA 4.0 saymak doğru değildir. Stack Exchange, katkı/revizyon tarihine göre 2.5, 3.0 veya 4.0 belirtir. Yalnız bağlantı saklamak yeterli kabul edilmemeli; uygun atıf ve lisans bilgisi de tutulmalıdır. [K4]

**Bugünkü durum:** Bu veri seti ve arama indeksi repoda yok. `prompts/` yalnız `.gitkeep` içeriyor. Rehberde önerilen mini-RAG, uygulanmış ürün değil.

## 07 | TF-IDF, FAISS veya GraphRAG: hangisi?

**TF-IDF başlangıcı:** Kelime örtüşmesine göre arar. Küçük, denetlenebilir bir veri setinde kurulumu ve hata incelemesi kolaydır. Eş anlamlı ifadeleri veya Türkçe-İngilizce farkını kaçırabilir. Mevcut Kişi 2 rehberinin önerisi budur.

**Embedding + FAISS adayı:** Metinleri anlamı temsil eden sayısal vektörlere çeviren yerel bir embedding modeli kullanılır. FAISS bu vektörlerde benzerlik araması yapar; cevabı üreten bileşen değildir. Model seçimi, Türkçe başarımı, kaynakları ve indeksi güncelleme maliyeti ayrıca değerlendirilir. FAISS kullanmak zorunlu bir sunucu veritabanı kurmak demek değildir. [K3]

**Hibrit arama adayı:** Hata kodu ve cihaz modeli gibi tam eşleşmeleri kelime aramasıyla, farklı anlatımları vektör aramasıyla yakalamayı hedefler. Ek karmaşıklık ancak ölçülen sonuç iyileşiyorsa değerlidir.

**GraphRAG ne zaman?** Cihaz-parça-belirti-ölçüm ilişkileri düzenli biçimde çıkarılmışsa ve sorular bu ilişkileri birkaç adım boyunca takip etmeyi gerektiriyorsa düşünülebilir. Küçük bir soru-cevap prototipinde grafik oluşturma ve güncel tutma işi, henüz kanıtlanmamış fayda için fazla olabilir.

**Seçim önerisi:** Önce gerçek mini-RAG akışını kur. Aynı 20-30 etiketli sorguda TF-IDF ile yerel embedding adayını karşılaştır. İlk üç sonuçta işe yarar kaynak bulunma oranını, gecikmeyi ve RAM kullanımını ölç. Aynı veride hata kodlarını ve Türkçe eş anlamlıları özellikle dene. Sonuç kazancı yoksa daha karmaşık aramaya geçme.

Bu karşılaştırma henüz yapılmadı; FAISS veya GraphRAG'ın projede kurulu ya da daha başarılı olduğu iddia edilmemelidir.

## 08 | Tam olarak hangi disk okunuyor?

**Uygulama şu anda fiziksel disk seçip taramıyor.** Kullanıcının yüklediği `smartctl` JSON dosyasını veya seçtiği demo JSON'unu okuyor. Dosya hangi fiziksel diskten üretildiyse değerlendirme o diske aittir. Uygulamanın kurulu olduğu diski otomatik olarak değerlendirdiğini varsayamayız.

**Gerçek kayıt:** Bu bilgisayarda daha önce `smartctl --scan` ile görülen `/dev/sda -d nvme` aygıtından `smartctl -j -a -d nvme /dev/sda` çıktısı alınmış. Dışa aktarılan güvenli örnekte model **KINGSTON SNV3S500G**, kapasite yaklaşık **500 GB**. Protokol **NVMe SSD**. `/dev/sda` adı burada HDD olduğu anlamına gelmiyor. [K2]

**C: ve D: konusu:** Bunlar Windows bölüm/sürücü harfleridir; fiziksel disk kimliğiyle aynı şey değildir. Bir fiziksel diskte birden fazla bölüm olabilir. Kaydımız, bu SSD'nin hangi harflerle eşleştiğini doğrulamıyor. “C: diskinin hepsini okuduk” demek yanlış olur.

**Neler okundu?** Model/kapasite, sıcaklık, çalışma saati, ömür kullanımı, kritik uyarı ve hata sayaçları gibi aygıtın verdiği sağlık bilgileri. Fotoğraf, belge, tarayıcı geçmişi veya klasör içerikleri okunmadı. Bütün sektörleri okuyarak yüzey taraması yapılmadı. Veri kurtarma, yazma veya self-test çalıştırılmadı.

**Müşteri cihazında nasıl olur?** Rapor müşteri bilgisayarında alınabilir veya uygun donanımla bağlanan müşteri diskinden üretilebilir. USB kutusu/denetleyici SMART bilgilerini aktarmayabilir; bütün diskler ve bağlantılar desteklenmiş sayılmaz. İleride disk seçici eklenirse model, kapasite ve aygıt kimliği kullanıcıya doğrulatılmalıdır.

**Demolar:** `healthy_hdd.json` ve `failing_hdd.json`, Backblaze gözlemlerinden dönüştürülmüş örneklerdir. `my_nvme.json` gerçek yerel yakalamadır; benzersiz aygıt kimlikleri kaldırılmıştır. [K5]

## 09 | Disk modeli neden var, nasıl hazırlandı?

RAG metinlerden ilgili bilgi getirir. SMART tablosundan deneysel bir arıza sinyali üretmek ise sayısal modelin görevidir. Bu nedenle sınıflandırıcı, soru-cevap veri setinin yerine yapılmış değildir. Disk kolunda Backblaze; RAG kolunda servis vakaları kullanılır.

**Veri hazırlama:** Resmî Backblaze Q2 2026 arşivi yerelde indirildi. Örneklemde 1.164 diskin kayıtlı arızasından tam bir gün önceki gözlemi ve 3.000 kontrol diski var. Her fiziksel diskten tek satır alındı. Kontrol, gözlenen çeyrekte kayıtlı arıza görülmeyen ve yeterli izleme süresi olan disktir; sonsuza kadar sağlıklı disk demek değildir. [K1, K5]

**Sızıntıyı azaltma:** Aynı fiziksel disk hem eğitim bağlamına hem teste konmadı. Eksik değerleri tamamlayan işlem yalnız eğitim bağlamından öğrenildi. İlk örneklemede kontroller tek tarihte yığılmıştı; hata düzeltildi, kontrol tarihleri yedi güne dağıtıldı. Eski rapor silinmedi.

**Girdiler:** Yeniden atanmış, bekleyen ve düzeltilemeyen sektörler gibi SMART sayaçları; sıcaklık ve çalışma süresi. Sayaçlar uygun dönüşümlerle modele verilir. Eksik değerler otomatik olarak sağlıklı anlamına gelen sıfıra çevrilmez.

**Yöntemler:** Yerel CPU üzerinde TabPFN ve karşılaştırma için RandomForest. TabPFN küçük etiketli bağlamla kullanılan bir tablosal modeldir; sıfırdan büyük bir temel model eğitmedik. Çalışma bağlamı 960 disktir. NVMe bu HDD modeline verilmez; ayrı, açık kurallarla değerlendirilir.

**Önemli sınır:** ATA verisinin okunabilmesi, her SATA SSD'de modelin geçerli olduğunu göstermez. Ölçülen deney HDD verisindedir. Model skoru, müşterinin diskinin yarın bozulma olasılığı olarak kalibre edilmemiştir.

## 10 | Sonuçlar ne söylüyor, ne söylemiyor?

Kırmızı eşik 0,60. Bu tablo düzeltilmiş gerçek veri deneylerini özetler. Rastgele disk ayrımında 1.041 test diski (291 pozitif); Haziran takvim kontrolünde 1.124 test diski (267 pozitif) var. [K5, K6]

| Deney | Model | Recall | Precision | ROC-AUC |
|---|---|---|---|---|
| Disk kimliğine göre ayrılmış test | RandomForest | %73,5 | %91,1 | 0,928 |
| Disk kimliğine göre ayrılmış test | TabPFN | %78,7 | %87,7 | 0,927 |
| Haziran takvim kontrolü | RandomForest | %69,3 | %80,4 | 0,875 |
| Haziran takvim kontrolü | TabPFN | %68,9 | %80,7 | 0,879 |

**Recall:** Gerçekte arıza kaydı bulunanların kaçını kırmızı işaretledik? Haziran TabPFN deneyinde 267 diskin 184'ü yakalandı; 83'ü kırmızı olmadı. Düşük skorun güvence olmadığını bu sayı açıkça gösterir.

**Precision:** Kırmızı işaretlenenlerin kaçında arıza kaydı vardı? Haziran deneyinde 228 kırmızı işaretin 184'ü pozitif, 44'ü kontroldü. Bu oran örneklemdeki arızalı disk oranına bağlıdır; dükkânda aynı çıkacağı söylenemez.

**ROC-AUC:** Skorun iki sınıfı sıralama başarısını özetler. 0,879, “disklerin %87,9'unu doğru teşhis ettik” anlamına gelmez. Eşik seçimi ve kullanım maliyeti ayrı değerlendirilir.

**Dürüst yorum:** Zaman ayrımında performans düşüyor. Kontroller çeyreğin sonuçlarıyla geriye dönük seçildiği için bu bir ileriye dönük saha deneyi değil. TabPFN'in RF'den genel olarak üstün olduğu gösterilmedi. RF çok daha hızlı; Haziran testinde sonuçları birbirine yakın. RAG doğruluğu veya müşteri faydası bu disk metriklerinden çıkarılamaz.

## 11 | Güvenilirliği nasıl ele alıyoruz?

Güvenilirlik tek bir başarı yüzdesi değildir. Girdi kalitesi, kaynak uygunluğu, cevabın kaynağa dayanması, ölçümün doğruluğu ve teknisyenin kontrolü birlikte gerekir.

**Disk tarafında uygulanmış önlemler:** Bozuk JSON ve geçersiz sayaçlar reddedilir. Eksik alanlar sağlıklı diye doldurulmaz. Açık SMART başarısızlığı veya okuma hatası yeşil sonuç üretmemelidir. Kısmi NVMe bilgisi belirsizlikle ele alınır. Bunların sınır durumları sentetik testlerle kontrol edilmiştir. [K5]

**RAG tarafında yapılması gerekenler:** Kaynağı olmayan iddiayı kesin teşhis gibi sunmamak; kullanılan kaynak kimliğini cevapla ilişkilendirmek; ilgisiz kaynakta “yeterli kanıt yok” demek; çelişen vakaları göstermek. Veri tabanındaki zararlı metinler uygulama talimatı sayılmamalı. Bu önlemler bu sürümde tamamlanmış değildir.

**Rapor tasarımı:** “Müşterinin söylediği”, “ölçülen bulgu”, “teknisyenin yaptığı kontrol” ve “öneri” ayrı yazılmalı. Sayısal alanlar koddan alınmalı. Dil modeli açıklamayı çarpıtabilir; sadece sayıları kodun yazması bütün raporu otomatik güvenilir yapmaz. Teknisyen onayı gereklidir.

**Güncel arayüzde düzeltilmesi gereken ifade:** Kart bütün skorları “% arıza riski” gösteriyor. Bu bizim kanıtımızdan daha kesin. HDD için “model skoru”, NVMe için “kural tabanlı sağlık skoru” yazılmalı. 0,05 NVMe skoru, %5 arıza ihtimali değildir.

**Mahremiyet:** Yerel hesaplama dış modele müşteri verisi gönderme ihtiyacını azaltır. Ancak günlükler, raporlar ve seri numaraları yine yerelde korunmalıdır. Ham donanım kimlikleri repoya konmadı. Güncel UI internet durumunu kontrol etmek için dış bağlantı deneyebilir; “uygulama hiç ağ bağlantısı kurmaz” denmemeli.

## 12 | Bugün ne hazır, ne hazır değil?

Bu durum `a0944ba` main sürümünün kod ve kayıt denetimine dayanır. “Dosya var” ile “bütün ürün denenmiş” aynı şey değildir.

| Bölüm | Durum | Kanıt / sınır |
|---|---|---|
| Backblaze hazırlama ve HDD modeli | Uygulandı, ölçüldü | Gerçek veri deneyleri; saha doğrulaması yok |
| ATA/NVMe JSON parser ve NVMe kuralları | Uygulandı, test edildi | Cihaz/adapter evrensel uyumluluğu yok |
| Bir yerel NVMe sağlık yakalaması | Kayıt mevcut | Bütün disklerin testi değil |
| Disk/şikâyet sekmeleri, demo seçimi | UI kodu mevcut | Tam son sürüm akışı yeniden doğrulanmadı |
| JSON yükleme, NVMe yönlendirmesi | UI koduna bağlandı | Gerçek mod ve varlıklar gerekli |
| Gerçek RAG ve Super User indeksi | Eksik | Rehber var; veri/indeks/modül yok |
| Gerçek Gemma, triage ve rapor | Eksik | UI modül bazında mock'a düşüyor |
| STT / TTS | Kapsam dışı | İlk prototipe dahil edilmeyecek |
| Tam çevrimdışı UI/Gemma demosu | Doğrulanmadı | Disk modülü deneyiyle karıştırılmamalı |
| Servis kullanıcısı, ödeme isteği | Doğrulanmadı | Gerçek görüşme ve pilot gerekiyor |

**Mock nedir?** Arayüzü geliştirmek için önceden yazılmış örnek cevaptır. Varsayılan `USE_MOCKS=1` tüm modülleri mock yapar. `USE_MOCKS=0` iken mevcut parser/model gerçek olabilir; bulunmayan triage/report/llm/config yine mock olur. Ekranda “Gemma düşünüyor” yazması modelin çalıştığının kanıtı değildir.

**Kişi 1 bitti mi?** Kendi veri/model modülleri ve devri hazır; bütün ürün tamamlanmış değil. 63 sentetik test ve ağ bağlantıları engellenmiş disk deneyleri kaydedildi. Bu dokümantasyon çalışmasında deneyler yeniden koşturulmadı. Gerçek kullanıcı faydası ve tam UI deneyi hâlâ bekliyor.

## 13 | Dizinde neler var, Git'e ne gitti?

**Repo klasörü:** `disk_doktor/disk-doctor/`. Üst klasörde yarışma ve ilk proje planı PDF'leri, `tmp/pdfs/` altında önceki okuma/render ara dosyaları bulunur. Bunlar uygulamanın eğitim verisi değildir.

**Kod ve takip edilen kanıtlar:** `core/` sözleşmeler, mock'lar, parser, HDD modeli ve NVMe kurallarını; `scripts/` veri hazırlama, eğitim ve demo üretimini içerir. `tests/` sınır/pipeline testleri; `demo/` kimlikleri temizlenmiş üç örnek; `docs/metrics*.md` deneyler ve düzeltme geçmişidir. `post/` DEV ve MLH taslaklarını içerir; yayımlandıkları anlamına gelmez.

**Yalnız yerelde, Git dışında:** `data/data_Q2_2026.zip` yaklaşık 2,09 GB ham Backblaze arşivi; örnek CSV ve deney günlükleri; `models/` eğitim bağlamı, test kimlikleri, yerel TabPFN checkpoint'i ve aktarım paketi. `.venv/` yerel çalışma ortamıdır. Ham gerçek NVMe kaydı benzersiz aygıt kimlikleri içerebilir; özel tutulur.

**Aktarım paketi:** `models/person1_demo_bundle.zip` yaklaşık 27 MB. Yerel checkpoint ve bağlamı demo bilgisayarına taşımak içindir. Git klonunda ağırlıklar yoktur. Lisans ve bağımlılıklar kontrol edilip önceden kurulmalıdır; “klonla ve internetsiz hemen çalıştır” beyanı doğru değildir.

**Git durumu:** Kişi 1 kodu `d638d33`, README özeti `88ac214` ile gönderilmişti. PR #1 artık main'e `a0944ba` ile birleştirilmiş. Ekip UI ve yazı taslakları da main'de. Önceki “yalnız feature dalında” bilgisi güncelliğini kaybetti. [K7]

**Yarışma açısından açık konu:** Denetimde repo GitHub'da PRIVATE. Etkinlik PDF'si yerel yarışma için public ve lisanslı repo istiyor. Bu belgeleri hazırlamak repo görünürlüğünü değiştirmez. Eski yazılardaki “kesin erken arıza”, “Gemma hazır” veya ölçülmemiş süre iddiaları teslimden önce güncellenmeli.

## 14 | Kim ne yapacak, sıradaki işler neler?

**Kişi 1 - sen:** Veri/model işini koru; etiket, örnekleme, karşılaştırma ve sınırlılıkların açıklanmasını sahiplen. Parser ve NVMe kurallarını UI'ye bağlarken gerçek sonuçları doğrula. RAG için etiketli değerlendirme sorgularını hazırlamak da katkı sağlayabilir; LLM dosyalarını ekipten habersiz değiştirmek gerekmez.

**Kişi 2:** Gerçek vaka hazırlama, retrieval, yerel LLM bağlantısı, kaynaklı triage ve rapor. Kullanılan model etiketi, ağırlık lisansı ve laptopta ölçülen hız kaydedilmeli. Rehberdeki Gemma 4 adı, indirilmiş ve denenmiş model kanıtı değildir; gerçekten çalışan model yazılmalı.

**Kişi 3:** Mock ile gerçek sonucu açık ayıran arayüz, şikâyet merkezli akış, isteğe bağlı disk ekleme, belirsizlik etiketleri, rapor indirme ve hikâye/teslim. “% arıza riski” etiketini düzeltme ve RAG-only rapor alma burada ele alınır; mevcut UI raporu disk sonucuna bağlıdır.

**Sıralama önerisi:**

1. Dar kapsamlı temiz vaka seti ve gerçek retrieval çalışsın.
2. Yerel model, kaynaklı Türkçe kart üretsin; uygun kaynak yok durumunu işlesin.
3. UI'de disk yüklemeden bir şikâyet -> kaynak -> kontrol -> rapor yolu tamamlansın.
4. Disk kolu aynı servis kaydına isteğe bağlı kanıt olarak eklensin.
5. Onaylanan test senaryoları ve bir kullanıcı deneyi tamamlanınca sunum kaydı alınsın.

**En büyük riskin en ucuz kontrolü:** Ses veya GraphRAG eklemeden, 10 gerçekçi şikâyette kaynakların gerçekten işe yarayıp yaramadığını teknisyene göster. Alakasız kaynak getiriliyorsa önce veri ve aramayı düzelt. Temel akış kabul ölçütlerini sağladıktan sonra yeni kol ekle.

## 15 | Başarıyı nasıl ölçeceğiz?

Aşağıdaki sayılar önerilen başlangıç kabul ölçütleridir; elde edilmiş sonuç değildir. Küçük örneklem ürünün genel doğruluğunu kanıtlamaz.

**RAG değerlendirmesi:** Üç şikâyet ailesinden 20-30 sorgu seç. Hata kodu, Türkçe eş anlamlı ifade, eksik bilgi ve kapsam dışı örnekler olsun. Teknisyen, hangi kaynakların ilgili olduğunu arama sonucunu görmeden işaretlesin. İlk üç sonuçta en az bir ilgili kayıt bulunma oranını raporla. Geliştirme sorguları ile son kontrol sorgularını ayır.

**Başlangıç hedefi:** Son kontrol setinde sorguların en az %80'inde ilk üçte ilgili kaynak. Bu eşik öneridir; veri toplanınca teknik servisin ihtiyacına göre gözden geçirilir. Her önerinin hangi kaynağa veya ölçüme dayandığı izlenebilir olmalı.

**Cevap kalitesi:** Kaynaktan desteklenmeyen iddiaları, yanlış cihaz eşleştirmelerini, uydurma bağlantıları ve önerinin yapılmış işlem diye yazılmasını ayrı say. Kapsam dışı vakalarda “yeterli bilgi yok” davranışını ölç. Bu sınırlı testte kritik zararlı öneri görülmemesi hedeflenir; görülmemesi genel güvenlik kanıtı değildir.

**Kullanıcı faydası:** Aynı zorluktaki görevlerde asistansız ve asistanlı süre, rapora yapılan düzeltme sayısı ve eksik bırakılan sorular kaydedilsin. Görev sırası dengelensin; aynı cevabı ezberleme etkisi azaltılsın. İlk pilot bir kişiyle yapılabilir, fakat bunun pazarı temsil ettiği iddia edilmesin.

**Teknik koşul:** Gerçek modüllerle, tam model etiketi ve laptop özellikleri kayıtlı olarak ağ kapalı prova yap. İlk yükleme ve sonraki istek sürelerini ayrı ölç. <30 saniye kart süresi mevcut plandaki hedeftir; bugünkü Gemma ölçümü değildir. Yeni veri döneminde HDD değerlendirmesi ve dükkân diskleriyle ileriye dönük doğrulama sonraki aşamadır.

## 16 | Yarışmaya nasıl uyuyoruz?

Bu bölüm, kullanıcının sağladığı `hacktoberfest-elazig-kickoff.pdf` içindeki koşulları esas alır; etkinlik organizatörünün canlı sayfasındaki olası değişiklikleri doğrulamaz. Bölüm/sayfa referansları aşağıdadır. [K8]

**Tema: Side Hustle (s.13-16).** Küçük ve spesifik bir müşteri sorununu çözmek gerekiyor. Bizim önerimiz; küçük teknik servisin şikâyet toplama, kaynak arama ve raporlama işi. “Herkese her soruda yardımcı AI” demek kapsamı ve ödeme gerekçesini zayıflatır.

**Açık yaklaşım (s.14,18).** Yerel open-weight model ve açık araçlar; müşteri verisini dış modele göndermeden çalışmayı, kullanım başına bulut API bedeli olmamasını ve model değiştirilebilirliğini hedefler. Toplam maliyet sıfır değildir: donanım, elektrik, kurulum ve bakım vardır. Yerel modelin buluttan daha doğru veya hızlı olduğu ölçülmedi.

**Gerçek kullanıcı (s.19).** Birine kullandır, ne dediğini ve ödeme isteğini yaz. Bizde bu kanıt henüz yok. Uydurma servis adı, müşteri sözü, tasarruf oranı veya fiyat eklenmemeli.

**Yerel yarışma teslimi (s.23-24).** PDF; yeni proje, en fazla dört kişi, public GitHub repo, açık kaynak lisansı, MLH gönderimi ve jüri sunumu istiyor. Repo şu anda private; görünürlük işi açık kalem. MLH gönderiminin yapıldığına dair bu denetimde kanıt yok.

**DEV ödülleri (s.23-25,28).** İngilizce yazı ve submission template isteniyor; PDF'deki son tarih 19 Ekim 2026 Pazartesi 09:59 Türkiye saati. DEV yazısı yerel yarışma için PDF'ye göre opsiyonel, DEV ödülleri için gerekli. Yazı kalitesi en ağır kriter olarak belirtilmiş.

**Kategori iddiaları:** TabPFN için gerçek deney var. Gemma kategorisi için gerçek yerel model entegrasyonu ve demo gerekiyor. Copilot, DevRelay veya başka araçlar yalnız gerçekten kullanıldığı ve kaydı olduğu ölçüde listelenmeli; taslak metin kanıt değildir.

## 17 | Üç dakikalık jüri konuşması

Bu metin hedef ürün yönünü anlatır. Henüz hazır olmayan özellikleri “hedefliyoruz” diye söyle; demo anındaki gerçek durumu son cümlede güncelle.

**0:00-0:35 | Sorun ve kullanıcı**

“Küçük bilgisayar servislerine müşteriler teknik teşhisle değil, ‘yavaşladı’ veya ‘görüntü gelmiyor’ gibi şikâyetlerle geliyor. Teknisyen her seferinde eksik bilgiyi topluyor, kaynak arıyor ve müşteriye durumu açıklıyor. DiskDoctor ile bu tekrar eden işi daha düzenli ve izlenebilir hale getirmeyi hedefliyoruz.”

**0:35-1:15 | Çözüm**

“Ana yaklaşımımız RAG: İlgili servis vakalarını yerel bilgi tabanından bulup yerel dil modeline vermeyi hedefliyoruz. Hedef çıktı; kaynak bağlantıları, sorulacak sorular ve kontrol listesi. Disk şüphesi varsa SMART sağlık raporu ekleniyor. HDD sayısal modelle, NVMe ise açık kurallarla değerlendiriliyor. Son karar teknisyende.”

**1:15-1:55 | Kanıt ve sınır**

“Şu an disk modülleri uygulanmış ve ölçülmüş durumda. Haziran kontrolünde TabPFN, 267 arıza kaydının 184'ünü kırmızı işaretledi; 83'ünü kaçırdı. Bu nedenle skoru kesin arıza yüzdesi veya güvence olarak sunmuyoruz. Veri merkezindeki HDD sonuçlarının dükkân disklerine genellenmesini henüz doğrulamadık.”

**1:55-2:30 | Açık yaklaşım ve gelir**

“Yerel çalışma müşteri bilgisini dış modele gönderme ihtiyacını azaltıyor; bulut API çağrısı başına ödeme gerektirmiyor. Açık kaynak çekirdeğin yanında kurulum, dükkâna özel bilgi tabanı ve destek hizmetini sınamayı düşünüyoruz. Henüz ödeme isteği veya satış doğrulaması yok.”

**2:30-3:00 | Bugünkü durum ve sonraki kanıt**

“Arayüz ve disk değerlendirme kodu var. Bu denetim anında gerçek RAG ve Gemma modülleri eksik; bu bölümler mock. Sonraki adımımız gerçek kaynaklı akışı tamamlayıp bir teknisyenle süreyi ve önerilerin uygunluğunu ölçmek.”

## 18 | Demo nasıl yapılmalı?

**Bugün dürüstçe gösterilebilecek:** Gerçek parser/model modülleriyle üç JSON örneğinin değerlendirilmesi ve ölçüm raporları. Bu oturumda son UI sürümünün uçtan uca çalışması doğrulanmadı; sahne öncesi prova şart. RAG hazır değilken mock kart, gerçek model cevabı gibi sunulmamalı.

**Hedef demo sırası - tamamlandıktan sonra:**

1. Model adı, gerçek/mock durumu ve internet koşulu açık gösterilir.
2. “Fanlar dönüyor, görüntü yok” şikâyeti yazılır. Disk yüklenmeden ilgili kaynaklar ve kontrol adımları gösterilir.
3. Kaynaklardan biri açılır veya yerel saklanan ilgili metin gösterilir. İnternet kapalıysa dış bağlantının açılmaması arama başarısızlığı değildir; kaynak içeriği yerelde olmalıdır.
4. Yavaşlık örneğine geçilir. `failing_hdd.json` seçilir; bunun canlı müşteri diski değil, kayıtlı arızadan bir gün önceki Backblaze gözlemi olduğu söylenir.
5. `my_nvme.json` ile ayrı kuralların çalıştığı gösterilir. Eski kayıt bugün alınmış ölçüm diye sunulmaz.
6. Teknisyenin yaptığı kontroller işaretlenip müşteri raporu indirilir. Bu rapor akışı henüz hedef davranıştır.

**Örnek rapor iskeleti:** “Şikâyet: açılışta donma. Ölçülen: şu SMART alanları. Yapılan kontrol: teknisyenin girdiği sonuç. Değerlendirme: mevcut bulgular depolama sorununu düşündürüyor; kesin teşhis değil. Öneri: teknisyen tarafından onaylanan sonraki işlem.” Sayı ve kaynak uydurulmaz.

**Yedek gösterim:** Ekran kaydı ve ölçüm tabloları hazır bulunsun. Önceden kaydedilmiş video canlı demo diye anlatılmasın. Model ağırlıkları, bağlam dosyası ve paketler önceden hazırlanmalı. Demo başlamadan tüm mock uyarıları ve skor etiketleri kontrol edilmeli.

## 19 | Jüri soruları: ihtiyaç ve iş modeli

**1. Tamirci zaten işini biliyor; buna neden ihtiyaç duysun?** Deneyimli ustanın bilgisinin yerine geçmiyoruz. Tekrar eden bilgi toplama ve rapor hazırlama işini düzenlemeyi, yeni çalışanın ilgili kaynaklara erişimini kolaylaştırmayı hedefliyoruz. Fayda pilotta ölçülecek; gereksiz bulunursa kapsam değişmeli.

**2. Neden Google veya genel bir sohbet aracı yetmiyor?** Bunlar ciddi alternatifler. Bizim fark hedefimiz; dükkânın seçilmiş kaynaklarını yerelde aramak, cihaz ölçümünü aynı kayıtla birleştirmek ve rapor üretmek. Eğer aynı görevde daha az zaman veya daha iyi izlenebilirlik sağlayamazsak farkımız kanıtlanmış olmaz.

**3. Neden mevcut SMART araçlarından farklı?** Onlar zaten sağlık verisini gösterebilir. DiskDoctor'ın hedefi şikâyet, kaynaklı kontrol ve müşteri açıklamasını birleştirmek. SMART okuma tek başına özgünlüğümüz değil; özel HDD skorunun da saha üstünlüğü gösterilmiş değil.

**4. Kim neden para versin?** İlk aday teknik servis sahibi. Kurulum, özelleştirilmiş bilgi tabanı ve desteğe ödeme yapabilir. Bu bir hipotez; ödeme yapan müşteri yok. Ürünün açık kaynak olması bu hizmetleri satmayı engellemez.

**5. Kaç dakika veya ne kadar para kazandırıyor?** Henüz ölçmedik. Asistansız/asistanlı görev süresi ve rapor düzeltme ihtiyacı ölçülecek. Sunumda örnek hesap gerçek sonuç gibi kullanılmayacak.

**6. Neden açık/yerel model?** Müşteri bilgisinin dükkânda kalabilmesi, kurulumdan sonra ağsız çalışma ve model değiştirebilme. Karşılığı bakım ve donanım ihtiyacı. Daha yüksek doğruluk iddiamız yok.

**7. Kapsam çok geniş değil mi?** İlk sürümü üç şikâyet ailesine daraltıyoruz. Ses, otomatik onarım, her cihaz desteği ve kapsamlı servis yönetimi ilk prototipte yok.

## 20 | Jüri soruları: teknik ve güvenilirlik

**8. RAG varken sınıflandırıcı neden var?** RAG metinsel vakaları getirir. Sınıflandırıcı SMART sayaçlarından deneysel sayısal skor üretir. Aynı işi yapmazlar; disk kolu isteğe bağlıdır.

**9. Neden FAISS veya GraphRAG kullanmadınız?** Henüz çalışan retrieval yok. İlk plan TF-IDF; aynı sorgularda yerel embedding adayıyla karşılaştıracağız. FAISS vektör arama aracıdır. Grafik ancak ilişki sorgularında ölçülen fayda sağlarsa eklenecek.

**10. RAG yanlış cevabı engeller mi?** Hayır. Yanlış kaynak bulunabilir veya doğru kaynak yanlış yorumlanabilir. Kaynak gösterimi, kapsam sınırı, kanıt yok cevabı ve teknisyen kontrolü gerekir. Bunların başarısı ayrıca ölçülür.

**11. Skor %99 ise disk yarın kesin bozulur mu?** Hayır. Skor gerçek dünyaya kalibre edilmiş olasılık değil. Örneklem arıza kayıtlarıyla zenginleştirilmiş; müşterinin gerçek arıza oranını temsil etmiyor. UI'daki yüzde etiketi düzeltilmeli.

**12. TabPFN daha mı iyi?** Genel üstünlük göstermedik. Rastgele testte recall daha yüksek; takvim kontrolünde RF ile yakın, RF daha hızlı. Seçim gecikme, kaynak ve gerçek veri performansına göre yapılmalı.

**13. SSD'leri de tahmin ediyor musunuz?** NVMe SSD sağlık günlüğünü kurallarla değerlendiriyoruz. HDD modelinin başarımını SSD'ye taşımıyoruz. NVMe arıza tahmin doğruluğu ölçülmedi.

**14. Hangi diski, hangi dosyaları okuyorsunuz?** Yüklenen SMART JSON'un ait olduğu aygıtı değerlendiriyoruz. Gerçek yerel örnek Kingston NVMe SSD'den. Kullanıcı belgeleri ve klasör içerikleri okunmuyor; tüm sektör taraması yapılmıyor.

**15. 63 test geçti; güvenilirliği kanıtladınız mı?** Parser ve pipeline sınır durumlarında kanıt sağlar. Gerçek arıza tahmin başarısı, RAG kalitesi ve kullanıcı faydası için ayrı değerlendirme gerekir. Ağ engelli disk deneyi, bütün UI/Gemma'nın çevrimdışı çalıştığını kanıtlamaz.

## 21 | İyileştirme, ses ve teslim öncesi açık işler

**Önce çekirdek:** Gerçek RAG ve yerel model; kaynakla ilişkilendirilmiş cevap; disk yüklemeden rapor; gerçek/mock ayrımı; doğru skor etiketleri. Bunlar yeni bir ses kolundan önce gelir.

**Sonraki faydalı aday:** Teknisyenin onayladığı çözümü vakaya bağlayan yerel servis hafızası. Daha sonra gelen benzer vakalar dükkânın kendi bilgisinden yararlanabilir. Hatalı veya doğrulanmamış onarım notları otomatik doğru kabul edilmemelidir. İzin, kişisel veri temizliği ve saklama süresi tasarlanır.

**Disk geçmişi:** Aynı cihazın zaman içindeki sayaçlarını karşılaştırmak, tek anlık ölçümden daha fazla bağlam sağlayabilir. Bunun arıza tahminini iyileştirdiği henüz gösterilmedi; yeni bir deney gerekir.

**Ses terimleri:** STT (speech-to-text), konuşmayı yazıya çevirir. TTS (text-to-speech), cevabı seslendirir. “Ses-to-text” ile “speech-to-text” aynı yöndür. Kullanıcının kararı gereği ikisi de ilk prototip dışında. İleride önce STT denenebilir; elleri dolu teknisyende not girişini kolaylaştırıp kolaylaştırmadığı test edilir. TTS ancak erişilebilirlik veya eller serbest kullanım ihtiyacı doğrulanırsa eklenir.

**Teslim öncesi açık liste:** Gerçek RAG/Gemma; temiz ve lisanslı kaynaklar; model etiketi/lisansı; UI metinleri; tam çevrimdışı prova; gerçek kullanıcı geri bildirimi; README/DEV/MLH iddialarını güncelleme; public repo kararını uygulama; takım bilgileri; gerçek demo kaydı; gönderim teyidi. Bu rapor bunları yapılmış saymaz.

**Vaat sınırı:** “Veri kaybını önlüyoruz”, “her diskte çalışır”, “%X kesin arıza olasılığı”, “müşteriler para ödemeye hazır”, “Gemma/RAG tamam” cümleleri mevcut kanıtla savunulamaz. Savunulabilir anlatım; ölçülen modülleri, hedef iş akışını ve sıradaki doğrulamayı birlikte göstermektir.

## 22 | Kaynaklar ve kısa sözlük

Kaynak türleri: K1-K4 dış birincil teknik kaynak; K5-K7 proje kanıtı; K8-K9 kullanıcı tarafından sağlanan plan/etkinlik belgeleri. Plan belgesi ürünün çalıştığını kanıtlamaz. Teknik kaynaklar 17 Ekim 2026'da kontrol edildi.

- **K1 - Backblaze veri kaynağı:** https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data ; yerel deney Q2 2026 arşivini kullanır.
- **K2 - smartctl 7.5 resmî kullanım kaynağı:** https://raw.githubusercontent.com/smartmontools/smartmontools/RELEASE_7_5/smartmontools/smartctl.8.in ; aygıt seçimi, protokoller ve sağlık çıktısı.
- **K3 - FAISS resmî wiki:** https://github.com/facebookresearch/faiss/wiki ; vektör benzerlik araması.
- **K4 - Stack Exchange içerik lisansları:** https://stackoverflow.com/help/licensing ; katkı/revizyon tarihine göre lisans sürümleri.
- **K5 - Proje disk deneyleri:** `docs/metrics.md`, `docs/metrics_initial.md`, `tests/test_person1_pipeline.py`, `demo/my_nvme.json`.
- **K6 - Takvim kontrolü:** `docs/metrics_temporal.md`; n=1.124, pozitif=267; güven aralıkları ve karışıklık matrisleri burada.
- **K7 - GitHub kaynak ve PR:** https://github.com/hacktob3v-devs/disk-doctor ; https://github.com/hacktob3v-devs/disk-doctor/pull/1 ; denetim tabanı `a0944ba`.
- **K8 - Etkinlik:** Üst klasörde `hacktoberfest-elazig-kickoff.pdf`, 29 sayfa. Tema s.13-19; kategori s.20-22; kurallar/teslim s.23-24; değerlendirme s.25,28.
- **K9 - İlk plan:** Üst klasörde `DiskDoctor_Kazanma_Plani.pdf`; `docs/rehber/00_ortak.md` ve üç kişi rehberi. İş bölümü ve ilk teknik tercihler; mevcut uygulama kanıtı değildir.

**RAG:** Cevap üretmeden önce ilgili kaynakları bulup modele verme yaklaşımı. **Embedding:** Metni benzerlik araması için vektörle temsil etme. **Mock:** Önceden yazılmış örnek çıktı. **SMART:** Aygıtın sunduğu sağlık/çalışma sayaçları. **HDD:** Mekanik sabit disk. **NVMe SSD:** NVMe protokolüyle erişilen katı hâl depolama aygıtı. **Holdout:** Geliştirme/eğitim bağlamından ayrılan test grubu. **Kalibrasyon:** Skorlarla gerçek olay sıklığının uyumunu değerlendirme; burada saha için yapılmadı.
