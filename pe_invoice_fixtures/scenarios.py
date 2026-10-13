# -*- coding: utf-8 -*-
"""
Pool of daily-batch scenario templates. Each builder takes an output
directory and a reference date (the day the batch is generated), and
returns a dict describing what it built — used both for the email body
and for the rotation log that keeps the daily batch from repeating itself.

To add a new template: write a build_xxx(outdir, today) function matching
this signature and add its id to SCENARIOS at the bottom.
"""
import os
from datetime import timedelta
from reportlab.lib import colors
from reportlab.lib.units import inch

from lib import (
    FUNDS, GP_NAME, FUND_CONTACT_NAME, FUND_CONTACT_EMAIL,
    money, money_cur, build_invoice_pdf, make_eml, us_pay, uk_pay, eur_pay,
)


def _fmt(d):
    return d.strftime("%B %-d, %Y")


def _due(d, days=30):
    return _fmt(d + timedelta(days=days))


# ---------------------------------------------------------------------------
def build_ashcroft_whitmore(outdir, today, seq):
    accent = colors.HexColor("#4E6E58")
    inv_no = f"AWE-2026-{3400 + seq}"
    firm = {
        "name": "Ashcroft Whitmore Engineering LLC",
        "addr_lines": ["4400 Post Oak Parkway, Suite 1800", "Houston, TX 77027",
                       "Tel: (713) 555-0392 &nbsp;&nbsp; Fed. Tax ID: 76-2298114"],
        "tagline": "Independent engineering, technical &amp; environmental due diligence for infrastructure assets",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": us_pay("Gulf Coast National Bank", "Houston, TX", "113000023", f"{3400+seq}-7742-19", "GCNBUS55", "Ashcroft Whitmore Engineering LLC"),
        "notes": f"For billing questions, please contact accounts@ashcroftwhitmore.com, referencing invoice {inv_no} and project code PHW-2026-04.",
        "footer_note": "This report and the underlying site work were prepared for the sole use of Meridian Infrastructure Partners I, L.P. and its lenders in connection with the Prairie Horizon Wind Project.",
    }
    fund = FUNDS["MIP-I"]
    matter_lines = ["ENGAGEMENT", "Independent Engineer Support &mdash;", "Ongoing Monitoring",
                    "Project: Prairie Horizon Wind Project", "Project Code: PHW-2026-04"]
    columns = ["Service", "Description", "Amount"]
    col_widths = [1.55 * inch, 3.75 * inch, 1.0 * inch]
    base = 5800.00 + (seq % 5) * 240
    rows = [["Site Monitoring", "Monthly site monitoring visit and progress review", money(base)],
            ["Reporting", "Monthly engineer's report for lender syndication group", money(2100.00 + (seq % 3) * 90)]]
    subtotal = base + 2100.00 + (seq % 3) * 90
    totals_rows = [("Subtotal", money(subtotal), False), ("TOTAL DUE", money(subtotal), True)]
    pdf_path = os.path.join(outdir, f"AshcroftWhitmore_MIPI_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows, align_right_from=2)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="Accounts, Ashcroft Whitmore Engineering", from_email="accounts@ashcroftwhitmore.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Invoice {inv_no} — Prairie Horizon Wind Project (PHW-2026-04)",
              body_text=f"Dear {FUND_CONTACT_NAME},\n\nAttached is invoice {inv_no} for monthly engineer support on Prairie Horizon, totalling {money(subtotal)}.\n\nBest regards,\nAccounts\nAshcroft Whitmore Engineering LLC\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "ashcroft_whitmore", "fund": "MIP-I", "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"USD {subtotal:,.2f}", "kind": "standard", "pdf": pdf_path, "eml": eml_path,
            "watch": "Standard single-fund USD invoice, matches MIP-I's own base currency — baseline case."}


