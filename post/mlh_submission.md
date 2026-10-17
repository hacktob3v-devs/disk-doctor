# MLH gönderimi — kopyala/yapıştır metinleri

**İlk gönderim: 01:30 (CP2) · Güncelleme: 05:15**

## Proje adı
DiskDoctor

## Kısa açıklama (tagline)
An offline assistant that tells a neighborhood repair shop which hard drive is about to die.

## Açıklama
DiskDoctor helps a neighborhood computer repair shop triage customer complaints and spot hard drives that are about to fail, before the customer loses their data. It runs fully offline on the shop's own laptop: Gemma 4 via Ollama turns the customer's complaint into a triage card and writes a plain-language report for the customer, and TabPFN trained on Backblaze drive-failure data scores the failure risk from a `smartctl` report (NVMe drives use a transparent rule set). No closed APIs, zero per-customer cost, and no customer data leaves the shop.

## Kullanılan teknolojiler
Gemma 4, Ollama, TabPFN, scikit-learn, Streamlit, smartmontools, Backblaze Drive Stats, Stack Exchange Data Explorer, GitHub Copilot

## Linkler
- Repo: https://github.com/hacktob3v-devs/disk-doctor
- DEV yazısı (05:15'te taslak linki, Pazar yayın linki): [ ]
- Demo videosu: [ ]

## Kontrol
- [ ] Takım arkadaşlarının üçü de eklendi
- [ ] Repo public, MIT lisansı görünüyor
- [ ] 05:15'te GIF / video ve yazı linki eklendi
