#!/usr/bin/env python3
"""
Generate a professional PDF presentation from evaluation results
Enhanced version with better visuals and no overlapping
"""

import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ============== COLOR PALETTE ==============
# Professional dark theme with gold accents
DARK_NAVY = colors.Color(0.08, 0.12, 0.20)
NAVY = colors.Color(0.12, 0.18, 0.28)
ACCENT_GOLD = colors.Color(0.85, 0.65, 0.13)
LIGHT_GOLD = colors.Color(0.95, 0.85, 0.55)
WHITE = colors.white
LIGHT_GRAY = colors.Color(0.95, 0.95, 0.97)
MEDIUM_GRAY = colors.Color(0.6, 0.6, 0.65)
SUCCESS_GREEN = colors.Color(0.18, 0.55, 0.34)
SOFT_BLUE = colors.Color(0.88, 0.92, 0.98)


class PresentationPDF:
    def __init__(self, output_path, metrics_path):
        self.output_path = output_path
        self.width, self.height = landscape(A4)
        self.margin = 40

        # Load metrics
        with open(metrics_path, 'r') as f:
            data = json.load(f)
        self.metrics = data['metrics']
        self.metadata = data['metadata']

    def create(self):
        c = canvas.Canvas(self.output_path, pagesize=landscape(A4))

        # Page 1: Title
        self.draw_title_page(c)
        c.showPage()

        # Page 2: ASR & Intent Classification
        self.draw_page2(c)
        c.showPage()

        # Page 3: Slots, E2E, Latency, Task Success
        self.draw_page3(c)
        c.showPage()

        c.save()
        print(f"Presentation saved to: {self.output_path}")

    def draw_gradient_bg(self, c):
        """Draw a subtle gradient-like background"""
        # Main background
        c.setFillColor(WHITE)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Top header area
        c.setFillColor(DARK_NAVY)
        c.rect(0, self.height - 70, self.width, 70, fill=1, stroke=0)

        # Gold accent line
        c.setFillColor(ACCENT_GOLD)
        c.rect(0, self.height - 74, self.width, 4, fill=1, stroke=0)

    def draw_header(self, c, title, page_num):
        """Draw page header"""
        self.draw_gradient_bg(c)

        # Title
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(self.margin + 10, self.height - 48, title)

        # Page indicator
        c.setFont("Helvetica", 11)
        c.setFillColor(LIGHT_GOLD)
        c.drawRightString(self.width - self.margin - 10, self.height - 48, f"{page_num} / 3")

    def draw_footer(self, c):
        """Draw page footer"""
        c.setFillColor(MEDIUM_GRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width / 2, 18,
            "On-Device Voice Assistant  •  Weather & Appointments  •  NLS  •  Philipps-Universität Marburg  •  Winter 2025/26")

        # Bottom accent line
        c.setFillColor(ACCENT_GOLD)
        c.rect(self.margin, 30, self.width - 2*self.margin, 2, fill=1, stroke=0)

    def draw_title_page(self, c):
        """Draw an impressive title page"""
        # Full dark background
        c.setFillColor(DARK_NAVY)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Decorative geometric elements
        c.setFillColor(NAVY)
        c.rect(0, self.height - 180, self.width, 180, fill=1, stroke=0)

        # Gold accent bars
        c.setFillColor(ACCENT_GOLD)
        c.rect(0, self.height - 185, self.width, 5, fill=1, stroke=0)
        c.rect(self.width/2 - 200, self.height * 0.52, 400, 3, fill=1, stroke=0)

        # University name with subtle styling
        c.setFillColor(LIGHT_GOLD)
        c.setFont("Helvetica", 14)
        c.drawCentredString(self.width / 2, self.height - 55, "PHILIPPS-UNIVERSITÄT MARBURG")

        # Course name - prominent
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(self.width / 2, self.height - 110, "Natural Language Systems")

        # Semester
        c.setFont("Helvetica", 16)
        c.setFillColor(MEDIUM_GRAY)
        c.drawCentredString(self.width / 2, self.height - 145, "Winter Semester 2025/26")

        # Main project title box
        box_y = self.height * 0.42
        box_height = 85
        c.setFillColor(colors.Color(0.15, 0.22, 0.32))
        c.roundRect(self.margin * 2, box_y, self.width - self.margin * 4, box_height, 12, fill=1, stroke=0)

        # Border for the box
        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(2)
        c.roundRect(self.margin * 2, box_y, self.width - self.margin * 4, box_height, 12, fill=0, stroke=1)

        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(self.width / 2, box_y + 52, "On-Device Voice Assistant")

        c.setFillColor(ACCENT_GOLD)
        c.setFont("Helvetica", 14)
        c.drawCentredString(self.width / 2, box_y + 25, "Weather Queries & Appointment Management")
        c.setFillColor(MEDIUM_GRAY)
        c.setFont("Helvetica", 11)
        c.drawCentredString(self.width / 2, box_y + 8, "Faster-Whisper ASR  •  Hybrid NLU (GLiNER + Regex)  •  Template NLG")

        # Team section header
        team_header_y = self.height * 0.32
        c.setFillColor(ACCENT_GOLD)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(self.width / 2, team_header_y, "— TEAM MEMBERS —")

        # Team members in a clean grid
        members = [
            ("Abu Bakar Siddik Nayem", "3875335"),
            ("Shibin Benny", "3872714"),
            ("M A Moit Sowrav", "3854501"),
            ("Muhammad Safkat Uddin Jamie", "3864520"),
        ]

        # Calculate positions for 2x2 grid
        col1_x = self.width * 0.28
        col2_x = self.width * 0.72
        row1_y = team_header_y - 45
        row2_y = team_header_y - 105

        positions = [(col1_x, row1_y), (col2_x, row1_y), (col1_x, row2_y), (col2_x, row2_y)]

        for i, (name, matrikel) in enumerate(members):
            x, y = positions[i]

            # Member card background
            card_w, card_h = 200, 50
            c.setFillColor(colors.Color(0.1, 0.15, 0.22))
            c.roundRect(x - card_w/2, y - 15, card_w, card_h, 8, fill=1, stroke=0)

            # Name
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(x, y + 18, name)

            # Matriculation
            c.setFillColor(MEDIUM_GRAY)
            c.setFont("Helvetica", 10)
            c.drawCentredString(x, y, f"Matriculation: {matrikel}")

        # Date at bottom
        c.setFillColor(MEDIUM_GRAY)
        c.setFont("Helvetica", 11)
        c.drawCentredString(self.width / 2, 35, "February 2026")

        # Decorative bottom bar
        c.setFillColor(ACCENT_GOLD)
        c.rect(self.width/2 - 50, 55, 100, 2, fill=1, stroke=0)

    def draw_metric_card(self, c, x, y, width, height, title, value, subtitle=None, is_good=True):
        """Draw a styled metric card"""
        # Card background
        c.setFillColor(SOFT_BLUE)
        c.roundRect(x, y, width, height, 6, fill=1, stroke=0)

        # Left accent bar
        accent_color = SUCCESS_GREEN if is_good else ACCENT_GOLD
        c.setFillColor(accent_color)
        c.roundRect(x, y, 5, height, 3, fill=1, stroke=0)

        # Title
        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 12, y + height - 14, title)

        # Value - adjust font size based on card height
        font_size = 20 if height < 50 else 24
        c.setFillColor(accent_color)
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(x + 12, y + height/2 - 10, value)

        # Subtitle
        if subtitle:
            c.setFillColor(MEDIUM_GRAY)
            c.setFont("Helvetica", 7)
            c.drawString(x + 12, y + 5, subtitle)

    def draw_section_title(self, c, x, y, number, title):
        """Draw a section title with number badge"""
        # Number badge
        c.setFillColor(ACCENT_GOLD)
        c.circle(x + 12, y + 6, 12, fill=1, stroke=0)
        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + 12, y + 2, str(number))

        # Title
        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 32, y, title)

    def draw_page2(self, c):
        """Draw ASR & Intent Classification results"""
        self.draw_header(c, "ASR & Intent Classification Performance", 2)
        self.draw_footer(c)

        content_top = self.height - 100

        # ===== LEFT COLUMN: ASR =====
        left_x = self.margin + 10
        col_width = (self.width - 3 * self.margin) / 2 - 20

        self.draw_section_title(c, left_x, content_top, 1, "ASR Performance")

        wer = self.metrics['asr']['wer']
        cer = self.metrics['asr']['cer']

        # ASR metric cards
        card_y = content_top - 75
        card_w = col_width / 2 - 10

        self.draw_metric_card(c, left_x, card_y, card_w, 60,
                             "Word Error Rate", f"{wer:.1%}",
                             "Lower is better", wer < 0.25)

        self.draw_metric_card(c, left_x + card_w + 15, card_y, card_w, 60,
                             "Character Error Rate", f"{cer:.1%}",
                             "Lower is better", cer < 0.10)

        # Visual WER bar
        bar_y = card_y - 45
        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_x, bar_y + 20, "WER Visualization")

        # Background bar
        bar_width = col_width - 20
        c.setFillColor(colors.Color(0.9, 0.9, 0.9))
        c.roundRect(left_x, bar_y, bar_width, 15, 4, fill=1, stroke=0)

        # Filled portion
        c.setFillColor(SUCCESS_GREEN if wer < 0.25 else ACCENT_GOLD)
        c.roundRect(left_x, bar_y, bar_width * (1 - wer), 15, 4, fill=1, stroke=0)

        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica", 9)
        c.drawRightString(left_x + bar_width, bar_y - 5, f"{(1-wer)*100:.1f}% words correct")

        # ===== RIGHT COLUMN: Intent Classification =====
        right_x = self.width / 2 + 20

        self.draw_section_title(c, right_x, content_top, 2, "Intent Classification")

        intent = self.metrics['intent_classification']

        # Main accuracy card - larger
        acc_card_y = content_top - 55
        c.setFillColor(SOFT_BLUE)
        c.roundRect(right_x, acc_card_y, col_width, 45, 8, fill=1, stroke=0)
        c.setFillColor(SUCCESS_GREEN)
        c.roundRect(right_x, acc_card_y, 6, 45, 3, fill=1, stroke=0)

        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(right_x + 15, acc_card_y + 28, "Overall Accuracy")
        c.setFillColor(SUCCESS_GREEN)
        c.setFont("Helvetica-Bold", 28)
        c.drawRightString(right_x + col_width - 15, acc_card_y + 12, f"{intent['accuracy']:.1%}")

        # Other metrics in a row
        metrics_y = acc_card_y - 50
        small_card_w = col_width / 3 - 8

        metrics_list = [
            ("Precision", intent['macro_precision']),
            ("Recall", intent['macro_recall']),
            ("F1 Score", intent['macro_f1']),
        ]

        for i, (label, val) in enumerate(metrics_list):
            mx = right_x + i * (small_card_w + 10)
            c.setFillColor(LIGHT_GRAY)
            c.roundRect(mx, metrics_y, small_card_w, 40, 6, fill=1, stroke=0)

            c.setFillColor(DARK_NAVY)
            c.setFont("Helvetica", 9)
            c.drawCentredString(mx + small_card_w/2, metrics_y + 28, label)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(mx + small_card_w/2, metrics_y + 8, f"{val:.1%}")

        # ===== PER-CLASS PERFORMANCE TABLE (FULL WIDTH) =====
        table_y = content_top - 185
        self.draw_section_title(c, left_x, table_y, 3, "Per-Class Intent Performance")

        # Table data
        table_data = [["Intent", "Precision", "Recall", "F1 Score", "Support", "Status"]]
        for intent_name, m in intent['per_class'].items():
            display_name = intent_name.replace('_', ' ').title()
            status = "Excellent" if m['f1'] >= 0.95 else ("Good" if m['f1'] >= 0.80 else "Needs Work")
            table_data.append([
                display_name,
                f"{m['precision']:.2f}",
                f"{m['recall']:.2f}",
                f"{m['f1']:.2f}",
                str(m['support']),
                status
            ])

        col_widths = [150, 80, 70, 70, 60, 90]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DARK_NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))

        table.wrapOn(c, self.width, self.height)
        table.drawOn(c, left_x, table_y - 175)

        # Confusion Matrix Summary (right side of table area)
        cm_x = left_x + 550
        cm_y = table_y - 20

        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cm_x, cm_y, "Key Insights")

        insights = [
            ("Weather Query", "98.5%", "67/68"),
            ("Delete Appointment", "100%", "17/17"),
            ("Update Appointment", "100%", "14/14"),
            ("Get Appointment", "96.3%", "26/27"),
            ("Create Appointment", "93.1%", "27/29"),
        ]

        c.setFont("Helvetica", 9)
        for i, (name, rate, count) in enumerate(insights):
            iy = cm_y - 25 - i * 22
            c.setFillColor(DARK_NAVY)
            c.drawString(cm_x, iy, name)
            c.setFillColor(SUCCESS_GREEN)
            c.drawString(cm_x + 130, iy, rate)
            c.setFillColor(MEDIUM_GRAY)
            c.drawString(cm_x + 175, iy, f"({count})")

    def draw_page3(self, c):
        """Draw Slots, E2E, Latency, and Task Success"""
        self.draw_header(c, "End-to-End Performance & System Metrics", 3)
        self.draw_footer(c)

        content_top = self.height - 100
        col_width = (self.width - 3 * self.margin) / 2 - 20

        # ===== LEFT COLUMN =====
        left_x = self.margin + 10

        # Slot Extraction
        self.draw_section_title(c, left_x, content_top, 4, "Slot/Entity Extraction")

        slot_f1 = self.metrics['slot_extraction']['average_f1']
        self.draw_metric_card(c, left_x, content_top - 55, col_width * 0.55, 45,
                             "Average Slot F1", f"{slot_f1:.1%}",
                             "Entity extraction accuracy", slot_f1 > 0.90)

        # End-to-End Performance
        e2e_y = content_top - 80
        self.draw_section_title(c, left_x, e2e_y, 5, "End-to-End Performance")

        ser = self.metrics['end_to_end']['semantic_error_rate']
        sent_acc = self.metrics['end_to_end']['sentence_accuracy']

        card_w = col_width / 2 - 10
        card_y = e2e_y - 55

        self.draw_metric_card(c, left_x, card_y, card_w, 45,
                             "Semantic Error Rate", f"{ser:.1%}",
                             "Lower is better", ser < 0.20)

        self.draw_metric_card(c, left_x + card_w + 15, card_y, card_w, 45,
                             "Sentence Accuracy", f"{sent_acc:.1%}",
                             "Intent + slots correct", sent_acc > 0.80)

        # Latency Metrics
        lat_y = e2e_y - 115
        self.draw_section_title(c, left_x, lat_y, 6, "Latency Metrics")

        latency = self.metrics['latency']

        # Latency visualization with bars
        bar_y = lat_y - 28
        bar_width = col_width - 50

        # Get NLG latency with fallback for older reports
        nlg_latency = latency.get('nlg', {}).get('avg_ms', 0)

        components = [
            ("ASR", latency['asr']['avg_ms'], colors.Color(0.3, 0.5, 0.7)),
            ("NLU", latency['nlu']['avg_ms'], colors.Color(0.2, 0.6, 0.4)),
            ("NLG", nlg_latency, colors.Color(0.5, 0.3, 0.6)),
            ("Total", latency['total']['avg_ms'], ACCENT_GOLD),
        ]

        max_latency = latency['total']['max_ms']

        for i, (name, avg_ms, bar_color) in enumerate(components):
            by = bar_y - i * 24

            c.setFillColor(DARK_NAVY)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(left_x, by + 5, name)

            # Background
            c.setFillColor(colors.Color(0.92, 0.92, 0.92))
            c.roundRect(left_x + 45, by, bar_width, 16, 4, fill=1, stroke=0)

            # Filled bar (proportional)
            fill_width = (avg_ms / max_latency) * bar_width
            c.setFillColor(bar_color)
            c.roundRect(left_x + 45, by, fill_width, 16, 4, fill=1, stroke=0)

            # Value label
            c.setFillColor(DARK_NAVY)
            c.setFont("Helvetica", 8)
            c.drawRightString(left_x + 45 + bar_width + 40, by + 3, f"{avg_ms:.0f} ms")

        # ===== RIGHT COLUMN: Task Success =====
        right_x = self.width / 2 + 20

        self.draw_section_title(c, right_x, content_top, 7, "Task Success Rate")

        task_success = self.metrics['task_success']
        overall = task_success['overall']

        # Large overall success card
        success_card_y = content_top - 55
        c.setFillColor(SOFT_BLUE)
        c.roundRect(right_x, success_card_y, col_width, 50, 8, fill=1, stroke=0)

        c.setFillColor(SUCCESS_GREEN)
        c.roundRect(right_x, success_card_y, 6, 50, 3, fill=1, stroke=0)

        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_x + 15, success_card_y + 35, "Overall Task Success Rate")

        c.setFillColor(SUCCESS_GREEN)
        c.setFont("Helvetica-Bold", 26)
        c.drawString(right_x + 15, success_card_y + 8, f"{overall:.1%}")

        c.setFillColor(MEDIUM_GRAY)
        c.setFont("Helvetica", 9)
        c.drawRightString(right_x + col_width - 12, success_card_y + 12,
                         f"{int(overall * 161)}/161 tasks")

        # Per-intent success bars
        bars_y = success_card_y - 20
        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(right_x, bars_y, "Success Rate by Intent")

        sorted_intents = sorted(task_success['per_intent'].items(),
                               key=lambda x: x[1]['success_rate'], reverse=True)

        bar_start_y = bars_y - 20
        intent_bar_width = col_width - 95

        for i, (intent, stats) in enumerate(sorted_intents):
            iy = bar_start_y - i * 24
            display_name = intent.replace('_', ' ').title()
            rate = stats['success_rate']

            # Intent name
            c.setFillColor(DARK_NAVY)
            c.setFont("Helvetica", 8)
            c.drawString(right_x, iy + 4, display_name[:18])

            # Background bar
            bar_x = right_x + 110
            c.setFillColor(colors.Color(0.92, 0.92, 0.92))
            c.roundRect(bar_x, iy, intent_bar_width, 14, 3, fill=1, stroke=0)

            # Filled bar
            bar_color = SUCCESS_GREEN if rate >= 0.80 else ACCENT_GOLD
            c.setFillColor(bar_color)
            c.roundRect(bar_x, iy, intent_bar_width * rate, 14, 3, fill=1, stroke=0)

            # Percentage
            c.setFillColor(DARK_NAVY)
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(right_x + col_width, iy + 3, f"{rate:.0%}")

        # ===== KEY FINDINGS BOX (BOTTOM) =====
        findings_y = 50
        findings_height = 55

        c.setFillColor(colors.Color(0.12, 0.18, 0.28, 0.08))
        c.roundRect(self.margin, findings_y, self.width - 2*self.margin, findings_height, 8, fill=1, stroke=0)

        c.setStrokeColor(ACCENT_GOLD)
        c.setLineWidth(2)
        c.roundRect(self.margin, findings_y, self.width - 2*self.margin, findings_height, 8, fill=0, stroke=1)

        c.setFillColor(DARK_NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.margin + 15, findings_y + 38, "Key Findings")

        wer = self.metrics['asr']['wer']
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.Color(0.3, 0.3, 0.35))

        findings = [
            f"WER: {wer:.1%}  |  Intent Accuracy: {self.metrics['intent_classification']['accuracy']:.1%}  |  Slot F1: {slot_f1:.1%}  |  Task Success: {overall:.1%}  |  Avg Latency: {latency['total']['avg_ms']:.0f}ms"
        ]
        c.drawString(self.margin + 15, findings_y + 15, findings[0])


if __name__ == "__main__":
    import os

    project_dir = "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
    metrics_path = os.path.join(project_dir, "tests/evaluation/evaluation_report_20260202_010948.json")
    output_path = os.path.join(project_dir, "tests/evaluation/evaluation_report_20260202_010948.pdf")

    pdf = PresentationPDF(output_path, metrics_path)
    pdf.create()