# ---------------------------------------------------------------------------
def build_beacon_diligence(outdir, today, seq):
    accent = colors.HexColor("#A64B2A")
    inv_no = f"BDG-2026-{2300 + seq}"
    firm = {
        "name": "Beacon Diligence Group LLC",
        "addr_lines": ["1330 Avenue of the Americas, 23rd Floor", "New York, NY 10019",
                       "Tel: (212) 555-0871 &nbsp;&nbsp; Fed. Tax ID: 81-3345621"],
        "tagline": "Commercial, operational &amp; IT due diligence for private equity transactions",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": us_pay("Hudson Yards National Bank", "New York, NY", "021000322", f"{2300+seq}-5581-90", "HYNBUS31", "Beacon Diligence Group LLC"),
        "notes": f"Please reference invoice {inv_no} with your remittance. For billing questions, contact billing@beacondiligence.com.",
        "footer_note": "This engagement is a pre-LOI commercial and operational diligence exercise conducted under the internal project codename referenced above.",
    }
    fund = FUNDS["MGE-I"]
    matter_lines = ["ENGAGEMENT", "Project Copper &mdash; Commercial &amp;", "Operational Due Diligence",
                    "Target Company: Under NDA &mdash; pre-LOI", "Engagement Lead: K. Marsh, Partner"]
    columns = ["Service", "Description", "Amount"]
    col_widths = [1.55 * inch, 3.75 * inch, 1.0 * inch]
    base = 11200.00 + (seq % 4) * 650
    rows = [["Commercial Diligence", "Continued customer and end-market analysis", money(base)],
            ["Reporting", "Interim findings memorandum for deal team", money(2400.00)]]
    subtotal = base + 2400.00
    totals_rows = [("Subtotal", money(subtotal), False), ("TOTAL DUE", money(subtotal), True)]
    pdf_path = os.path.join(outdir, f"BeaconDiligence_MGEI_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows, align_right_from=2)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="Billing, Beacon Diligence Group", from_email="billing@beacondiligence.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Invoice {inv_no} — Project Copper Commercial Diligence",
              body_text=f"Dear {FUND_CONTACT_NAME},\n\nAttached is invoice {inv_no} for continued diligence work on Project Copper, totalling {money(subtotal)}.\n\nBest regards,\nK. Marsh\nPartner\nBeacon Diligence Group LLC\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "beacon_diligence", "fund": "MGE-I", "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"USD {subtotal:,.2f}", "kind": "standard", "pdf": pdf_path, "eml": eml_path,
            "watch": "Standard single-fund USD invoice against MGE-I's GBP base — currency mismatch, deal-linked (Project Copper)."}


# ---------------------------------------------------------------------------
def build_ridgeline_valuation(outdir, today, seq):
    accent = colors.HexColor("#B8860B")
    fund_code = ["MGE-I", "MCP-III", "MCO-I"][seq % 3]
    fund = FUNDS[fund_code]
    inv_no = f"RVP-2026-{150 + seq}"
    firm = {
        "name": "Ridgeline Valuation Partners LLC",
        "addr_lines": ["100 Congress Avenue, Suite 2000", "Austin, TX 78701", "Tel: (512) 555-0654"],
        "tagline": "Independent valuation &amp; financial advisory services",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": uk_pay("Barclays Bank PLC", "Ridgeline Valuation Partners LLC — UK Engagements",
                           "20-45-71", f"{150+seq:05d}071", f"GB33 BARC 2045 71{150+seq:05d}", "BARCGB22"),
        "notes": f"For questions regarding this invoice, please contact billing@ridgelinevaluation.com, referencing invoice {inv_no}.",
        "footer_note": "Valuations were prepared solely for financial reporting purposes in accordance with ASC 820. Amounts are stated in Pounds Sterling (GBP).",
    }
    matter_lines = ["ENGAGEMENT", "Quarterly Portfolio Valuation", f"Engagement Lead: T. Kowalski, ASA"]
    columns = ["Service", "Description", "Amount"]
    col_widths = [1.55 * inch, 3.75 * inch, 1.0 * inch]
    base = 8600.00 + (seq % 5) * 320
    rows = [["Valuation", "Fair value estimate, portfolio investments — discounted cash flow method", money_cur(base, "£")],
            ["Reporting", "Valuation committee memorandum", money_cur(2100.00, "£")]]
    subtotal = base + 2100.00
    totals_rows = [("Subtotal", money_cur(subtotal, "£"), False), ("TOTAL DUE", money_cur(subtotal, "£"), True)]
    pdf_path = os.path.join(outdir, f"Ridgeline_{fund_code}_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows, align_right_from=2)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="T. Kowalski, Ridgeline Valuation Partners", from_email="tkowalski@ridgelinevaluation.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Invoice {inv_no} — Quarterly Portfolio Valuation, {fund_code}",
              body_text=f"Dear {FUND_CONTACT_NAME},\n\nAttached is invoice {inv_no} for quarterly valuation work, totalling {money_cur(subtotal, chr(163))}.\n\nBest regards,\nT. Kowalski\nRidgeline Valuation Partners LLC\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "ridgeline_valuation", "fund": fund_code, "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"GBP {subtotal:,.2f}", "kind": "standard", "pdf": pdf_path, "eml": eml_path,
            "watch": f"Standard single-fund GBP invoice, matches {fund_code}'s own base currency — baseline case."}


