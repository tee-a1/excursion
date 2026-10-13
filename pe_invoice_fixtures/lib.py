# -*- coding: utf-8 -*-
"""
Core PDF/email generation helpers + reference data for the daily AP
stress-test batch. All company names (except the fund itself, which mirrors
the user's real system) are fabricated for software testing purposes only.

This module is the durable home for everything the daily routine needs —
it lives in git specifically because the sandbox's /tmp scratchpad does not
survive a container reset between routine firings, and a daily job that
fires for weeks needs its generator code to still be here tomorrow.
"""
import os
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

FUND_ADDR = ["1201 Harbor Boulevard, Suite 2200", "San Francisco, CA 94111"]
FUND_CONTACT_NAME = "David Chen"
FUND_CONTACT_TITLE = "Group Fund Controller"
FUND_CONTACT_EMAIL = "dchen@meridiancapital.com"
GP_NAME = "Meridian Capital Group"

# Real fund list (ex-coinvests), with base currency per the user's system screenshot.
FUNDS = {
    "MWP":     {"name": "Meridian Wealth Preservation Fund, L.P.", "code": "MWP",     "strategy": "Private Wealth",   "base_ccy": "GBP"},
    "MCO-I":   {"name": "Meridian Credit Opportunities I, L.P.",   "code": "MCO-I",   "strategy": "Private Credit",   "base_ccy": "GBP"},
    "MCP-III": {"name": "Meridian Capital Partners III, L.P.",     "code": "MCP-III", "strategy": "Private Equity",   "base_ccy": "GBP"},
    "MGE-I":   {"name": "Meridian Growth Equity I, L.P.",          "code": "MGE-I",   "strategy": "Private Equity",   "base_ccy": "GBP"},
    "MIP-I":   {"name": "Meridian Infrastructure Partners I, L.P.", "code": "MIP-I",  "strategy": "Infrastructure",   "base_ccy": "USD"},
}

styles = getSampleStyleSheet()


def money(x):
    return f"${x:,.2f}"


def money_neg(x):
    return f"(${x:,.2f})"


def money_cur(x, symbol, euro_style=False):
    if euro_style:
        s = f"{x:,.2f}".translate(str.maketrans({",": "X", ".": ","})).replace("X", ".")
        return f"{symbol}{s}"
    return f"{symbol}{x:,.2f}"


def build_styles(accent):
    s = {}
    s["firm_name"] = ParagraphStyle("firm_name", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=17, textColor=accent, leading=20)
    s["firm_sub"] = ParagraphStyle("firm_sub", parent=styles["Normal"], fontName="Helvetica", fontSize=8.3, textColor=colors.HexColor("#444444"), leading=11)
    s["invoice_title"] = ParagraphStyle("invoice_title", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=20, textColor=colors.HexColor("#222222"), alignment=TA_RIGHT, leading=24)
    s["meta_label"] = ParagraphStyle("meta_label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#555555"), alignment=TA_RIGHT)
    s["meta_value"] = ParagraphStyle("meta_value", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#111111"), alignment=TA_RIGHT)
    s["section_head"] = ParagraphStyle("section_head", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=accent, spaceBefore=2, spaceAfter=4)
    s["body"] = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=12.5, textColor=colors.HexColor("#222222"))
    s["body_small"] = ParagraphStyle("body_small", parent=styles["Normal"], fontName="Helvetica", fontSize=7.8, leading=10.5, textColor=colors.HexColor("#555555"))
    s["table_cell"] = ParagraphStyle("table_cell", parent=styles["Normal"], fontName="Helvetica", fontSize=8.3, leading=11, textColor=colors.HexColor("#222222"))
    s["table_cell_r"] = ParagraphStyle("table_cell_r", parent=s["table_cell"], alignment=TA_RIGHT)
    s["table_head"] = ParagraphStyle("table_head", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.3, textColor=colors.white)
    s["table_head_r"] = ParagraphStyle("table_head_r", parent=s["table_head"], alignment=TA_RIGHT)
    s["total_label"] = ParagraphStyle("total_label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, alignment=TA_RIGHT, textColor=colors.HexColor("#111111"))
    s["total_value"] = ParagraphStyle("total_value", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, alignment=TA_RIGHT, textColor=accent)
    s["footer"] = ParagraphStyle("footer", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7.5, textColor=colors.HexColor("#777777"), leading=10)
    return s


def header_block(c, firm, accent, s, doc_title="INVOICE", meta_rows=None):
    left = [Paragraph(firm["name"], s["firm_name"])]
    for line in firm["addr_lines"]:
        left.append(Paragraph(line, s["firm_sub"]))
    left.append(Spacer(1, 2))
    left.append(Paragraph(firm["tagline"], s["firm_sub"]))

    right = [Paragraph(doc_title, s["invoice_title"])]
    if meta_rows is None:
        meta_rows = [("Invoice No.", firm["invoice_no"]), ("Invoice Date", firm["invoice_date"]),
                     ("Due Date", firm["due_date"]), ("Terms", firm["terms"])]
    meta_tbl_data = [[Paragraph(k, s["meta_label"]), Paragraph(v, s["meta_value"])] for k, v in meta_rows]
    max_label_len = max((len(k) for k, _ in meta_rows), default=12)
    right_total = 3.3 * inch if max_label_len > 14 else 2.7 * inch
    label_w = max_label_len * s["meta_label"].fontSize * 0.78
    label_w = min(max(label_w, 70), right_total - 84)
    meta_tbl = Table(meta_tbl_data, colWidths=[label_w, right_total - label_w])
    meta_tbl.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("ALIGN", (0, 0), (-1, -1), "RIGHT")]))
    right.append(Spacer(1, 6))
    right.append(meta_tbl)

    left_total = 6.6 * inch - right_total
    header_tbl = Table([[left, right]], colWidths=[left_total, right_total])
    header_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return header_tbl


