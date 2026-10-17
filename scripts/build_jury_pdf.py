"""Build the Turkish jury preparation PDF from docs/PROJE_REHBERI.md.

Documentation-only tool. Requires reportlab and a Turkish-capable font.
Run: python scripts/build_jury_pdf.py
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs' / 'PROJE_REHBERI.md'
OUTPUT = ROOT / 'output' / 'pdf' / 'DiskDoctor_Juri_Hazirlik.pdf'
NAVY = colors.HexColor('#142C40')
TEAL = colors.HexColor('#087E81')
ORANGE = colors.HexColor('#E66D48')
MUTED = colors.HexColor('#536675')
LIGHT = colors.HexColor('#EDF4F6')
WIDTH, HEIGHT = A4
MARGIN = 47
CONTENT_WIDTH = WIDTH - 2 * MARGIN


def register_fonts():
    candidates = [
        (Path('C:/Windows/Fonts'), 'arial.ttf', 'arialbd.ttf', 'ariali.ttf'),
        (Path('/usr/share/fonts/truetype/dejavu'), 'DejaVuSans.ttf',
         'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf'),
    ]
    for folder, normal, bold, italic in candidates:
        if all((folder / name).exists() for name in (normal, bold, italic)):
            for family, name in [('Body', normal), ('Body-Bold', bold), ('Body-Italic', italic)]:
                pdfmetrics.registerFont(TTFont(family, str(folder / name)))
            pdfmetrics.registerFontFamily('Body', normal='Body', bold='Body-Bold',
                                          italic='Body-Italic', boldItalic='Body-Bold')
            return
    raise FileNotFoundError('A Turkish-capable Arial or DejaVu Sans font is required.')


def inline(text):
    # The source is authored locally; escape it before adding limited markup.
    text = text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font color="#087E81">\1</font>', text)
    # URLs remain readable and clickable; long links wrap at punctuation.
    def link(match):
        url = match.group(0).rstrip(';,')
        visible = url.replace('/', '/\u200b').replace('_', '_\u200b')
        return f'<link href="{url}" color="#087E81">{visible}</link>'
    return re.sub(r'https?://[^\s<]+', link, text)


def architecture():
    d = Drawing(CONTENT_WIDTH, 146)
    labels = ['Şikâyet', 'Yerel arama', 'Kaynak + LLM', 'Kontrol / rapor']
    gap = 10
    box_w = (CONTENT_WIDTH - gap * 3) / 4
    for i, label in enumerate(labels):
        x = i * (box_w + gap)
        d.add(Rect(x, 94, box_w, 40, fillColor=NAVY if i == 0 else LIGHT,
                   strokeColor=None, rx=7, ry=7))
        d.add(String(x + box_w / 2, 110, label, textAnchor='middle',
                     fontName='Body-Bold', fontSize=10,
                     fillColor=colors.white if i == 0 else NAVY))
        if i < 3:
            sx = x + box_w + 1
            d.add(Line(sx, 114, sx + gap - 3, 114, strokeColor=TEAL))
            d.add(Polygon([sx + gap - 2, 114, sx + gap - 6, 117,
                           sx + gap - 6, 111], fillColor=TEAL, strokeColor=None))
    d.add(Rect(100, 23, CONTENT_WIDTH - 200, 41, fillColor=colors.HexColor('#FFF1E9'),
               strokeColor=None, rx=6, ry=6))
    d.add(String(CONTENT_WIDTH / 2, 48, 'İsteğe bağlı: SMART JSON + disk değerlendirmesi',
                 textAnchor='middle', fontName='Body-Bold', fontSize=10, fillColor=NAVY))
    d.add(String(CONTENT_WIDTH / 2, 33, 'HDD: TabPFN / RF     |     NVMe: kurallar',
                 textAnchor='middle', fontName='Body', fontSize=9, fillColor=MUTED))
    d.add(Line(CONTENT_WIDTH - 122, 64, CONTENT_WIDTH - 70, 91, strokeColor=ORANGE))
    d.add(String(0, 4, 'Hedef mimari: RAG/Gemma kolu henüz uygulanmış değil.',
                 fontName='Body-Italic', fontSize=9, fillColor=MUTED))
    return d


def main():
    register_fonts()
    source = SOURCE.read_text(encoding='utf-8')
    sections = source.split('\n## ')
    total = len(sections)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyTR', fontName='Body', fontSize=11.2, leading=16.3,
                              textColor=NAVY, spaceAfter=10, alignment=TA_LEFT))
    styles.add(ParagraphStyle('TitleTR', parent=styles['BodyTR'], fontName='Body-Bold',
                              fontSize=27, leading=32, spaceAfter=19))
    styles.add(ParagraphStyle('ChapterTR', parent=styles['TitleTR'], fontSize=23,
                              leading=28, spaceAfter=20))
    styles.add(ParagraphStyle('EyebrowTR', parent=styles['BodyTR'], fontName='Body-Bold',
                              fontSize=10, leading=13, textColor=TEAL, spaceAfter=12))
    styles.add(ParagraphStyle('BulletTR', parent=styles['BodyTR'], leftIndent=13,
                              firstLineIndent=-10, spaceAfter=7))
    styles.add(ParagraphStyle('CellTR', parent=styles['BodyTR'], fontSize=9.3,
                              leading=12.8, spaceAfter=0))
    styles.add(ParagraphStyle('SourceTR', parent=styles['BodyTR'], fontSize=9.5,
                              leading=14, spaceAfter=9))
    styles.add(ParagraphStyle('TableHeadTR', parent=styles['CellTR'],
                              fontName='Body-Bold', textColor=colors.white))

    def page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(TEAL)
        canvas.rect(0, HEIGHT - 8, WIDTH, 8, fill=1, stroke=0)
        canvas.setFillColor(MUTED)
        canvas.setFont('Body-Bold', 8)
        canvas.drawString(MARGIN, HEIGHT - 30, 'DISKDOCTOR / JÜRİ HAZIRLIK DOSYASI')
        canvas.setFont('Body', 8)
        canvas.drawRightString(WIDTH - MARGIN, HEIGHT - 30, 'KANIT + HEDEF + AÇIK İŞLER')
        canvas.setStrokeColor(colors.HexColor('#DCE5EA'))
        canvas.line(MARGIN, 43, WIDTH - MARGIN, 43)
        canvas.setFont('Body', 8)
        canvas.drawString(MARGIN, 29, '17 Ekim 2026  |  Kod denetimi: a0944ba')
        canvas.drawRightString(WIDTH - MARGIN, 29, f'{doc.page:02d} / {total:02d}')
        canvas.restoreState()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, title='DiskDoctor - Projeyi Anlama ve Jüriye Hazırlık',
                           author='DiskDoctor ekibi', subject='Mevcut kanıtlar, RAG odaklı ürün önerisi ve jüri soruları',
                           leftMargin=MARGIN, rightMargin=MARGIN, topMargin=58, bottomMargin=59)
    frame = Frame(MARGIN, 59, CONTENT_WIDTH, HEIGHT - 117,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='main', frames=[frame], onPage=page))
    story = []

    def table(lines):
        rows = [[cell.strip() for cell in line.strip().strip('|').split('|')]
                for line in lines if not re.fullmatch(r'[|:\-\s]+', line)]
        n = len(rows[0])
        if n == 5:
            widths = [CONTENT_WIDTH * p for p in (.34, .19, .15, .16, .16)]
        elif n == 3:
            widths = [CONTENT_WIDTH * p for p in (.31, .25, .44)]
        else:
            widths = [CONTENT_WIDTH / n] * n
        data = [[Paragraph(inline(cell), styles['TableHeadTR' if i == 0 else 'CellTR'])
                 for cell in row] for i, row in enumerate(rows)]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT, colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, -1), (-1, -1), .6, colors.HexColor('#C8D8DE')),
        ]))
        return [t, Spacer(1, 14)]

    for index, section in enumerate(sections):
        if index:
            story.append(PageBreak())
        lines = section.strip().splitlines()
        title = lines.pop(0).removeprefix('# ')
        if index == 0:
            story += [Spacer(1, 22), Paragraph('TÜRKÇE PROJE VE KONUŞMACI REHBERİ', styles['EyebrowTR']),
                      Paragraph('DiskDoctor', styles['TitleTR']),
                      Paragraph('Projeyi anlama.<br/>Jüriye hazırlanma.', styles['TitleTR'])]
        else:
            number, heading = title.split(' | ', 1)
            story += [Paragraph(f'BÖLÜM {number} / {len(sections) - 1:02d}', styles['EyebrowTR']),
                      Paragraph(inline(heading), styles['ChapterTR'])]
            if number == '05':
                story += [architecture(), Spacer(1, 15)]
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith('|'):
                block = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    block.append(lines[i].strip())
                    i += 1
                story.extend(table(block))
                continue
            numbered = re.match(r'^(\d+)\. (.+)', line)
            bullet = line.startswith('- ')
            if bullet or numbered:
                text = ('• ' + line[2:]) if bullet else line
                style = styles['SourceTR'] if index == len(sections) - 1 else styles['BulletTR']
                story.append(Paragraph(inline(text), style))
                i += 1
                continue
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('|'):
                para.append(lines[i].strip())
                i += 1
            story.append(Paragraph(inline(' '.join(para)), styles['BodyTR']))
    doc.build(story)
    print(f'PDF built: {OUTPUT}; expected pages: {total}')


if __name__ == '__main__':
    main()