# ---------------------------------------------------------------------------
def build_aldergate_prentice(outdir, today, seq):
    accent = colors.HexColor("#8C3B2E")
    inv_no = f"APW-2026-{91200 + seq}"
    firm = {
        "name": "Aldergate Prentice Wealth Advisors",
        "addr_lines": ["88 Wood Street", "London EC2V 7RS, United Kingdom", "Tel: +44 20 7100 8800"],
        "tagline": "Private wealth advisory for high net worth families",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": uk_pay("HSBC UK Bank PLC", "Aldergate Prentice Wealth Advisors LLP", "40-27-15", f"{91200+seq}09", f"GB47 HBUK 4027 15{91200+seq}09", "HBUKGB4B"),
        "notes": f"For billing questions, please contact billing@aldergateprentice.com, referencing invoice {inv_no}.",
        "footer_note": "This invoice reflects private wealth advisory services rendered pursuant to our engagement letter. Amounts are stated in Pounds Sterling (GBP).",
    }
    fund = FUNDS["MWP"]
    matter_lines = ["SERVICE PERIOD", "Monthly Private Wealth Advisory", "Client Ref: MWP-2024"]
    columns = ["Service", "Description", "Amount"]
    col_widths = [1.55 * inch, 3.75 * inch, 1.0 * inch]
    base = 7800.00 + (seq % 4) * 300
    rows = [["Investment Advisory", "Monthly investment advisory and portfolio review", money_cur(base, "£")]]
    subtotal = base
    totals_rows = [("Subtotal", money_cur(subtotal, "£"), False), ("TOTAL DUE", money_cur(subtotal, "£"), True)]
    pdf_path = os.path.join(outdir, f"AldergatePrentice_MWP_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows, align_right_from=2)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="Billing, Aldergate Prentice", from_email="billing@aldergateprentice.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Invoice {inv_no} — Monthly Private Wealth Advisory",
              body_text=f"Dear {FUND_CONTACT_NAME},\n\nAttached is invoice {inv_no}, totalling {money_cur(subtotal, chr(163))}.\n\nBest regards,\nM. Prentice\nDirector\nAldergate Prentice Wealth Advisors\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "aldergate_prentice", "fund": "MWP", "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"GBP {subtotal:,.2f}", "kind": "standard", "pdf": pdf_path, "eml": eml_path,
            "watch": "Standard single-fund GBP invoice, matches MWP's own base currency — baseline case."}


# ---------------------------------------------------------------------------
def build_thackeray_trap(outdir, today, seq):
    accent = colors.HexColor("#6B4226")
    inv_no = f"THK-2026-{500 + seq}"
    firm = {
        "name": "Thackeray Capital Advisors LLC",
        "addr_lines": ["650 Fifth Avenue, 29th Floor", "New York, NY 10019", "Tel: (212) 555-0633"],
        "tagline": "Private fund placement &amp; investor advisory services",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": us_pay("Continental Harbor Bank", "New York, NY", "026015052", f"{500+seq}-7741-88", "CHBKUS44", "Thackeray Capital Advisors LLC"),
        "notes": f"Please reference invoice {inv_no} with your remittance. For billing questions, contact billing@thackeraycapital.com.",
        "footer_note": "This invoice covers placement and investor introduction services in connection with the fundraising of Meridian Capital Partners IV, L.P. This engagement is unrelated to Meridian Capital Partners III, L.P.'s existing portfolio or operations.",
    }
    fund = FUNDS["MCP-III"]  # deliberately mis-addressed — this is Fund IV's cost, not MCP-III's
    matter_lines = ["ENGAGEMENT", "Placement &amp; Investor Introduction Services",
                    "Meridian Capital Partners IV, L.P. &mdash; Fundraising", "Engagement Lead: W. Castellane, Partner"]
    columns = ["Service", "Description", "Amount"]
    col_widths = [1.55 * inch, 3.75 * inch, 1.0 * inch]
    base = 28000.00 + (seq % 4) * 1500
    rows = [["Investor Outreach", "Investor identification &amp; outreach, Fund IV", money(base)],
            ["Closing Support", "Closing coordination and documentation support, Fund IV", money(18500.00)]]
    subtotal = base + 18500.00
    totals_rows = [("Subtotal", money(subtotal), False), ("TOTAL DUE", money(subtotal), True)]
    pdf_path = os.path.join(outdir, f"Thackeray_MisAddressed_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows, align_right_from=2)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="Billing, Thackeray Capital Advisors", from_email="billing@thackeraycapital.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Invoice {inv_no} — Fund IV Placement Services",
              body_text=f"Dear {FUND_CONTACT_NAME},\n\nAttached is invoice {inv_no} for Fund IV placement work, totalling {money(subtotal)}.\n\nBest regards,\nW. Castellane\nThackeray Capital Advisors LLC\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "thackeray_trap", "fund": "MCP-III", "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"USD {subtotal:,.2f}", "kind": "trap", "pdf": pdf_path, "eml": eml_path,
            "watch": "CODING TRAP: billed to MCP-III but the content is Fund IV fundraising — should be rejected as a fund cost entirely and redirected to the GP/ManCo."}