def bill_to_block(s, fund, matter_lines=None, care_of=GP_NAME):
    rows = [Paragraph("BILL TO", s["section_head"])]
    rows.append(Paragraph(f"<b>{fund['name']}</b>", s["body"]))
    if care_of:
        rows.append(Paragraph(f"c/o {care_of}", s["body"]))
    for line in FUND_ADDR:
        rows.append(Paragraph(line, s["body"]))
    rows.append(Paragraph(f"Attn: {FUND_CONTACT_NAME}, {FUND_CONTACT_TITLE}", s["body"]))
    rows.append(Paragraph(FUND_CONTACT_EMAIL, s["body"]))
    code_line = fund.get("code_line") or f"Fund Code: {fund['code']} &nbsp;&nbsp; Strategy: {fund['strategy']}"
    rows.append(Paragraph(code_line, s["body_small"]))
    left = rows
    right = []
    if matter_lines:
        right.append(Paragraph(matter_lines[0], s["section_head"]))
        for line in matter_lines[1:]:
            right.append(Paragraph(line, s["body"]))
    tbl = Table([[left, right]], colWidths=[3.9 * inch, 2.7 * inch])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return tbl


def line_items_table(columns, rows, col_widths, accent, s, align_right_from=1):
    header = [Paragraph(c, s["table_head_r"] if i >= align_right_from else s["table_head"]) for i, c in enumerate(columns)]
    data = [header]
    for row in rows:
        data.append([Paragraph(str(cell), s["table_cell_r"] if i >= align_right_from else s["table_cell"]) for i, cell in enumerate(row)])
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), accent), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, accent),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F6F8")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#DDDDDD")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    tbl.setStyle(TableStyle(style))
    return tbl


def totals_block(rows, accent, s, grand_label="TOTAL DUE"):
    data = []
    for label, val, bold in rows[:-1]:
        data.append([
            Paragraph(label, s["body"] if not bold else ParagraphStyle("b", parent=s["body"], fontName="Helvetica-Bold")),
            Paragraph(val, ParagraphStyle("v", parent=s["body"], alignment=TA_RIGHT, fontName="Helvetica-Bold" if bold else "Helvetica")),
        ])
    tbl = None
    if data:
        tbl = Table(data, colWidths=[1.9 * inch, 1.5 * inch])
        tbl.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    grand_label_, grand_val, _ = rows[-1]
    grand = Table([[Paragraph(grand_label_, s["total_label"]), Paragraph(grand_val, s["total_value"])]], colWidths=[1.9 * inch, 1.5 * inch])
    grand.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1, accent), ("TOPPADDING", (0, 0), (-1, -1), 5)]))
    wrapper_rows = ([[tbl]] if tbl is not None else []) + [[grand]]
    wrapper = Table(wrapper_rows, colWidths=[3.4 * inch])
    wrapper.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    outer = Table([[Spacer(1, 1), wrapper]], colWidths=[3.3 * inch, 3.4 * inch])
    outer.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return outer


