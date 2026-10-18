"""
Build professional Turkish Technical Report PDF for EsnafDoktor.
Uses system ReportLab with Arial font (full Turkish character support).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PDF = ROOT_DIR / "docs" / "EsnafDoktor_Teknik_Rapor.pdf"
WORKSPACE_PDF = ROOT_DIR.parent / "EsnafDoktor_Teknik_Rapor.pdf"

# Colors
PRIMARY = colors.HexColor("#1e293b")      # Deep Slate Navy
ACCENT = colors.HexColor("#c2410c")       # Terracotta Orange
SUCCESS = colors.HexColor("#15803d")      # Forest Green
WARNING = colors.HexColor("#b45309")      # Amber
MUTED = colors.HexColor("#64748b")        # Slate Gray
BG_LIGHT = colors.HexColor("#f8fafc")     # Light Slate
BG_WARM = colors.HexColor("#fef7f2")      # Soft Terracotta Tint
BORDER_COLOR = colors.HexColor("#e2e8f0")

WIDTH, HEIGHT = A4
MARGIN = 40


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


def build_pdf():
    fn = setup_fonts()
    fn_bold = f"{fn}-Bold" if fn == "ArialTR" else "Helvetica-Bold"

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        fontName=fn_bold,
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        fontName=fn,
        fontSize=11,
        leading=15,
        textColor=ACCENT,
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        fontName=fn_bold,
        fontSize=13,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        fontName=fn_bold,
        fontSize=11,
        leading=15,
        textColor=ACCENT,
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "DocBody",
        fontName=fn,
        fontSize=9,
        leading=13,
        textColor=PRIMARY,
        spaceAfter=6
    )
    body_bold = ParagraphStyle(
        "DocBodyBold",
        fontName=fn_bold,
        fontSize=9,
        leading=13,
        textColor=PRIMARY
    )
    callout_style = ParagraphStyle(
        "Callout",
        fontName=fn,
        fontSize=8.5,
        leading=12,
        textColor=PRIMARY
    )
    table_cell = ParagraphStyle(
        "TableCell",
        fontName=fn,
        fontSize=8,
        leading=11,
        textColor=PRIMARY
    )
    table_header = ParagraphStyle(
        "TableHeader",
        fontName=fn_bold,
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Title & Header
    story.append(Paragraph("EsnafDoktor (MerchantDoctor) — Teknik Rapor", title_style))
    story.append(Paragraph("Açık Ağırlıklı Gemma 3 4B ve Hibrit RAG ile Satıcıya Sorulan Sorulara Saniyeler İçinde Kurala Dayalı Yanıt", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=10))

    # Meta Info Table
    meta_data = [
        [
            Paragraph("<b>Yarışma:</b> Hacktoberfest Elazığ 2026 (FÜBEV / MLH / DEV)", table_cell),
            Paragraph("<b>Tarih:</b> 18 Ekim 2026", table_cell),
            Paragraph("<b>Lisans:</b> MIT (Tamamen Açık Kaynak)", table_cell)
        ],
        [
            Paragraph("<b>Hedef Ödüller:</b> Gemma ($200), Open Source ($200), TabPFN ($200)", table_cell),
            Paragraph("<b>Altyapı:</b> Yerel çıkarım, 0.00 TL API", table_cell),
            Paragraph("<b>Test Durumu:</b> 7/7 birim testi geçti", table_cell)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[200, 150, 165])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_WARM),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f8d7c2")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 1. Executive Summary & Problem
    story.append(Paragraph("1. Yönetici Özeti ve Problem Tanımı", h1_style))
    story.append(Paragraph(
        "E-ticaret sitelerinde satıcıya sorulan sorular (kargo nerede, beden değişimi, çift çekim, iade süresi) çoğu zaman saatlerce "
        "cevapsız kalır. Trendyol, Hepsiburada ve Instagram üzerinden satış yapan küçük satıcı hem siparişi paketler hem de günde yüzlerce "
        "mesaja yetişmeye çalışır. Geç yanıt pazar yeri mağaza puanını düşürür; her iade talebinin koşulsuz kabulü ise kullanılmış veya "
        "etiketi sökülmüş ürünlerde doğrudan zarar yazar. Mesaj başına ücretli bulut yapay zekâ servisleri ise maliyeti mesaj sayısıyla büyütür. "
        "<b>EsnafDoktor</b>, satıcının kendi bilgisayarında çalışan açık ağırlıklı bir modelle rutin soruları saniyeler içinde, "
        "mağazanın kendi kuralına dayanarak yanıtlar; riskli vakaları ise gerekçesiyle satıcıya iletir.",
        body_style
    ))

    # 2. Üç Sütunlu Çekirdek Mimari
    story.append(Paragraph("2. Teknik Mimari ve Model Dağılımı", h1_style))
    arch_data = [
        [
            Paragraph("Modül", table_header),
            Paragraph("Kullanılan Teknoloji", table_header),
            Paragraph("Görevi ve Sisteme Katkısı", table_header),
            Paragraph("Süre (ısınmış)", table_header)
        ],
        [
            Paragraph("<b>NLU Motoru</b>", table_cell),
            Paragraph("Türkçe anahtar kelime sınıflandırıcı (ince ayarlı BERTurk yuvası hazır)", table_cell),
            Paragraph("Mesajı 3 niyete (şikâyet, bilgi, teşekkür) ayırır. Kategori, daha isabetli olan kural eşleşmesinden alınır.", table_cell),
            Paragraph("< 1 ms", table_cell)
        ],
        [
            Paragraph("<b>Hibrit RAG</b>", table_cell),
            Paragraph("BM25 + multilingual-e5-small + RRF + Cross-Encoder ağırlığı", table_cell),
            Paragraph("16 mağaza kuralından doğrusunu bulur; kural düzeyinde %95,2 isabet.", table_cell),
            Paragraph("~440 ms (CPU)", table_cell)
        ],
        [
            Paragraph("<b>Tabular Risk</b>", table_cell),
            Paragraph("TabPFN entegrasyonu; lisans onayına kadar kalibre lojistik formül", table_cell),
            Paragraph("Tutar, teslimat, iade geçmişi, açılış videosu ve hasar bildiriminden iade suistimali riskini hesaplar.", table_cell),
            Paragraph("< 1 ms", table_cell)
        ],
        [
            Paragraph("<b>Akıl Yürütme & Aksiyon</b>", table_cell),
            Paragraph("Gemma 3 4B (Ollama, yerel GPU) + dayanak denetimi", table_cell),
            Paragraph("Yalnızca bulunan kurala dayanarak müşteriye yanıt yazar; kuralda geçmeyen sayı içeren yanıt reddedilir.", table_cell),
            Paragraph("~1,4 sn", table_cell)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[90, 130, 215, 80])
    arch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 10))

    # 3. Neden Açık Kaynak? (Slayt 18 Cevabı)
    story.append(Paragraph("3. Jüri Analizi: Neden Açık Kaynak Kapalı API'den (GPT-4o) Üstün?", h1_style))
    why_data = [
        [Paragraph("Kriter", table_header), Paragraph("Kapalı API (OpenAI GPT-4o / Claude)", table_header), Paragraph("EsnafDoktor (Yerel Açık Kaynak)", table_header)],
        [
            Paragraph("<b>Değişken Maliyet</b>", table_cell),
            Paragraph("Mesaj başına ücret; maliyet mesaj sayısıyla büyür.", table_cell),
            Paragraph("<b>0.00 TL.</b> Cihaz üzerinde sınırsız ve ücretsiz çalışır.", table_cell)
        ],
        [
            Paragraph("<b>İnternet Bağımlılığı</b>", table_cell),
            Paragraph("Bağlantı koptuğunda yanıt üretilemez.", table_cell),
            Paragraph("<b>Yerel çıkarım.</b> Modeller indirildikten sonra Wi-Fi kapalıyken de yanıt verir.", table_cell)
        ],
        [
            Paragraph("<b>Veri Gizliliği (KVKK)</b>", table_cell),
            Paragraph("Müşteri adı, adresi, telefon numarası ve sepet tutarı yabancı buluta uçar.", table_cell),
            Paragraph("<b>Sıfır Sızıntı.</b> Tüm müşteri kayıtları yerel sabit diskte kalır.", table_cell)
        ],
        [
            Paragraph("<b>Kilitlenme</b>", table_cell),
            Paragraph("Fiyat ve model sağlayıcının elinde.", table_cell),
            Paragraph("<b>Model değiştirilebilir.</b> Satıcı masasından Gemma, Qwen, Llama seçilir.", table_cell)
        ]
    ]
    why_table = Table(why_data, colWidths=[110, 200, 205])
    why_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(why_table)
    story.append(Spacer(1, 10))

    # Page Break for Clean Results Page
    story.append(PageBreak())

    # 4. Bilimsel Değerlendirme & Metrikler (Held-Out Gold)
    story.append(Paragraph("4. Deneysel Değerlendirme & Dürüst Akademik Metrikler", h1_style))
    story.append(Paragraph(
        "Tüm sayılar <b>python scripts/evaluate_honest_metrics.py</b> ile bu repoda yeniden üretilir (docs/metrics.md). "
        "Sınıflandırma, eğitimde kullanılmamış <b>20 vakalık Held-Out Gold Set</b> üzerinde; kural getirme ise doğru cevabı tek bir "
        "politika olan 21 günlük dil müşteri mesajında ölçülmüştür.",
        body_style
    ))

    # Metrics Table
    metrics_data = [
        [Paragraph("Görev / Test Katmanı", table_header), Paragraph("Metrik", table_header), Paragraph("Elde Edilen Değer", table_header), Paragraph("Açıklama & Hata Analizi", table_header)],
        [
            Paragraph("Kategori (sistem)", table_cell),
            Paragraph("Doğruluk / Macro F1", table_cell),
            Paragraph("<b>%95,0 / %93,8</b>", table_cell),
            Paragraph("Kategori eşleşen kuraldan alınır. Anahtar kelime NLU'su tek başına %60,0 / %54,0'da kalır.", table_cell)
        ],
        [
            Paragraph("Niyet (anahtar kelime NLU)", table_cell),
            Paragraph("Macro F1", table_cell),
            Paragraph("<b>%61,2</b>", table_cell),
            Paragraph("İnce ayarlı BERTurk dosyaları repoda değil; en zayıf halka ve sıradaki iyileştirme.", table_cell)
        ],
        [
            Paragraph("Kural getirme (kural düzeyi)", table_cell),
            Paragraph("Hit@1", table_cell),
            Paragraph("<b>%95,2</b> (20/21)", table_cell),
            Paragraph("Ablasyon: BM25 %81,0 · E5 %71,4 · RRF %81,0 · Cross-Encoder tek başına 17/21.", table_cell)
        ],
        [
            Paragraph("Kural getirme (kategori düzeyi)", table_cell),
            Paragraph("Hit@1 / Hit@3", table_cell),
            Paragraph("<b>%100 / %100</b>", table_cell),
            Paragraph("Doğru kategoriden herhangi bir kural isabet sayılır; kural düzeyinden daha kolay bir ölçüt.", table_cell)
        ],
        [
            Paragraph("Yanıt dayanak denetimi", table_cell),
            Paragraph("İlk denemede geçen", table_cell),
            Paragraph("<b>8/8</b>", table_cell),
            Paragraph("Gemma 3 4B, 8 örnek soru ve yorum. Kuralda olmayan sayı içeren yanıt reddedilir, şablona dönülür.", table_cell)
        ],
        [
            Paragraph("Uçtan uca yanıt", table_cell),
            Paragraph("Ortalama süre", table_cell),
            Paragraph("<b>~2 sn</b>", table_cell),
            Paragraph("Analiz ~0,46 sn (CPU) + Gemma ~1,4 sn (GPU, 2,9 GB). İlk istekte model yüklemesi ~7 sn.", table_cell)
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[120, 80, 105, 210])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # 5. Sentetik Veri İyileştirmesi
    story.append(Paragraph("5. Sentetik Veri İyileştirmesi: Robotik Şablondan Gerçek Hayata", h1_style))
    story.append(Paragraph(
        "Önceki çalışmalardaki mekanik slot doldurma (örn: <i>'Merhaba canli destekte bugun kargom gelmedi'</i>) yapaydı. "
        "Geliştirdiğimiz yeni üretim motorunda <b>8 farklı tüketici personası</b> (Öfkeli, Aceleci Genç, Yaşlı/Acemi, Pazarlıkçı vb.) "
        "tanımlanmış ve <b>%38.8 oranında mobil klavye gürültüsü</b> (ş->s, ç->c, bitişik harf kayması, noktalama eksikliği) "
        "enjekte edilerek <b>3.000 satırlık yüksek gerçekçilikli korpus</b> üretilmiştir.",
        body_style
    ))

    # 6. İş Modeli ve Jüri Kapanışı
    story.append(Paragraph("6. Side Hustle İş Modeli & Sahadaki Değer", h1_style))
    story.append(Paragraph(
        "Tek bir sahte deri mont iadesi esnafa <b>5.800 TL</b> doğrudan zarar yazmaktadır. "
        "Hasarlı kargolarda zabıt tutanağı tutturulmadığı için kargo firmasının ödemediği tazminat esnafın cebinden çıkmaktadır. "
        "EsnafDoktor rutin soruları saatler yerine yaklaşık 2 saniyede yanıtlayarak mağaza puanını korur; riskli iadeleri gerekçesiyle "
        "satıcıya ileterek tek bir haksız iadenin yazacağı zararı önler. Mesaj başına API ücreti olmadığı için maliyet mesaj sayısıyla artmaz. "
        "Önerilen fiyatlandırma: tek seferlik 1.500 TL kurulum veya aylık 250 TL bakım.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Final Footer Sign-off
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceAfter=8))
    story.append(Paragraph(
        "<b>EsnafDoktor Ekibi</b> — Hacktoberfest Elazığ 2026 | Fırat Üniversitesi Bilgisayar Mühendisliği | MIT Lisansı",
        ParagraphStyle("Footer", fontName=fn, fontSize=8, textColor=MUTED, alignment=1)
    ))

    doc.build(story)

    # Also copy to workspace root
    import shutil
    shutil.copyfile(str(OUTPUT_PDF), str(WORKSPACE_PDF))
    print(f"PDF built successfully at:\n- {OUTPUT_PDF}\n- {WORKSPACE_PDF}")


if __name__ == "__main__":
    build_pdf()
