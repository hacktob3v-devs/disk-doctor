# Proje çalışma notları

- Türkçe iletişim kur; teknik identifier'ları koru.
- Güncel durum ve yerel varlıklar için önce [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) oku. Ayrıntılı ürün açıklaması ve jüri hazırlığı [docs/PROJE_REHBERI.md](docs/PROJE_REHBERI.md) içindedir. Durum ayrıntılarını bu dosyaya çoğaltma.
- RAG ana akış, disk değerlendirmesi isteğe bağlı kanıt kolu olarak öneriliyor. Önerilen hedefi çalışan özellik diye sunma. STT ve TTS ilk prototip dışında.
- Çalışan, mock, planlanan ve doğrulanmamış özellikleri ayrı belirt. Yeni sonuç için deney kaydı olmadan başarı, hız, müşteri veya ödeme iddiası ekleme.
- HDD çıktısı kalibre edilmiş arıza olasılığı değil; NVMe çıktısı kural tabanlı sağlık skoru. SMART erişimini dosya/klasör okuma ya da her cihazda model doğrulamasıyla karıştırma.
- `data/`, `models/`, ham aygıt kimlikleri ve müşteri bilgilerini Git'e ekleme. Kod lisansı ile model/veri lisanslarını ayrı değerlendir.
- Ekip dosya sahipliği için `docs/rehber/00_ortak.md` kullan; ortak sözleşme değişikliklerini koordine et. Belge güncellemesi, başka kişinin ürün akışını sessizce değiştirme yetkisi değildir.