def payment_and_footer(firm, s, accent, show_payment=True):
    story = [Spacer(1, 14), HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#DDDDDD")), Spacer(1, 8)]
    if not show_payment:
        story.append(Paragraph(firm.get("notes", ""), s["body_small"]))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#EEEEEE")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(firm["footer_note"], s["footer"]))
        return story
    story.append(Paragraph("PAYMENT INSTRUCTIONS", s["section_head"]))
    pay = firm["payment"]
    if pay.get("style") == "iban":
        pay_lines = (f"Wire Transfer &mdash; {pay['bank']}, {pay['bank_addr']}<br/>IBAN: {pay['iban']} &nbsp;&nbsp; BIC/SWIFT: {pay['swift']}<br/>"
                      f"Account Name: {pay['account_name']} &nbsp;&nbsp; Reference: {firm['invoice_no']}")
    elif pay.get("style") == "uk":
        pay_lines = (f"Wire Transfer &mdash; {pay['bank']}, {pay['bank_addr']}<br/>Sort Code: {pay['sort_code']} &nbsp;&nbsp; Account No.: {pay['account']} "
                      f"&nbsp;&nbsp; IBAN: {pay['iban']} &nbsp;&nbsp; SWIFT: {pay['swift']}<br/>Account Name: {pay['account_name']} &nbsp;&nbsp; Reference: {firm['invoice_no']}")
    else:
        pay_lines = (f"Wire Transfer &mdash; {pay['bank']}, {pay['bank_addr']}<br/>ABA / Routing: {pay['routing']} &nbsp;&nbsp; Account No.: {pay['account']} "
                      f"&nbsp;&nbsp; SWIFT: {pay['swift']}<br/>Account Name: {pay['account_name']} &nbsp;&nbsp; Reference: {firm['invoice_no']}")
    story.append(Paragraph(pay_lines, s["body_small"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(firm.get("notes", ""), s["body_small"]))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#EEEEEE")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(firm["footer_note"], s["footer"]))
    return story


def overdue_banner(text, s):
    p = Paragraph(text, ParagraphStyle("banner", parent=s["body"], fontName="Helvetica-Bold", fontSize=10.5, textColor=colors.white, alignment=TA_LEFT))
    tbl = Table([[p]], colWidths=[6.6 * inch])
    tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#B3261E")), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    return tbl


def build_invoice_pdf(path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows,
                       align_right_from=1, doc_title="INVOICE", meta_rows=None, banner_text=None,
                       show_payment=True, care_of=GP_NAME):
    accent = firm["accent"]
    s = build_styles(accent)
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.55 * inch, bottomMargin=0.6 * inch,
                             leftMargin=0.65 * inch, rightMargin=0.65 * inch,
                             title=f"{doc_title.title()} {firm['invoice_no']} - {firm['name']}", author=firm["name"])
    story = [header_block(doc, firm, accent, s, doc_title=doc_title, meta_rows=meta_rows), Spacer(1, 10)]
    if banner_text:
        story.append(overdue_banner(banner_text, s))
        story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.4, color=accent))
    story.append(Spacer(1, 10))
    story.append(bill_to_block(s, fund, matter_lines, care_of=care_of))
    story.append(Spacer(1, 12))
    story.append(line_items_table(columns, rows, col_widths, accent, s, align_right_from))
    story.append(Spacer(1, 10))
    story.append(totals_block(totals_rows, accent, s))
    story.extend(payment_and_footer(firm, s, accent, show_payment=show_payment))
    doc.build(story)


def make_eml(path, *, from_name, from_email, to_name, to_email, cc=None, subject, body_text,
             attachment_path, attachment_name, send_date):
    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = f"{to_name} <{to_email}>"
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg["Date"] = format_datetime(send_date)
    msg["Message-ID"] = make_msgid(domain=from_email.split("@")[-1])
    msg.set_content(body_text)
    with open(attachment_path, "rb") as f:
        data = f.read()
    msg.add_attachment(data, maintype="application", subtype="pdf", filename=attachment_name)
    with open(path, "wb") as f:
        f.write(bytes(msg))


def uk_pay(bank, account_name, sort_code, account, iban, swift):
    return {"bank": bank, "bank_addr": "London, United Kingdom", "sort_code": sort_code,
            "account": account, "iban": iban, "swift": swift, "account_name": account_name, "style": "uk"}


def eur_pay(bank, bank_addr, iban, swift, account_name):
    return {"bank": bank, "bank_addr": bank_addr, "iban": iban, "swift": swift, "account_name": account_name, "style": "iban"}


def us_pay(bank, bank_addr, routing, account, swift, account_name):
    return {"bank": bank, "bank_addr": bank_addr, "routing": routing, "account": account, "swift": swift, "account_name": account_name}