# ---------------------------------------------------------------------------
def build_ashford_kane_multigl(outdir, today, seq):
    accent = colors.HexColor("#1F3A5F")
    inv_no = f"AK-2026-{5600 + seq}"
    firm = {
        "name": "Ashford Kane LLP",
        "addr_lines": ["555 Fifth Avenue, 38th Floor", "New York, NY 10017", "Tel: (212) 555-0147"],
        "tagline": "Counsel to sponsors, funds and financial institutions",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": us_pay("First Meridian Trust Bank, N.A.", "New York, NY", "021909651", f"{5600+seq}-0098-2231", "FMTBUS33", "Ashford Kane LLP Client Trust / Operating Account"),
        "notes": f"Please reference invoice {inv_no} with your remittance. This invoice spans two matters, broken out below; please code accordingly rather than as a single line item.",
        "footer_note": "This invoice reflects fees for legal services rendered across the two matters referenced below. Confidential — attorney work product.",
    }
    fund = FUNDS["MCP-III"]
    matter_lines = ["MATTERS ON THIS INVOICE", "(1) Project Halyard &mdash; Matter No. HAL-2026-0031",
                    "(2) General Fund Governance &mdash; Matter No. 08812-0015", "Responsible Partner: S. Whitcombe"]
    columns = ["Date", "Timekeeper", "Description", "Hrs", "Rate", "Amount"]
    col_widths = [0.75 * inch, 1.0 * inch, 2.48 * inch, 0.38 * inch, 0.75 * inch, 0.84 * inch]
    h_hrs = 2.4 + (seq % 3) * 0.4
    halyard_rows = [["", "S. Whitcombe, Partner", "Continued negotiation support on Project Halyard SPA terms", f"{h_hrs:.1f}", "1,450.00", money(h_hrs * 1450)]]
    gov_rows = [["", "M. Reyes, Associate", "General fund governance and investor onboarding document review", "1.8", "795.00", money(1.8 * 795)]]
    halyard_fees = h_hrs * 1450
    gov_fees = 1.8 * 795
    all_rows = (
        [["", "", "<b>MATTER (1) — PROJECT HALYARD — DEAL-SPECIFIC — HAL-2026-0031</b>", "", "", ""]]
        + halyard_rows
        + [["", "", "<b>Matter (1) Subtotal</b>", "", "", f"<b>{money(halyard_fees)}</b>"]]
        + [["", "", "<b>MATTER (2) — GENERAL FUND GOVERNANCE — NOT DEAL-LINKED — 08812-0015</b>", "", "", ""]]
        + gov_rows
        + [["", "", "<b>Matter (2) Subtotal</b>", "", "", f"<b>{money(gov_fees)}</b>"]]
    )
    subtotal = halyard_fees + gov_fees
    totals_rows = [("Matter (1) Project Halyard", money(halyard_fees), False),
                   ("Matter (2) General Fund Governance", money(gov_fees), False),
                   ("TOTAL DUE", money(subtotal), True)]
    pdf_path = os.path.join(outdir, f"AshfordKane_MultiGL_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, all_rows, col_widths, totals_rows, align_right_from=3)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="Client Accounting, Ashford Kane LLP", from_email="billing@ashfordkane.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Ashford Kane LLP Invoice {inv_no} — Two Matters",
              body_text=f"Dear {FUND_CONTACT_NAME},\n\nAttached is invoice {inv_no}, covering Project Halyard and general fund governance work, totalling {money(subtotal)}.\n\nBest regards,\nClient Accounting\nAshford Kane LLP\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "ashford_kane_multigl", "fund": "MCP-III", "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"USD {subtotal:,.2f}", "kind": "trap", "pdf": pdf_path, "eml": eml_path,
            "watch": f"CODING TEST: one invoice, one fund, two GL lines — Matter (1) ${halyard_fees:,.2f} deal-specific vs. Matter (2) ${gov_fees:,.2f} general governance, within MCP-III only."}


