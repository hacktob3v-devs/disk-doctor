# DiskDoctor - Proje durumu

Son denetim: 17 Ekim 2026. Kod tabanı: origin/main `a0944ba`.

## Ürün yönü ve kapsam

- Önerilen yön: küçük bilgisayar servisleri için şikâyet -> kaynaklı RAG yardımı -> kontrol sonuçları -> müşteri raporu. Disk sağlığı isteğe bağlı ek kanıt. Bu yönün uygulaması henüz tamamlanmadı.
- STT ve TTS ilk prototipe dahil edilmeyecek (kullanıcının açık kararı).
- Ayrıntılı gerekçe, örnekler, jüri soruları ve PDF kaynağı: [PROJE_REHBERI.md](PROJE_REHBERI.md).

## Uygulandı / ölçüldü

- Kişi 1: Backblaze veri hazırlama; ATA/NVMe JSON parser; yerel CPU TabPFN ve RF; NVMe kuralları; üç demo; 63 sentetik testin kayıtlı başarılı çalışması.
- Q2 2026 örneklemi: 1.164 pozitif + 3.000 kontrol. Düzeltilmiş disk ayrımı TabPFN AUC 0,927; Haziran takvim kontrolü 0,879. Ayrıntı ve sınırlılıklar: [metrics.md](metrics.md), [metrics_temporal.md](metrics_temporal.md). Bunlar gerçek dünyaya kalibre olasılık veya servis doğrulaması değil.
- Gerçek NVMe yakalaması: KINGSTON SNV3S500G, yaklaşık 500 GB; smartctl aygıtı `/dev/sda -d nvme`. C:/D: eşlemesi doğrulanmadı. Sağlık sayaçları okundu; dosya içerikleri, yüzey taraması, yazma veya self-test yok. Demo kimlikleri temizlendi.
- Ekip main'e arayüz, demo seçimi, modül bazlı mock fallback, NVMe yönlendirmesi ve HTML rapor indirme kodu eklemiş. Son UI sürümünün uçtan uca çalışması bu denetimde denenmedi.

## Eksik / yanlış anlaşılma riski

- `core/config.py`, `llm.py`, `retrieval.py`, `triage.py`, `report.py` ve gerçek Super User veri seti yok. `prompts/` boş yer tutucu. UI bu modüllerde mock kullanıyor; varsayılan `USE_MOCKS=1` bütün akışı mock yapıyor.
- UI'daki `% arıza riski` etiketi kanıtla uyumsuz: HDD için model skoru, NVMe için kural tabanlı sağlık skoru yazılmalı. Bu dokümantasyon işi UI kodunu değiştirmedi.
- UI ağ durumunu `1.1.1.1:53` bağlantı denemesiyle kontrol ediyor; hiç dış bağlantı kurmadığı söylenemez. Disk modülleri ağ engelli deneyde çalıştı; tam UI/Gemma çevrimdışı doğrulanmadı.
- Gerçek kullanıcı, ödeme isteği, RAG başarımı ve Gemma gecikmesi ölçülmedi. Mevcut post taslakları tamamlanmış özellik iddiası gibi yayımlanmamalı.

## Yerel varlıklar / Git

- Üst klasör: iki kaynak PDF ve `tmp/pdfs/` okuma ara dosyaları. Repo alt klasör `disk-doctor/`.
- Git dışında: `data/data_Q2_2026.zip` (~2,09 GB), CSV örneklemi, ham özel NVMe yakalaması, deney günlükleri; `models/` checkpoint/bağlam/test çıktıları; `models/person1_demo_bundle.zip` (~27 MB); `.venv/`.
- Git içinde: kod, temizlenmiş demolar, ölçüm raporları, rehberler, post taslakları. Seri numaraları ve ham veri eklenmeyecek.
- Kişi 1 commit'leri `d638d33`, `88ac214`; PR #1 MERGED, main `a0944ba`. Bu bilgi GitHub'dan doğrulandı. Yeni rehber/PDF ayrı `docs/rag-jury-guide` dalında hazırlanıyor; yayın durumu son Git kontrolünden okunmalı.
- Denetimde repo PRIVATE. Yarışma PDF'si public/lisanslı repo ve MLH teslimi istiyor. Görünürlük değiştirilmedi; gönderim yapıldığı doğrulanmadı.

## Sıradaki kabul noktaları

1. Kişi 2: gerçek vaka seti/atıflar, retrieval, yerel model, kaynaklı triage/rapor.
2. Kişi 3: şikâyet merkezli diskten bağımsız rapor akışı, doğru etiketler ve açık mock durumu.
3. Kişi 1: gerçek disk modülünün UI entegrasyon kontrolü ve değerlendirme verilerinin devri.
4. Ekip: etiketli RAG sorguları, son UI ile ağ kapalı prova, gerçek kullanıcı pilotu; sonra sunum ve teslim iddialarını güncelle.
