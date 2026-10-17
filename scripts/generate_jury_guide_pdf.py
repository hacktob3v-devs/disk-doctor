"""
Generate Professional Turkish Jury Defense Guide PDF for EsnafDoktor.
Hacktoberfest Elazig 2026 - Week 2 "Side Hustle"
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PDF = ROOT_DIR / "docs" / "EsnafDoktor_Juri_Savunma_Rehberi.pdf"
WORKSPACE_PDF = ROOT_DIR.parent / "EsnafDoktor_Juri_Savunma_Rehberi.pdf"

# Palette
PRIMARY = colors.HexColor("#0f172a")       # Slate 900
NAVY = colors.HexColor("#1e3a8a")          # Deep Blue 900
ACCENT = colors.HexColor("#c2410c")        # Terracotta Orange
SUCCESS = colors.HexColor("#15803d")       # Emerald 700
WARNING = colors.HexColor("#b45309")       # Amber 700
MUTED = colors.HexColor("#475569")         # Slate 600
BG_LIGHT = colors.HexColor("#f8fafc")      # Slate 50
BG_CARD = colors.HexColor("#ffffff")       # White
BORDER_LIGHT = colors.HexColor("#e2e8f0")  # Slate 200
TAG_BG = colors.HexColor("#eff6ff")        # Blue 50
TAG_TEXT = colors.HexColor("#1d4ed8")      # Blue 700

WIDTH, HEIGHT = A4
MARGIN = 36


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("ArialTR", 8)
        self.setFillColor(MUTED)
        
        # Header rule
        self.setStrokeColor(BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(MARGIN, HEIGHT - 24, WIDTH - MARGIN, HEIGHT - 24)
        self.drawString(MARGIN, HEIGHT - 20, "EsnafDoktor — Fırat Üniversitesi Jüri Savunma ve Soru-Cevap Rehberi")
        self.drawRightString(WIDTH - MARGIN, HEIGHT - 20, "Hacktoberfest Elazığ 2026")

        # Footer rule
        self.line(MARGIN, 28, WIDTH - MARGIN, 28)
        self.drawString(MARGIN, 18, "Gizli / Yarışmacı Hazırlık Dokümanı · %100 Açık Ağırlıklı Mimari (Gemma 4 + TabPFN)")
        self.drawRightString(WIDTH - MARGIN, 18, f"Sayfa {self._pageNumber} / {page_count}")
        self.restoreState()


def setup_fonts():
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font_bd_path = Path("C:/Windows/Fonts/arialbd.ttf")
    font_it_path = Path("C:/Windows/Fonts/ariali.ttf")

    if font_path.exists() and font_bd_path.exists():
        pdfmetrics.registerFont(TTFont("ArialTR", str(font_path)))
        pdfmetrics.registerFont(TTFont("ArialTR-Bold", str(font_bd_path)))
        pdfmetrics.registerFont(TTFont("ArialTR-Italic", str(font_it_path)))
        pdfmetrics.registerFontFamily("ArialTR", normal="ArialTR", bold="ArialTR-Bold", italic="ArialTR-Italic")
        return "ArialTR"
    return "Helvetica"


def make_question_card(
    q_num: int,
    judge_name: str,
    criterion: str,
    question_text: str,
    what_judge_measures: str,
    full_score_answer: str,
    golden_punchline: str,
    fn: str,
    fn_bold: str
) -> Table:
    """Build a beautiful, high-contrast Q&A card for a jury question."""
    
    header_p = Paragraph(
        f"<b>SORU {q_num}: {question_text}</b>",
        ParagraphStyle("CardQ", fontName=fn_bold, fontSize=10.5, leading=14, textColor=PRIMARY)
    )
    
    meta_p = Paragraph(
        f"<b>Hedef Jüri:</b> {judge_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Ölçülen Kriter:</b> <font color='#c2410c'><b>{criterion}</b></font>",
        ParagraphStyle("CardMeta", fontName=fn, fontSize=8.5, leading=11, textColor=MUTED)
    )
    
    intent_p = Paragraph(
        f"<b>🎯 Jüri Neyi Ölçüyor?</b> {what_judge_measures}",
        ParagraphStyle("CardIntent", fontName=fn, fontSize=8.5, leading=12, textColor=NAVY)
    )
    
    ans_p = Paragraph(
        f"<b>💡 100/100 Tam Puanlık Cevap:</b><br/>{full_score_answer}",
        ParagraphStyle("CardAns", fontName=fn, fontSize=9, leading=13, textColor=PRIMARY)
    )
    
    punch_p = Paragraph(
        f"<b>⭐ Vurgulanacak Altın Cümle:</b> \"{golden_punchline}\"",
        ParagraphStyle("CardPunch", fontName=fn_bold, fontSize=8.5, leading=12, textColor=SUCCESS)
    )
    
    content = [
        [header_p],
        [meta_p],
        [intent_p],
        [ans_p],
        [punch_p]
    ]
    
    card_table = Table(content, colWidths=[WIDTH - (MARGIN * 2)])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_LIGHT),
        ('LINEBEFORE', (0, 0), (0, -1), 3.5, NAVY if q_num % 2 == 1 else ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return card_table


def build_pdf():
    fn = setup_fonts()
    fn_bold = f"{fn}-Bold" if fn == "ArialTR" else "Helvetica-Bold"
    fn_it = f"{fn}-Italic" if fn == "ArialTR" else "Helvetica-Oblique"

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        fontName=fn_bold,
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        fontName=fn_bold,
        fontSize=9.5,
        leading=13,
        textColor=ACCENT,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=fn,
        fontSize=8.5,
        leading=12,
        textColor=PRIMARY
    )
    section_h1 = ParagraphStyle(
        "SecH1",
        fontName=fn_bold,
        fontSize=12,
        leading=16,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=4
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("🏆 EsnafDoktor — Fırat Üniversitesi Jüri Savunma Rehberi", title_style))
    story.append(Paragraph("HACKTOBERFEST ELAZIĞ 2026 · WEEK 2 \"SIDE HUSTLE\" · 100/100 TAM PUANLIK SAVUNMA REHBERİ", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8, spaceBefore=0))

    # Rubric & Juri Info Table
    info_data = [
        [
            Paragraph("<b>Resmî Jüri Heyeti (Fırat Üniversitesi):</b><br/>"
                      "• Arş. Gör. Mehmet Arzu (NLP & Model Mimarisi)<br/>"
                      "• Öğr. Gör. Semih Yücel (Sistem & Güvenlik)<br/>"
                      "• Arş. Gör. Diyar Güzelses (Veri Bilimi & Metrikler)<br/>"
                      "• Arş. Gör. Muhammed Veysi Güler (İş Modeli)<br/>"
                      "• Arş. Gör. Mert İncidelen (Açık Kaynak & Sponsorlar)", body_style),
            Paragraph("<b>Puanlama Ağırlıkları (Sayfa 28):</b><br/>"
                      "• <b>Yazı / Rapor Kalitesi:</b> En ağır kriter (Akademik PDF)<br/>"
                      "• <b>Temaya Uygunluk:</b> KOBİ/E-Ticaret Side Hustle<br/>"
                      "• <b>Teknik Uygulama:</b> 4 Katmanlı Hibrit Mimari<br/>"
                      "• <b>Partner Teknolojisi:</b> Gemma 4 + TabPFN ($400 Hedef)<br/>"
                      "• <b>Yaratıcılık:</b> İki Yönlü Sesli Asistan (STT/TTS)", body_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[(WIDTH - (MARGIN * 2)) * 0.52, (WIDTH - (MARGIN * 2)) * 0.48])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("🎯 EN KRİTİK 7 JÜRİ SORUSU VE 100/100 TAM PUANLIK CEVAPLAR", section_h1))

    # Question 1: Architecture Division of Labor
    story.append(make_question_card(
        q_num=1,
        judge_name="Arş. Gör. Mehmet Arzu",
        criterion="Teknik Uygulama (%25)",
        question_text="Sistemde BERTürk, RAG, TabPFN ve Gemma 4 var. Neden tek bir LLM ile çözmediniz?",
        what_judge_measures="Adayın mikro-model prensibini bilip bilmediği, LLM'i her işe körü körüne alet edip etmediği.",
        full_score_answer="Tek bir LLM her işe yetmez ve gecikmeyi artırır. Biz görevleri uzmanlarına dağıttık: "
                          "<b>1) BERTürk</b> 15 ms'de intent ve kategori çıkarır. "
                          "<b>2) 2026 Hibrit RAG (BM25+E5+RRF)</b> mağazanın 16 hukuki kuralını getirir. "
                          "<b>3) TabPFN</b> sayısal sipariş parametrelerinden 18 ms'de risk dağılımı hesaplar. "
                          "<b>4) Gemma 4</b> ise tüm bu kanıtları birleştirip aksiyon kartı ve WhatsApp yanıtı üreten Akıl Yürütme Motorudur. "
                          "Böylece sistem CPU üzerinde &lt;1.8 saniyede ve 0 TL değişken maliyetle çalışır.",
        golden_punchline="LLM metin akıl yürütmesi için merkezdedir; ancak deterministik kuralları RAG, tabüler riski TabPFN çözer.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 2: Data Leakage & Metrics
    story.append(make_question_card(
        q_num=2,
        judge_name="Arş. Gör. Diyar Güzelses",
        criterion="Veri Bilimi ve Doğrulama (%20)",
        question_text="Veri setiniz sentetik mi, gerçek mi? Neden F1 skorunuz %100 değil?",
        what_judge_measures="Veri sızıntısı (leakage) olup olmadığı ve adayın dürüst akademik olgunluğu.",
        full_score_answer="Hocam, yapay %100 skor sentetik ezber ve veri sızıntısı işaretidir. Biz 3 katmanlı dürüst veri kurduk: "
                          "BERTürk modelimiz 18.000+ gerçek Türkçe şikayet verisiyle eğitilmiştir. "
                          "Sentetik motorumuzda şablon kopyalamayı çöpe attık; 8 farklı tüketici davranışı ve mobil klavye yazım hataları (typo) "
                          "içeren 3.000 satırlık veri ürettik. "
                          "Modeli ise daha önce hiç görmediği 20 zorlu sınır vakası (Held-Out Gold) üzerinde test ettik. "
                          "Aldığımız %73.2 kategori ve %88.0 niyet F1 skorları, gerçek dünya gürültüsüne karşı alınmış sızıntısız skorlardır.",
        golden_punchline="Yarışmada %100 skor getiren sistem ezber yapmıştır; bizim %73-%88 aralığımız sızıntısız validasyonun kanıtıdır.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 3: TabPFN & Real Data
    story.append(make_question_card(
        q_num=3,
        judge_name="Arş. Gör. Mert İncidelen",
        criterion="Partner Teknolojisi ($200 Kategori)",
        question_text="TabPFN bir dil modeli değil, e-ticarette ne işi var? Hangi verilere dayanıyor?",
        what_judge_measures="TabPFN kullanımının zorlama mı yoksa gerçek bir mühendislik ihtiyacı mı olduğu.",
        full_score_answer="Şartnamede (Sayfa 20) doğrudan 200$ ödüllü <b>Best Use of TabPFN</b> kategorisi var. "
                          "Teknik gerekçemiz şudur: Müşteri metninin arkasında 5 doğrulanmış tablo verisi vardır: "
                          "<b>1) Tutar (TL)</b> (100 TL kupa vs 5.800 TL mont), "
                          "<b>2) Teslimat günü</b> (taze kargo hasarı mı, 14. gün mü?), "
                          "<b>3) Müşteri geçmiş iade oranı</b> (%0 mı, %80 suistimalci mi?), "
                          "<b>4) Açılış videosu</b> ve <b>5) Kargo hasar tutanağı</b> varlığı. "
                          "LLM bu tablodan güvenilir olasılık çıkaramaz, sayı uydurur. "
                          "TabPFN CPU'da 18 ms'de riski hesaplar; risk yüksekse Gemma sahte iadeyi onaylamaz, inceleme adımlarını devreye sokar.",
        golden_punchline="TabPFN metin botunu işletme koruyucusuna dönüştürür; esnafı sahte iade dolandırıcılığından kurtaran parça budur.",
        fn=fn, fn_bold=fn_bold
    ))

    story.append(PageBreak())

    # Question 4: Offline & Privacy
    story.append(make_question_card(
        q_num=4,
        judge_name="Öğr. Gör. Semih Yücel",
        criterion="Yazılım Mimarisi & Güvenlik (%20)",
        question_text="Wi-Fi'ı kopardığımızda bu sistem gerçekten çalışır mı? Dışarıya gizli API çağrısı var mı?",
        what_judge_measures="Sistemin gerçekten yerel (open-weight) çalışıp çalışmadığı ve KVKK/Gizlilik uyumu.",
        full_score_answer="Kesinlikle evet. Şu anda laptopun Wi-Fi bağlantısını jüri önünde tamamen kapatabiliriz. "
                          "BERTürk, TabPFN, E5 embedding ve Gemma 4 yerel donanımda çalışır. "
                          "Dışarıya tek bir HTTP/API çağrısı gitmez. "
                          "Bu sayede iki dev avantaj sağlanır: "
                          "<b>1) 0.00 TL API Maliyeti:</b> Günde 200 mesaj alan küçük işletme ayda ~15.000 TL OpenAI token faturası ödeyemez. "
                          "<b>2) KVKK / Gizlilik:</b> Alıcının adresi, telefonu ve sepet tutarı yabancı bulutlara gitmez, cihazda kalır.",
        golden_punchline="Dükkanda internet kesilse bile sistem kesintisiz karar verir; müşteri verisi asla bilgisayardan dışarı çıkmaz.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 5: Hallucination & Self-RAG
    story.append(make_question_card(
        q_num=5,
        judge_name="Arş. Gör. Mehmet Arzu",
        criterion="RAG Mimarisi & Güvenilirlik (%20)",
        question_text="Gemma politikada olmayan bir kural uydurursa esnaf batar. Halüsinasyonu nasıl önlediniz?",
        what_judge_measures="RAG boru hattının güvenliği ve Self-RAG / Grounding denetimi.",
        full_score_answer="Geçen yılın düz kosinüs RAG'lerini terk ettik; <b>2026 İki Aşamalı Hibrit RAG</b> kurduk: "
                          "BM25 anahtar kelime ile Multilingual-E5 vektör araması paralel çalışır, RRF (k=60) ile birleştirilir ve Cross-Encoder ile yeniden sıralanır. "
                          "En önemlisi: <b>Self-RAG Grounding Guard</b> devrededir. Gemma'nın çıktısı sistemdeki 16 doğrulanmış mağaza politikasıyla "
                          "birebir eşleştirilir. Dayanağı olmayan hiçbir kural (örn. 14 gün yerine 30 gün) üretilemez. "
                          "Ayrıca nihai WhatsApp gönderim onayı her zaman satıcıdadır.",
        golden_punchline="Sistem kural uyduramaz; her önerinin altında 'Dayanak Kural Kodu' zorunlu TypedDict kontratı olarak üretilir.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 6: Side Hustle & Business Value
    story.append(make_question_card(
        q_num=6,
        judge_name="Arş. Gör. Muhammed Veysi Güler",
        criterion="Temaya Uygunluk (Side Hustle - %25)",
        question_text="Bu proje 'Side Hustle' temasına nasıl oturuyor? Satıcı buna neden para ödesin?",
        what_judge_measures="Projenin teorik bir ödev mi yoksa gerçek dünyada para kazandıran/kurtaran bir ürün mü olduğu.",
        full_score_answer="Side Hustle yapan butik ve e-ticaret satıcılarının en büyük kanayan yarası uyuşmazlıklardır. "
                          "Haksız kabul edilen tek bir sahte mont/telefon iadesi 5.800 TL doğrudan zarar yazar. "
                          "Kargo hasarında tutanak tutturulmadığı için tazminat kargo şirketinden alınamaz, satıcının cebinden çıkar. "
                          "Geç cevap vermek ise pazar yeri mağaza puanını düşürür. "
                          "EsnafDoktor ayda sadece 2 sahte iadeyi ve 3 kargo tazminatını kurtardığında satıcıya en az 10.000 TL net nakit koruma sağlar. "
                          "Satıcı tek seferlik 1.500 TL veya aylık 250 TL bakım ücretini tereddüt etmeden öder.",
        golden_punchline="EsnafDoktor esnafa harcama yaptırmaz; haksız iadeleri ve kargo hasarlarını önleyerek doğrudan net kârını kurtarır.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 7: Voice Assistant & User Experience
    story.append(make_question_card(
        q_num=7,
        judge_name="Arş. Gör. Mert İncidelen",
        criterion="Yaratıcılık & UX (%15)",
        question_text="Paketleme yapan satıcı klavye kullanamaz. Kullanıcı deneyimini nasıl çözdünüz?",
        what_judge_measures="Uygulamanın masa başında değil sahada nasıl kullanılacağının düşünülüp düşünülmediği.",
        full_score_answer="İki yönlü tam Sesli Asistan entegre ettik: "
                          "<b>1) STT (Mikrofon):</b> Satıcı elinde koli bandı varken mikrofona tıklar ve müşterinin ses kaydını veya problemini söyler. "
                          "Web Speech API bunu anında Türkçeye çevirir ve sistemi tetikler. "
                          "<b>2) TTS (Sesli Yanıt):</b> Otomatik Seslendirme açık olduğunda asistan kararı ve aksiyonu satıcıya sesli olarak okur. "
                          "Tek tıkla müşteriye WhatsApp yanıtı hazır linkle açılır ve A4 resmi servis tutanağı PDF olarak indirilir.",
        golden_punchline="Satıcı elini klavyeye sürmeden mikrofona konuşur; asistan inceler, riskini tartar ve kararı kulağına fısıldar.",
        fn=fn, fn_bold=fn_bold
    ))

    story.append(PageBreak())

    # 3. 3-Minute Live Pitch Sequence & Cheat Sheet
    story.append(Paragraph("⏱️ 3 DAKİKALIK JÜRİ SUNUM PLANI (CANLI PİTCH KRONOMETRESİ)", section_h1))
    
    pitch_data = [
        [
            Paragraph("<b>Zaman</b>", ParagraphStyle("TH1", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY)),
            Paragraph("<b>Sunucu Ne Anlatıyor?</b>", ParagraphStyle("TH2", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY)),
            Paragraph("<b>Ekranda Ne Gösteriliyor? (Aksiyon)</b>", ParagraphStyle("TH3", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY)),
            Paragraph("<b>Hedeflenen Puan</b>", ParagraphStyle("TH4", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY))
        ],
        [
            Paragraph("<b>0:00 - 0:40</b><br/>(Giriş)", body_style),
            Paragraph("E-ticaret butik satıcılarının her akşam yaşadığı iade ve uyuşmazlık krizini anlatın. "
                      "Geciken yanıtların puan düşürdüğünü, sahte iadelerin kârı yok ettiğini belirtin. "
                      "EsnafDoktor'un 0 TL maliyetle yerel çalıştığını söyleyin.", body_style),
            Paragraph("Arayüzün üst bandını gösterin: <b>0.00 TL Değişken Maliyet</b> rozeti ve <b>Wi-Fi Kapalı</b> durumu.", body_style),
            Paragraph("Temaya Uygunluk<br/><b>10/10</b>", body_style)
        ],
        [
            Paragraph("<b>0:40 - 1:40</b><br/>(Canlı Demo)", body_style),
            Paragraph("Üstteki 4 canlı senaryodan <b>'2. Şüpheli İade (5.800 TL Mont)'</b> senaryosuna tıklayın. "
                      "Ardından mikrofona basıp Türkçe sesle komut verin. "
                      "TabPFN'in 18 ms'de Kırmızı Risk çıkardığını ve Gemma'nın hemen iade yerine inceleme adımı önerdiğini gösterin. "
                      "Sesli Asistanın kararı okumasını dinletin.", body_style),
            Paragraph("1. Butona tıkla.<br/>2. 🎙️ Mikrofona konuş.<br/>3. TabPFN Kırmızı Riski göster.<br/>4. 🔊 Kararı seslendir.", body_style),
            Paragraph("Teknik + UX<br/><b>10/10</b>", body_style)
        ],
        [
            Paragraph("<b>1:40 - 2:20</b><br/>(Bilimsel Kanıt)", body_style),
            Paragraph("Sayfanın altındaki <b>'Jüri İçin Bilimsel Kanıtlar & Slayt 18'</b> sekmesini açın. "
                      "Neden açık kaynak (0 TL, KVKK, Çevrimdışı)? "
                      "Held-Out Gold test setinde %73-%88 dürüst F1 skorlarını gösterip veri sızıntısı olmadığını vurgulayın. "
                      "PDF Raporu gösterin.", body_style),
            Paragraph("Akordeonu açın, Slayt 18 karşılaştırma tablosunu ve Held-Out F1 metriklerini gösterin.", body_style),
            Paragraph("Veri Bilimi<br/><b>10/10</b>", body_style)
        ],
        [
            Paragraph("<b>2:20 - 3:00</b><br/>(Kapanış & Q&A)", body_style),
            Paragraph("Tek tıkla <b>WhatsApp Gönder</b> butonunu ve <b>A4 PDF Servis Tutanak Çıktısını</b> gösterip bitirin: "
                      "<i>'EsnafDoktor; Google Gemma 4 ve TabPFN ile Türk e-ticaret satıcısını koruyan %100 açık kaynaklı bir copilot'tur. Sorularınızı almaktan onur duyarız.'</i>", body_style),
            Paragraph("A4 Servis Raporunu indirip açın ve WhatsApp butonuna tıklayın.", body_style),
            Paragraph("Yazı & Bütünlük<br/><b>10/10</b>", body_style)
        ]
    ]

    pitch_table = Table(pitch_data, colWidths=[65, 190, 185, 75])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 14))

    # Golden Checklist Box
    checklist_data = [
        [
            Paragraph("<b>JÜRİ MASASINA OTURMADAN ÖNCE 5 MADDELİK ALTIN KONTROL LİSTESİ:</b><br/>"
                      "1. <b>Laptop Wi-Fi'ını Kapatın:</b> Üst bantta 'Tamamen Çevrimdışı (Wi-Fi Kapalı)' rozeti yansın.<br/>"
                      "2. <b>Sesi Açın:</b> Sesli Asistan hoparlörden kararı okurken jüri net duysun.<br/>"
                      "3. <b>Raporu Hazır Tutun:</b> `EsnafDoktor_Teknik_Rapor.pdf` ve `EsnafDoktor_Juri_Savunma_Rehberi.pdf` masaüstünde hazır olsun.<br/>"
                      "4. <b>Asla %100 Doğruluk İddia Etmeyin:</b> '%73.2 ve %88.0 aldık çünkü test setimiz izole sınır vakalarıdır' deyin.<br/>"
                      "5. <b>TabPFN'i Savunun:</b> 'Metin Gemma'da, 5 sayısal sipariş parametresi TabPFN'de' cümlesini mutlaka kurun.", body_style)
        ]
    ]
    check_table = Table(checklist_data, colWidths=[WIDTH - (MARGIN * 2)])
    check_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#ef4444")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(check_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Copy to workspace root for easy user download/viewing
    shutil.copy(OUTPUT_PDF, WORKSPACE_PDF)
    print(f"Jury Defense Guide PDF built successfully at: {OUTPUT_PDF}")
    print(f"Copied to workspace root: {WORKSPACE_PDF}")


if __name__ == "__main__":
    build_pdf()