# ---------------------------------------------------------------------------
def build_anchorpoint_nav_cutoff(outdir, today, seq):
    accent = colors.HexColor("#2E6E5E")
    inv_no = f"AFS-{100280 + seq}"
    # invoice lands a few days into the new month but covers the prior month
    prior_month_end = today.replace(day=1) - timedelta(days=1)
    prior_month_name = prior_month_end.strftime("%B %Y")
    firm = {
        "name": "Anchorpoint Fund Services LLC",
        "addr_lines": ["200 Liberty Street, 4th Floor", "Jersey City, NJ 07302", "Tel: (201) 555-0432"],
        "tagline": "Private capital fund administration &amp; investor services",
        "invoice_no": inv_no, "invoice_date": _fmt(today), "due_date": _due(today), "terms": "Net 30", "accent": accent,
        "payment": uk_pay("Barclays Bank PLC", "Anchorpoint Fund Services Ltd — GBP Client Account", "20-45-71", f"{100280+seq}71", f"GB14 BARC 2045 71{100280+seq}71", "BARCGB22"),
        "notes": f"Please reference invoice {inv_no} with your remittance. Questions: L. Bergstrom, lbergstrom@anchorpointfs.com.",
        "footer_note": (f"Service Period: {prior_month_name}. Although this invoice is dated {_fmt(today)}, the services below relate entirely to the "
                         f"{prior_month_name} period and should be accrued back to that period for NAV and financial reporting purposes, notwithstanding the invoice date."),
    }
    fund = FUNDS["MGE-I"]
    matter_lines = ["SERVICE PERIOD", prior_month_name, f"Client Ref: {fund['code']}-2021"]
    columns = ["Service", "Description", "Amount"]
    col_widths = [1.55 * inch, 3.75 * inch, 1.0 * inch]
    base = 11800.00 + (seq % 4) * 450
    rows = [["Core Administration", f"Monthly fund accounting and NAV calculation — {prior_month_name}", money_cur(base, "£")],
            ["Investor Reporting", "Monthly investor statements", money_cur(3600.00, "£")]]
    subtotal = base + 3600.00
    totals_rows = [("Subtotal", money_cur(subtotal, "£"), False), ("TOTAL DUE", money_cur(subtotal, "£"), True)]
    pdf_path = os.path.join(outdir, f"Anchorpoint_NAVCutoff_{inv_no}.pdf")
    build_invoice_pdf(pdf_path, firm, fund, matter_lines, columns, rows, col_widths, totals_rows, align_right_from=2)
    eml_path = pdf_path.replace(".pdf", "_email.eml")
    make_eml(eml_path, from_name="L. Bergstrom, Anchorpoint Fund Services", from_email="lbergstrom@anchorpointfs.com",
              to_name=FUND_CONTACT_NAME, to_email=FUND_CONTACT_EMAIL,
              subject=f"Invoice {inv_no} — {prior_month_name} Fund Administration (dated {_fmt(today)})",
              body_text=f"Hi {FUND_CONTACT_NAME.split()[0]},\n\nAttached is invoice {inv_no} for {prior_month_name} fund administration, totalling {money_cur(subtotal, chr(163))}. Everything here relates to {prior_month_name} even though the invoice is dated today.\n\nBest,\nL. Bergstrom\nAnchorpoint Fund Services LLC\n",
              attachment_path=pdf_path, attachment_name=os.path.basename(pdf_path), send_date=today)
    return {"id": "anchorpoint_nav_cutoff", "fund": "MGE-I", "vendor": firm["name"], "invoice_no": inv_no,
            "amount": f"GBP {subtotal:,.2f}", "kind": "trap", "pdf": pdf_path, "eml": eml_path,
            "watch": f"CODING TEST: dated {_fmt(today)} but every line item is {prior_month_name} service — should accrue to the prior month, not the invoice date's period."}


SCENARIOS = {
    "ashcroft_whitmore": build_ashcroft_whitmore,
    "beacon_diligence": build_beacon_diligence,
    "ridgeline_valuation": build_ridgeline_valuation,
    "aldergate_prentice": build_aldergate_prentice,
    "thackeray_trap": build_thackeray_trap,
    "ashford_kane_multigl": build_ashford_kane_multigl,
    "anchorpoint_nav_cutoff": build_anchorpoint_nav_cutoff,
}
