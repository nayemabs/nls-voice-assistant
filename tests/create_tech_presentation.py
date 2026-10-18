#!/usr/bin/env python3
"""
Generate a 2-page PDF presentation on the technologies used in the Voice Assistant.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

# Color palette
DARK_NAVY = colors.Color(0.08, 0.12, 0.20)
NAVY = colors.Color(0.12, 0.18, 0.28)
ACCENT_GOLD = colors.Color(0.85, 0.65, 0.13)
LIGHT_GOLD = colors.Color(0.95, 0.85, 0.55)
WHITE = colors.white
LIGHT_GRAY = colors.Color(0.95, 0.95, 0.97)
MEDIUM_GRAY = colors.Color(0.6, 0.6, 0.65)
SUCCESS_GREEN = colors.Color(0.18, 0.55, 0.34)
SOFT_BLUE = colors.Color(0.88, 0.92, 0.98)
TECH_BLUE = colors.Color(0.20, 0.40, 0.70)
TECH_PURPLE = colors.Color(0.45, 0.25, 0.65)
TECH_TEAL = colors.Color(0.15, 0.50, 0.50)
TECH_ORANGE = colors.Color(0.80, 0.45, 0.10)

# Page dimensions
PAGE_W, PAGE_H = landscape(A4)  # 842 x 595
MARGIN = 40
HEADER_H = 74  # header bottom edge
FOOTER_H = 38  # footer top edge (gold line at 30 + some padding)


def draw_footer(c):
    c.setFillColor(MEDIUM_GRAY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 14,
        "On-Device Voice Assistant  •  NLS  •  Philipps-Universität Marburg  •  Winter 2025/26")
    c.setFillColor(ACCENT_GOLD)
    c.rect(MARGIN, 28, PAGE_W - 2 * MARGIN, 2, fill=1, stroke=0)


def draw_header(c, title, page_num):
    c.setFillColor(DARK_NAVY)
    c.rect(0, PAGE_H - 70, PAGE_W, 70, fill=1, stroke=0)
    c.setFillColor(ACCENT_GOLD)
    c.rect(0, PAGE_H - 74, PAGE_W, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(MARGIN + 10, PAGE_H - 48, title)
    c.setFont("Helvetica", 11)
    c.setFillColor(LIGHT_GOLD)
    c.drawRightString(PAGE_W - MARGIN - 10, PAGE_H - 48, f"{page_num} / 2")


def draw_tech_card(c, x, y, w, h, icon_text, title, description, color, bullets=None):
    """Draw a technology card. y is the BOTTOM of the card."""
    # Card background
    c.setFillColor(SOFT_BLUE)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    # Left accent
    c.setFillColor(color)
    c.roundRect(x, y, 6, h, 3, fill=1, stroke=0)
    # Icon circle
    c.setFillColor(color)
    c.circle(x + 28, y + h - 22, 14, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(x + 28, y + h - 26, icon_text)
    # Title
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 50, y + h - 26, title)
    # Description lines — generous gap below title/icon row
    c.setFillColor(colors.Color(0.3, 0.3, 0.35))
    c.setFont("Helvetica", 9)
    desc_lines = description if isinstance(description, list) else [description]
    desc_start_y = y + h - 54  # more breathing room below title
    for i, line in enumerate(desc_lines):
        c.drawString(x + 14, desc_start_y - i * 13, line)
    # Bullets
    if bullets:
        c.setFont("Helvetica", 8.5)
        bullet_start_y = desc_start_y - len(desc_lines) * 13 - 6
        for i, bullet in enumerate(bullets):
            by = bullet_start_y - i * 13
            c.setFillColor(color)
            c.drawString(x + 14, by, "•")
            c.setFillColor(colors.Color(0.35, 0.35, 0.4))
            c.drawString(x + 25, by, bullet)


def draw_page1(c):
    """Page 1: Core Technologies & Pipeline Overview"""
    draw_header(c, "Technology Stack & Pipeline", 1)
    draw_footer(c)

    # Layout constants
    title_h = 16       # section title text height
    title_gap = 10     # gap below title to pipeline
    pipe_h = 40        # pipeline box height
    pipe_gap = 14      # gap below pipeline to first card row
    card_gap_h = 14    # gap between card rows
    card_gap_w = 16    # gap between card columns

    # Available area
    area_top = PAGE_H - HEADER_H  # 521
    area_bot = FOOTER_H           # 38
    available = area_top - area_bot  # 483

    # Fixed content above cards
    fixed_h = title_h + title_gap + pipe_h + pipe_gap
    # Remaining space for 2 card rows + 1 gap, with equal top/bottom padding
    remaining = available - fixed_h  # ~403
    # Use 85% of remaining for cards, rest split as padding top/bottom
    cards_total = remaining * 0.88  # ~355
    card_h = (cards_total - card_gap_h) / 2  # ~170 each
    top_pad = (remaining - cards_total) / 2   # ~24

    block_top = area_top - top_pad

    # --- Pipeline section title ---
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN + 10, block_top - title_h, "Voice Assistant Pipeline")

    # --- Pipeline boxes ---
    pipeline_y = block_top - title_h - title_gap - pipe_h
    stages = [
        ("Audio\nInput", colors.Color(0.5, 0.5, 0.55)),
        ("ASR\n(Faster-Whisper)", TECH_BLUE),
        ("NLU\n(GLiNER + Regex)", TECH_PURPLE),
        ("Intent\nExecution", TECH_TEAL),
        ("NLG\n(Templates)", TECH_ORANGE),
        ("TTS\n(Piper)", SUCCESS_GREEN),
        ("Audio\nOutput", colors.Color(0.5, 0.5, 0.55)),
    ]
    box_w = 95
    box_h = pipe_h
    gap = 10
    total_w = len(stages) * box_w + (len(stages) - 1) * gap
    start_x = (PAGE_W - total_w) / 2

    for i, (label, clr) in enumerate(stages):
        bx = start_x + i * (box_w + gap)
        c.setFillColor(clr)
        c.roundRect(bx, pipeline_y, box_w, box_h, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        lines = label.split("\n")
        c.setFont("Helvetica-Bold", 8.5 if len(lines) > 1 else 10)
        for j, line in enumerate(lines):
            ly = pipeline_y + box_h / 2 + 4 - j * 11
            c.drawCentredString(bx + box_w / 2, ly, line)
        if i < len(stages) - 1:
            ax = bx + box_w + 1
            ay = pipeline_y + box_h / 2
            c.setFillColor(ACCENT_GOLD)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(ax + 4, ay - 3, "→")

    # --- Technology Cards (2x2 grid) ---
    card_w = (PAGE_W - 2 * MARGIN - card_gap_w) / 2

    row1_y = pipeline_y - pipe_gap - card_h        # top row bottom edge
    row2_y = row1_y - card_gap_h - card_h           # bottom row bottom edge
    left_x = MARGIN
    right_x = MARGIN + card_w + card_gap_w

    # Card 1: Faster-Whisper (ASR)
    draw_tech_card(c, left_x, row1_y, card_w, card_h,
        "W", "Faster-Whisper — ASR", [
            "CTranslate2-optimized Whisper model (4x faster than OpenAI).",
            "Converts spoken English audio into text transcriptions.",
        ], TECH_BLUE, [
            "Model: whisper-small (244M params, ~2GB)",
            "Quantization: int8 (CPU) / float16 (CUDA GPU)",
            "Includes ASR corrections for German city names",
            "Fallback: standard OpenAI Whisper if unavailable",
        ])

    # Card 2: GLiNER + Regex (NLU)
    draw_tech_card(c, right_x, row1_y, card_w, card_h,
        "G", "GLiNER + Regex — NLU", [
            "Hybrid NLU: regex detects intent, GLiNER extracts entities.",
            "Zero-shot entity recognition — no training data needed.",
        ], TECH_PURPLE, [
            "Intents: weather_query, create/get/update/delete appointment",
            "Entities: location, date, time, title, description",
            "spaCy pipeline for text preprocessing",
            "RapidFuzz for fuzzy string matching (typo tolerance)",
        ])

    # Card 3: Template NLG
    draw_tech_card(c, left_x, row2_y, card_w, card_h,
        "T", "Template-Based — NLG", [
            "Generates natural language responses from structured data.",
            "Uses randomized conversational fillers for naturalness.",
        ], TECH_ORANGE, [
            "Templates for weather, appointments, errors, greetings",
            "Dynamic slot filling (location, temp, date, time)",
            "Conversational fillers: \"Sure!\", \"Let me check...\"",
            "Context-aware responses based on dialogue history",
        ])

    # Card 4: Piper TTS
    draw_tech_card(c, right_x, row2_y, card_w, card_h,
        "P", "Piper — TTS", [
            "Fast neural text-to-speech engine, runs fully offline.",
            "Converts NLG text output into spoken audio.",
        ], SUCCESS_GREEN, [
            "Voice: en_US-lessac-medium (VITS neural model)",
            "Auto-downloads voice models on first use (~50MB)",
            "Low latency: suitable for real-time conversation",
            "Fallback: pyttsx3 (cross-platform, no download)",
        ])


def draw_page2(c):
    """Page 2: Supporting Technologies & How They Fit Together"""
    draw_header(c, "Supporting Technologies & Integration", 2)
    draw_footer(c)

    # Available area
    area_top = PAGE_H - HEADER_H   # 521
    area_bot = FOOTER_H            # 38

    # Split into left/right columns
    col_gap = 30
    col_w = (PAGE_W - 2 * MARGIN - col_gap) / 2
    left_x = MARGIN + 10
    right_x = MARGIN + col_w + col_gap

    # --- Estimate total content height to center vertically ---
    # Left: title(16) + gap(16) + table(~275) = ~307
    # Right: title(16) + gap(16) + weather_card(65) + gap(10) + cal_card(65) + gap(18)
    #        + title(16) + 4 features * 30 = ~326
    # Bottom box: 55
    # Total ≈ 326 + gap(18) + 55 = ~399
    content_h = 400
    top_pad = (area_top - area_bot - content_h) / 2
    top_y = area_top - top_pad

    # ===== LEFT COLUMN: Supporting Tech Table =====
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(left_x, top_y, "Supporting Technologies")

    table_data = [
        ["Technology", "Role in System"],
        ["Python 3.11+", "Core language for all modules"],
        ["spaCy", "NLP preprocessing (tokenization, POS tagging)"],
        ["RapidFuzz", "Fuzzy matching for entity normalization"],
        ["SpeechRecognition", "Microphone audio capture (voice mode)"],
        ["PyAudio", "Low-level audio I/O for mic input"],
        ["Requests", "HTTP client for Weather & Calendar APIs"],
        ["python-dateutil", "Natural date parsing (\"tomorrow\", \"Friday\")"],
        ["NumPy", "Audio array processing for ASR"],
        ["Docker", "Containerized deployment (CPU/CUDA)"],
        ["CTranslate2", "Optimized inference backend for Whisper"],
    ]

    table_col_widths = [110, col_w - 120]
    table = Table(table_data, colWidths=table_col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9.5),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))

    tw, th = table.wrapOn(c, PAGE_W, PAGE_H)
    table_top_y = top_y - 16
    table.drawOn(c, left_x, table_top_y - th)
    table_bottom_y = table_top_y - th

    # ===== RIGHT COLUMN =====
    # Section 1: External APIs
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(right_x, top_y, "External APIs")

    api_card_w = col_w - 20
    api_card_h = 65

    # Weather API card
    weather_top = top_y - 16
    weather_y = weather_top - api_card_h
    c.setFillColor(SOFT_BLUE)
    c.roundRect(right_x, weather_y, api_card_w, api_card_h, 6, fill=1, stroke=0)
    c.setFillColor(TECH_BLUE)
    c.roundRect(right_x, weather_y, 5, api_card_h, 3, fill=1, stroke=0)
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(right_x + 14, weather_y + api_card_h - 16, "Weather API  (POST)")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.Color(0.3, 0.3, 0.35))
    c.drawString(right_x + 14, weather_y + api_card_h - 30, "Endpoint: api.responsible-nlp.net/weather.php")
    c.drawString(right_x + 14, weather_y + api_card_h - 43, "Returns 7-day forecast with min/max temps & conditions.")
    c.drawString(right_x + 14, weather_y + api_card_h - 56, "Supports condition checks: rain, snow, sunny, cloudy, etc.")

    # Calendar API card
    cal_top = weather_y - 10
    cal_y = cal_top - api_card_h
    c.setFillColor(SOFT_BLUE)
    c.roundRect(right_x, cal_y, api_card_w, api_card_h, 6, fill=1, stroke=0)
    c.setFillColor(TECH_TEAL)
    c.roundRect(right_x, cal_y, 5, api_card_h, 3, fill=1, stroke=0)
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(right_x + 14, cal_y + api_card_h - 16, "Calendar API  (REST CRUD)")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.Color(0.3, 0.3, 0.35))
    c.drawString(right_x + 14, cal_y + api_card_h - 30, "Endpoint: api.responsible-nlp.net/calendar.php")
    c.drawString(right_x + 14, cal_y + api_card_h - 43, "Full CRUD: Create, Read, Update, Delete appointments.")
    c.drawString(right_x + 14, cal_y + api_card_h - 56, "Uses unique calenderid per team to avoid conflicts.")

    # Section 2: Dialogue Management
    dialogue_top = cal_y - 18
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(right_x, dialogue_top, "Dialogue Management")

    feat_items = [
        ("Context Tracking", "Maintains up to 10 conversation turns with timestamps"),
        ("Anaphora Resolution", "Resolves \"there\" → previous location, \"that\" → last appt."),
        ("Multi-Turn State", "Prompts for missing info (e.g., asks for date if not provided)"),
        ("Filler Removal", "Strips \"um\", \"uh\", \"like\", \"you know\" from ASR output"),
    ]

    feat_start_y = dialogue_top - 22
    feat_spacing = 30
    for i, (feat_title, feat_desc) in enumerate(feat_items):
        fy = feat_start_y - i * feat_spacing
        c.setFillColor(ACCENT_GOLD)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_x + 5, fy, feat_title)
        c.setFillColor(colors.Color(0.35, 0.35, 0.4))
        c.setFont("Helvetica", 9)
        c.drawString(right_x + 5, fy - 13, feat_desc)

    # Find the lowest content point from both columns
    right_bottom = feat_start_y - (len(feat_items) - 1) * feat_spacing - 13
    lowest_content = min(table_bottom_y, right_bottom)

    # ===== BOTTOM: Design Principles box — placed just below content =====
    box_h = 55
    box_y = lowest_content - box_h - 18
    # Clamp so it doesn't go below footer
    box_y = max(box_y, FOOTER_H + 8)
    c.setFillColor(colors.Color(0.96, 0.96, 0.98))
    c.roundRect(MARGIN, box_y, PAGE_W - 2 * MARGIN, box_h, 8, fill=1, stroke=0)
    c.setStrokeColor(ACCENT_GOLD)
    c.setLineWidth(2)
    c.roundRect(MARGIN, box_y, PAGE_W - 2 * MARGIN, box_h, 8, fill=0, stroke=1)
    c.setFillColor(DARK_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN + 15, box_y + 38, "Design Principles")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.Color(0.3, 0.3, 0.35))
    c.drawString(MARGIN + 15, box_y + 23,
        "Fully On-Device  •  All core models (ASR, NLU, TTS) run locally — no cloud AI services needed.")
    c.drawString(MARGIN + 15, box_y + 9,
        "Graceful Fallbacks  •  Each component has a fallback: Faster-Whisper → Whisper, Piper → pyttsx3, GLiNER → Regex-only NLU.")


def main():
    import os
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "tech_presentation.pdf"
    )

    c = canvas.Canvas(output_path, pagesize=landscape(A4))

    draw_page1(c)
    c.showPage()

    draw_page2(c)
    c.showPage()

    c.save()
    print(f"Presentation saved to: {output_path}")


if __name__ == "__main__":
    main()
