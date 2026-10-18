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
        self.drawString(MARGIN, 18, "Yarışmacı Hazırlık Dokümanı · Açık Ağırlıklı Yerel Mimari (Gemma 3 4B + Hibrit RAG)")
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
        f"<b> Jüri Neyi Ölçüyor?</b> {what_judge_measures}",
        ParagraphStyle("CardIntent", fontName=fn, fontSize=8.5, leading=12, textColor=NAVY)
    )
    
    ans_p = Paragraph(
        f"<b> 100/100 Tam Puanlık Cevap:</b><br/>{full_score_answer}",
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
    story.append(Paragraph("EsnafDoktor — Fırat Üniversitesi Jüri Savunma Rehberi", title_style))
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
                      "• <b>Partner Teknolojisi:</b> Gemma 3 4B (+ TabPFN entegrasyonu)<br/>"
                      "• <b>Yaratıcılık:</b> Müşteri sohbeti + satıcı masası, sesli okuma", body_style)
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

    story.append(Paragraph("EN KRİTİK 7 JÜRİ SORUSU VE 100/100 TAM PUANLIK CEVAPLAR", section_h1))

    # Question 1: Architecture Division of Labor
    story.append(make_question_card(
        q_num=1,
        judge_name="Arş. Gör. Mehmet Arzu",
        criterion="Teknik Uygulama (%25)",
        question_text="Sistemde NLU, RAG, risk modeli ve Gemma var. Neden tek bir LLM ile çözmediniz?",
        what_judge_measures="Adayın mikro-model prensibini bilip bilmediği, LLM'i her işe körü körüne alet edip etmediği.",
        full_score_answer="Tek bir LLM her işe yetmez; kural uydurur ve sayısal riski tahmin edemez. Görevleri uzmanlarına dağıttık: "
                          "<b>1) NLU</b> niyeti (şikâyet / soru / teşekkür) çıkarır. "
                          "<b>2) Hibrit RAG (BM25 + E5 + RRF + Cross-Encoder ağırlığı)</b> 16 mağaza kuralından doğrusunu %95,2 isabetle bulur. "
                          "<b>3) Risk modeli</b> 5 sipariş verisinden iade suistimali riskini hesaplar. "
                          "<b>4) Gemma 3 4B</b> yalnızca bulunan kurala dayanarak müşteriye yanıt yazar; yanıtı bir dayanak denetiminden geçer. "
                          "Analiz ~0,46 sn, Gemma yanıtı ~1,4 sn: toplam ~2 saniye, 0 TL değişken maliyet.",
        golden_punchline="Gemma yazar, ama neyi yazacağına kural karar verir; riskli kararı ise satıcı verir.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 2: Data Leakage & Metrics
    story.append(make_question_card(
        q_num=2,
        judge_name="Arş. Gör. Diyar Güzelses",
        criterion="Veri Bilimi ve Doğrulama (%20)",
        question_text="Veri setiniz sentetik mi, gerçek mi? Skorlarınıza neden güvenelim?",
        what_judge_measures="Veri sızıntısı (leakage) olup olmadığı ve adayın dürüst akademik olgunluğu.",
        full_score_answer="Her sayımız repodaki bir betikle yeniden üretilebilir; elle yazılmış metrik yok. "
                          "Sistemi daha önce hiç görmediği 20 zorlu sınır vakasında (Held-Out Gold) test ettik: kategori doğruluğu <b>%95,0</b> (macro F1 %93,8). "
                          "Kural düzeyinde 21 günlük dil mesajında doğru kuralı <b>%95,2</b> isabetle buluyoruz; ablasyonda BM25 %81, E5 %71, RRF %81'de kalıyor. "
                          "Zayıf yanımızı da saklamıyoruz: ince ayarlı BERTurk dosyaları repoda değil, çalışan anahtar kelime NLU'su tek başına %60. "
                          "Bu yüzden arayüzde kategoriyi daha isabetli kural eşleşmesinden alıyoruz.",
        golden_punchline="Ölçemediğimiz hiçbir şeyi iddia etmiyoruz: python scripts/evaluate_honest_metrics.py çalıştırın, aynı sayıları görün.",
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
                          "Dürüst durum: güncel TabPFN ağırlıkları PriorLabs lisans onayı istiyor; onaydan sonra ED_USE_TABPFN=1 ile açılıyor. "
                          "O zamana kadar aynı 5 özellikten kalibre bir lojistik formül çalışıyor ve /api/health bunu açıkça gösteriyor. "
                          "Risk yüksekse asistan müşteriye iade sözü vermez; mesaj satıcıya Acil olarak düşer.",
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
        full_score_answer="Evet, modeller bir kez indirildikten sonra. Wi-Fi'ı jüri önünde kapatabiliriz. "
                          "Gemma 3 4B (Ollama), E5, Cross-Encoder, NLU ve risk modeli yerel donanımda çalışır; hiçbir bulut API çağrısı yoktur. "
                          "Açıkça söylediğimiz tek istisna: tarayıcının sesle yazma özelliği sesi bulut servisine gönderir; yanıtları sesli okuma ise yereldir. "
                          "Bu sayede iki dev avantaj sağlanır: "
                          "<b>1) 0.00 TL API Maliyeti:</b> Mesaj başına token faturası yok; maliyet mesaj sayısıyla artmaz. "
                          "<b>2) KVKK / Gizlilik:</b> Alıcının adresi, telefonu ve sepet tutarı yabancı bulutlara gitmez, cihazda kalır.",
        golden_punchline="İnternet kesilse de sistem yanıt verir; müşteri verisi bilgisayardan dışarı çıkmaz.",
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
        full_score_answer="Üç katmanlı önlem aldık. <b>1) Doğru kuralı bulmak:</b> BM25 + E5 + RRF + Cross-Encoder ağırlığıyla kural düzeyinde %95,2 isabet. "
                          "<b>2) Dayanak denetimi:</b> Gemma'nın yanıtındaki her sayı (gün, tutar, kod) kural metninde ya da müşterinin mesajında geçmek zorunda; "
                          "geçmezse yanıt bir kez yeniden yazdırılır, yine geçmezse kurala dayalı şablon gönderilir. Geliştirmede bir modelin "
                          "'iade süreniz 7 gün' uydurmasını bu denetim yakaladı. "
                          "<b>3) Karar satıcıda:</b> iade reddi, kullanılmış ürün, öfkeli dil ve yüksek riskte müşteriye yalnızca 'mağaza sahibine ilettim' gider.",
        golden_punchline="Model yazar, kural sınırlar, denetim doğrular, satıcı karar verir.",
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
                          "EsnafDoktor rutin soruları saatler yerine ~2 saniyede yanıtlayarak mağaza puanını korur; "
                          "riskli iadeleri gerekçesiyle satıcıya düşürerek tek bir sahte iadenin yazacağı zararı önler. "
                          "Mesaj başına API ücreti olmadığından maliyet mesaj sayısıyla artmaz.",
        golden_punchline="EsnafDoktor esnafa harcama yaptırmaz; haksız iadeleri ve kargo hasarlarını önleyerek doğrudan net kârını kurtarır.",
        fn=fn, fn_bold=fn_bold
    ))
    story.append(Spacer(1, 8))

    # Question 7: Voice Assistant & User Experience
    story.append(make_question_card(
        q_num=7,
        judge_name="Arş. Gör. Mert İncidelen",
        criterion="Yaratıcılık & UX (%15)",
        question_text="Müşteri ve satıcı bu sistemi nasıl kullanıyor?",
        what_judge_measures="Uygulamanın masa başında değil sahada nasıl kullanılacağının düşünülüp düşünülmediği.",
        full_score_answer="İki ekran var. <b>1) Müşteri sayfası:</b> ürün sayfasında 'Satıcıya sor' sohbeti ve yorum formu; "
                          "müşteri soruyu yazar ya da sesle söyler, ~2 saniyede kurala dayalı yanıt alır. "
                          "<b>2) Satıcı masası:</b> otomatik yanıtlananlar ve ona iletilen riskli vakalar; risk kaşesi, risk nedenleri, "
                          "kontrol listesi, dayanak kural ve yerel modelin yazdığı düzenlenebilir taslak. J/K ile gezinir, E ile onaylar. "
                          "Sesli karar özeti açıkken asistan kararı kısa bir cümleyle okur; kural kodu ve sipariş numarası gibi gürültüyü okumaz.",
        golden_punchline="Müşteri saniyeler içinde cevap alır; satıcı sadece gerçekten kendisine gereken vakalarla uğraşır.",
        fn=fn, fn_bold=fn_bold
    ))

    story.append(PageBreak())

    # 3. 3-Minute Live Pitch Sequence & Cheat Sheet
    story.append(Paragraph("3 DAKİKALIK JÜRİ SUNUM PLANI (CANLI PİTCH KRONOMETRESİ)", section_h1))
    
    pitch_data = [
        [
            Paragraph("<b>Zaman</b>", ParagraphStyle("TH1", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY)),
            Paragraph("<b>Sunucu Ne Anlatıyor?</b>", ParagraphStyle("TH2", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY)),
            Paragraph("<b>Ekranda Ne Gösteriliyor? (Aksiyon)</b>", ParagraphStyle("TH3", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY)),
            Paragraph("<b>Hedeflenen Puan</b>", ParagraphStyle("TH4", fontName=fn_bold, fontSize=8.5, textColor=PRIMARY))
        ],
        [
            Paragraph("<b>0:00 - 0:40</b><br/>(Giriş)", body_style),
            Paragraph("Problemi anlatın: e-ticarette satıcıya sorulan sorular saatlerce cevapsız kalıyor; geç cevap puanı düşürüyor, "
                      "aceleyle verilen iade onayı zarar ettiriyor. EsnafDoktor'un yerel açık modelle 0 TL'ye çalıştığını söyleyin.", body_style),
            Paragraph("Müşteri sayfasını açın; sağ üstte <b>Yerel · Gemma 3 4B</b> rozetini gösterin.", body_style),
            Paragraph("Temaya Uygunluk<br/><b>10/10</b>", body_style)
        ],
        [
            Paragraph("<b>0:40 - 1:40</b><br/>(Canlı Demo)", body_style),
            Paragraph("Önce rutin bir soru sorun ('Kargom 5 gündür gelmedi'): analiz çipleri, dayanak kural ve ~2 sn'de gelen yanıtı gösterin. "
                      "Sonra sert bir iade mesajı yazın ('Bir kere kullandım, etiketini kestim, paramı verin'): asistan iade sözü vermez, "
                      "'Mağaza sahibine iletildi · Acil' notu çıkar. Satıcı masası sekmesine geçin; mesaj en üstte, risk kaşesi ve kontrol listesiyle.", body_style),
            Paragraph("1. Rutin soru gönder.<br/>2. Riskli iade gönder.<br/>3. Satıcı masasına geç.<br/>4. Sesli karar özetini dinlet.", body_style),
            Paragraph("Teknik + UX<br/><b>10/10</b>", body_style)
        ],
        [
            Paragraph("<b>1:40 - 2:20</b><br/>(Bilimsel Kanıt)", body_style),
            Paragraph("Satıcı masasında <b>'Nasıl çalışıyor'</b> çekmecesini açın: hat, maliyet ve bulut API karşılaştırması. "
                      "Ayrılmış test setinde %95 kategori doğruluğunu, kural düzeyinde %95,2 isabeti ve dayanak denetimini anlatın. "
                      "Model seçiciden modelin değiştirilebildiğini (kilitlenme yok) gösterin.", body_style),
            Paragraph("Çekmeceyi açın; ardından docs/metrics.md'yi gösterin.", body_style),
            Paragraph("Veri Bilimi<br/><b>10/10</b>", body_style)
        ],
        [
            Paragraph("<b>2:20 - 3:00</b><br/>(Kapanış & Q&A)", body_style),
            Paragraph("Taslağı onaylayıp (E) sıradaki vakaya geçerek bitirin: "
                      "<i>'EsnafDoktor; satıcının kendi bilgisayarında çalışan açık ağırlıklı Gemma ile müşteriye saniyeler içinde, kurala dayalı yanıt veren "
                      "MIT lisanslı bir asistandır. Sorularınızı almaktan onur duyarız.'</i>", body_style),
            Paragraph("Satıcı masasında taslağı onaylayın.", body_style),
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
                      "1. <b>Sunucuyu Önceden Başlatın:</b> python server.py çalışsın, bir soru sorarak Gemma'yı ısıtın (ilk yanıt ~7 sn sürer). Satıcı masasında 'Demo verisini sıfırla'ya basın.<br/>"
                      "2. <b>Sesi Açın:</b> Sesli Asistan hoparlörden kararı okurken jüri net duysun.<br/>"
                      "3. <b>Raporu Hazır Tutun:</b> `EsnafDoktor_Teknik_Rapor.pdf` ve `EsnafDoktor_Juri_Savunma_Rehberi.pdf` masaüstünde hazır olsun.<br/>"
                      "4. <b>Sadece Ölçtüğünüzü Söyleyin:</b> '%95 kategori, %95,2 kural isabeti; betikle yeniden üretilebilir' deyin. BERTurk ve TabPFN'in bugünkü durumunu sorulursa dürüstçe anlatın.<br/>"
                      "5. <b>Wi-Fi Kapalı Gösterecekseniz Önce Prova Edin:</b> modeller inik olmalı; sesle yazma internet ister, yazarak gösterin.", body_style)
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
