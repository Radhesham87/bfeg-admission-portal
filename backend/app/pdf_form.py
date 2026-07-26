"""Renders a submitted application as a PDF that mirrors the printed
Government of Maharashtra / State CET Cell application form.

Pages produced:
  1  NEET-UG details, subject marks, personal information, permanent address
  2  Reservation
  3  SSC and HSC qualification
  4  Parallel reservation, application fees
  5  Required documents checklist + signature block

The Marathi agreement pages of the original booklet carry no candidate data,
so they are not regenerated here; BFEG prints those once and has them signed.
"""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph,
    Spacer, Table, TableStyle,
)

from .fields import (BARCODE_DOCUMENTS, DOCUMENTS, MANDATORY_DOCUMENTS,
                     OPTIONAL_DOCUMENTS, doc_parts)

# ---------------------------------------------------------------- palette
NAVY = colors.HexColor("#1F3864")
BLUE = colors.HexColor("#1F5C99")
BAR = colors.HexColor("#E8E8E8")
LINE = colors.HexColor("#9A9A9A")
SOFT = colors.HexColor("#C8C8C8")

ASSETS = Path(__file__).resolve().parent / "assets"
EMBLEM = ASSETS / "emblem.png"          # Government of India emblem
CET_LOGO = ASSETS / "cet_logo.png"      # State CET Cell logo
AGREEMENT = ASSETS / "agreement_pages.pdf"   # Marathi terms pages of the booklet

PAGE_W, PAGE_H = A4
MARGIN = 12 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------- styles
S_TITLE = ParagraphStyle("t", fontName="Helvetica", fontSize=15, leading=18,
                         textColor=NAVY, alignment=TA_CENTER)
S_SUB = ParagraphStyle("s", fontName="Helvetica", fontSize=10.5, leading=13,
                       textColor=BLUE, alignment=TA_CENTER)
S_BAR = ParagraphStyle("b", fontName="Helvetica-Bold", fontSize=9.5, leading=12,
                       textColor=colors.black)
S_LAB = ParagraphStyle("l", fontName="Helvetica", fontSize=8, leading=10.5,
                       textColor=colors.HexColor("#222222"))
S_VAL = ParagraphStyle("v", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                       textColor=colors.black)
S_TH = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9, leading=11)
S_SMALL = ParagraphStyle("sm", fontName="Helvetica", fontSize=7, leading=9,
                         textColor=colors.HexColor("#555555"))
S_FOOT = ParagraphStyle("f", fontName="Helvetica", fontSize=8.5, leading=11)


def _v(data, key):
    """Value for a field key, or a blank underline when unanswered."""
    val = (data or {}).get(key, "")
    val = str(val).strip() if val is not None else ""
    return val if val else "—"


def cell(label, value):
    """A label with its filled value underneath, as the printed form reads."""
    return (label, value)


def row_table(cells, widths):
    """One bordered row holding several label/value cells side by side.

    Each cell stacks its label above its value in a single-column inner table,
    so long values wrap downwards instead of running into the next cell.
    """
    inner_style = TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 2),
        ("BOTTOMPADDING", (0, 1), (0, 1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])

    body = []
    for c, w in zip(cells, widths):
        if isinstance(c, tuple):
            label, value = c
            inner = Table([[Paragraph(label, S_LAB)], [Paragraph(value, S_VAL)]],
                          colWidths=[w - 11])
            inner.setStyle(inner_style)
            body.append(inner)
        else:
            # already a flowable list (used for the small note rows)
            body.append(c[0] if isinstance(c, list) and len(c) == 1 else c)

    t = Table([body], colWidths=widths)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def section_bar(title):
    t = Table([[Paragraph(title.upper(), S_BAR)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAR),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _logo(path, h=11 * mm):
    """Scaled logo, or blank spacing if the asset is missing."""
    if not path.exists():
        return Spacer(1, h)
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(str(path)).getSize()
    return Image(str(path), width=h * iw / ih, height=h)


def masthead():
    title = Table(
        [[Paragraph("GOVERNMENT OF MAHARASHTRA", S_TITLE)],
         [Paragraph("State Common Entrance Test Cell, Maharashtra State", S_SUB)]],
        colWidths=[CONTENT_W - 60 * mm],
    )
    title.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    outer = Table([[_logo(EMBLEM), title, _logo(CET_LOGO)]],
                  colWidths=[30 * mm, CONTENT_W - 60 * mm, 30 * mm])
    outer.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return outer


def two_col_header(left, right, widths=None):
    widths = widths or [CONTENT_W * 0.62, CONTENT_W * 0.38]
    t = Table([[Paragraph(left, S_TH), Paragraph(right, S_TH)]], colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAR),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def marks_row(label, value, widths=None):
    widths = widths or [CONTENT_W * 0.62, CONTENT_W * 0.38]
    t = Table([[Paragraph(label, S_LAB), Paragraph(value, S_VAL)]], colWidths=widths)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


# ---------------------------------------------------------------- document
class FormDoc(BaseDocTemplate):
    """Adds the 'Student Name / Signature' strip and page number at the foot."""

    def __init__(self, buf, student_name, reference, **kw):
        super().__init__(buf, pagesize=A4,
                         leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN, bottomMargin=18 * mm, **kw)
        self.student_name = student_name
        self.reference = reference
        frame = Frame(MARGIN, 18 * mm, CONTENT_W, PAGE_H - MARGIN - 18 * mm, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[frame],
                                            onPage=self._decorate)])

    def _decorate(self, canv, doc):
        canv.saveState()
        y = 13 * mm
        canv.setStrokeColor(SOFT)
        canv.setLineWidth(0.5)
        canv.line(MARGIN, y + 6 * mm, PAGE_W - MARGIN, y + 6 * mm)

        canv.setFont("Helvetica", 8)
        canv.setFillColor(colors.HexColor("#333333"))
        canv.drawString(MARGIN + 2, y + 1.5 * mm, "Student Name:")
        canv.setFont("Helvetica-Bold", 8)
        canv.drawString(MARGIN + 24 * mm, y + 1.5 * mm, self.student_name[:46])

        canv.setFont("Helvetica", 8)
        canv.drawString(PAGE_W / 2 + 10 * mm, y + 1.5 * mm, "Signature:")
        canv.line(PAGE_W / 2 + 26 * mm, y + 1 * mm, PAGE_W - MARGIN - 2, y + 1 * mm)

        canv.setFont("Helvetica", 7)
        canv.setFillColor(colors.HexColor("#777777"))
        canv.drawString(MARGIN + 2, y - 3.5 * mm, f"Ref: {self.reference}")
        canv.drawRightString(PAGE_W - MARGIN - 2, y - 3.5 * mm, str(canv.getPageNumber()))
        canv.restoreState()


# ---------------------------------------------------------------- builder
def build_form_pdf(sub) -> bytes:
    d = sub.data or {}
    docs = sub.documents or {}
    name = (sub.full_name or "").strip() or "—"

    buf = BytesIO()
    doc = FormDoc(buf, name, sub.reference or "—")
    F = []
    half = [CONTENT_W / 2] * 2
    third = [CONTENT_W / 3] * 3
    gap = Spacer(1, 5)

    # ---------------- PAGE 1 ----------------
    F += [masthead(), Spacer(1, 5)]

    F += [section_bar("CET Cell Login"), Spacer(1, 2)]
    F += [row_table([cell("CET CELL ID:", _v(d, "cet_cell_id")),
                     cell("CET CELL Password:", _v(d, "cet_cell_password"))], half)]
    F += [Spacer(1, 5)]

    F += [section_bar("NEET−UG Details"), Spacer(1, 2)]
    F += [row_table([cell("NEET Roll No:", _v(d, "neet_roll")),
                     cell("NEET Application No.:", _v(d, "neet_appno"))], half)]
    F += [row_table([cell("Date Of Birth:", _v(d, "dob_neet")),
                     cell("NEET Rank:", _v(d, "neet_rank")),
                     cell("NEET Marks:", _v(d, "neet_marks"))], third)]
    F += [Spacer(1, 5)]

    F += [two_col_header("SUBJECT", "MARKS")]
    for lbl, key in [("Physics Percentile Score Obtained:", "phy_pct"),
                     ("Chemistry Percentile Score Obtained:", "che_pct"),
                     ("Biology Percentile Score Obtained:", "bio_pct"),
                     ("Total Percentile Score Obtained:", "tot_pct"),
                     ("PCB Total [out of 720]:", "pcb_total")]:
        F += [marks_row(lbl, _v(d, key))]
    F += [Spacer(1, 5)]

    F += [section_bar("Personal Information"), Spacer(1, 2)]
    F += [row_table([cell("Full name of Candidate (As per NEET Score Card):",
                          _v(d, "full_name"))], [CONTENT_W])]
    F += [row_table([cell("Whether your name is changed or updated after 10th "
                          "or equivalent qualification or after marriage?:",
                          _v(d, "name_changed"))], [CONTENT_W])]
    F += [row_table([cell("Father's First Name:", _v(d, "father_name")),
                     cell("Mother's First Name:", _v(d, "mother_name"))], half)]
    F += [row_table([cell("Gender:", _v(d, "gender")),
                     cell("Date Of Birth:", _v(d, "dob"))], half)]
    F += [row_table([cell("CET Registration Mobile Number:", _v(d, "cet_mobile")),
                     cell("Email-ID (CET Registered):", _v(d, "cet_email"))], half)]
    F += [row_table([cell("Alternate Contact No:", _v(d, "alt_contact")),
                     cell("Alternate Email ID:", _v(d, "alt_email"))], half)]
    F += [row_table([cell("Aadhar Card No.:", _v(d, "aadhaar")),
                     cell("Religion:", _v(d, "religion"))], half)]
    F += [row_table([cell("Mother tongue:", _v(d, "mother_tongue")),
                     cell("Appar ID:", _v(d, "apaar_id"))], half)]
    F += [Spacer(1, 5)]

    F += [section_bar("Permanent Address"), Spacer(1, 2)]
    F += [row_table([cell("Address (Full Address):", _v(d, "address"))], [CONTENT_W])]
    F += [row_table([cell("City:", _v(d, "city")),
                     cell("State:", _v(d, "state")),
                     cell("District:", _v(d, "district"))], third)]
    F += [row_table([cell("Taluka:", _v(d, "taluka")),
                     cell("Pin Code:", _v(d, "pincode"))], half)]

    # ---------------- PAGE 2 : RESERVATION ----------------
    F += [_page_break()]
    F += [section_bar("Reservation"), Spacer(1, 2)]
    F += [row_table([cell("Nationality of the Candidate:", _v(d, "nationality")),
                     cell("Whether the Candidate is domicile of Maharashtra?:",
                          _v(d, "domicile_mh"))], half)]
    F += [row_table([cell("Is the candidate OCI card holder / NRI?:", _v(d, "oci")),
                     cell("Does the candidate want to apply for NRI?:",
                          _v(d, "nri"))], half)]
    F += [row_table([cell("Region of Residence:", _v(d, "region_res")),
                     cell("Category Of the Candidate:", _v(d, "category")),
                     cell("Sub Category:", _v(d, "sub_category"))], third)]
    F += [Spacer(1, 5)]

    F += [row_table([cell("Do you possess Caste Certificate?:",
                          _v(d, "has_caste_cert")),
                     cell("Caste Certificate Number (outward No):",
                          _v(d, "caste_cert_no"))], half)]
    F += [row_table([cell("Caste Certificate Issuing Date:", _v(d, "caste_cert_date")),
                     cell("Caste Certificate Issuing Authority:",
                          _v(d, "caste_cert_auth")),
                     cell("Caste Certificate Issuing District/Taluka:",
                          _v(d, "caste_cert_dist"))], third)]
    F += [Spacer(1, 5)]

    F += [row_table([cell("Do you possess Caste Validity?:", _v(d, "has_caste_val")),
                     cell("Caste Validity Number (VC No):",
                          _v(d, "caste_val_no"))], half)]
    F += [row_table([cell("Caste Validity Issuing Date:", _v(d, "caste_val_date")),
                     cell("Caste Validity Issuing Authority:", _v(d, "caste_val_auth")),
                     cell("Caste Validity Issuing District/Taluka:",
                          _v(d, "caste_val_dist"))], third)]
    F += [Spacer(1, 5)]

    F += [row_table([cell("Do you possess NCL Certificate?:", _v(d, "has_ncl")),
                     cell("NCL Certificate Number (Outward No):",
                          _v(d, "ncl_no"))], half)]
    F += [row_table([cell("NCL Certificate Issuing Date:", _v(d, "ncl_date")),
                     cell("NCL Certificate Issuing Authority:", _v(d, "ncl_auth")),
                     cell("NCL Certificate Issuing District/Taluka:",
                          _v(d, "ncl_dist"))], third)]
    F += [row_table([[Paragraph(
        "Required for VJ / NT / OBC / SBC (one year valid). Not required for "
        "SC / ST / OPEN / EWS / PWD. All document validity is one year only.",
        S_SMALL)]], [CONTENT_W])]
    F += [Spacer(1, 5)]

    F += [row_table([cell("Your Annual family Income:", _v(d, "annual_income")),
                     cell("Income Certificate (1 Year Valid):", _v(d, "income_1yr")),
                     cell("Income Certificate (1 to 3 Year Valid):",
                          _v(d, "income_3yr"))], third)]
    F += [row_table([cell("Do you want to claim Religious Minority Quota?:",
                          _v(d, "minority_religious")),
                     cell("Do you want to Claim Linguistic Minority?:",
                          _v(d, "minority_linguistic"))], half)]
    F += [row_table([cell("Is the candidate an orphan?:", _v(d, "orphan")),
                     cell("Orphan certificate available?:", _v(d, "orphan_cert")),
                     cell("Are you a Person With Disability (PWD)?:",
                          _v(d, "pwd"))], third)]

    # ---------------- PAGE 3 : SSC + HSC ----------------
    F += [_page_break()]
    F += [section_bar("SSC Qualification"), Spacer(1, 2)]
    F += [row_table([cell("SSC/10th or Equivalent Examination Year of passing:",
                          _v(d, "ssc_year")),
                     cell("One of the languages SSC/10th or Equivalent:",
                          _v(d, "ssc_language"))], half)]
    F += [row_table([cell("State of SSC/10th Std. Passing:", _v(d, "ssc_state")),
                     cell("District of SSC/10th Std. Passing:", _v(d, "ssc_district")),
                     cell("Taluka of SSC/10th Std. Passing:",
                          _v(d, "ssc_taluka"))], third)]
    F += [row_table([cell("10th Std Marks Out of:", _v(d, "ssc_out_of")),
                     cell("10th Std Marks Obtained:", _v(d, "ssc_obtained")),
                     cell("10th Std Marks Percentage:", _v(d, "ssc_percent"))], third)]
    F += [Spacer(1, 8)]

    F += [section_bar("HSC Qualification"), Spacer(1, 2)]
    F += [row_table([cell("HSC/12th Equivalent Examination:", _v(d, "hsc_exam")),
                     cell("HSC/12th or Equivalent Examination Passing Year:",
                          _v(d, "hsc_year"))], half)]
    F += [row_table([cell("HSC/12th Examination Roll No./Seat No.:",
                          _v(d, "hsc_rollno")),
                     cell("State of HSC/12th Std. Passing:", _v(d, "hsc_state"))], half)]
    F += [row_table([cell("District of HSC/12th Std. Passing:", _v(d, "hsc_district")),
                     cell("Taluka of HSC/12th Std. Passing:",
                          _v(d, "hsc_taluka"))], half)]
    F += [Spacer(1, 5)]

    w = [CONTENT_W * 0.4, CONTENT_W * 0.3, CONTENT_W * 0.3]
    head = Table([[Paragraph("SUBJECT", S_TH), Paragraph("MARKS OBTAINED", S_TH),
                   Paragraph("MARKS OUT OF", S_TH)]], colWidths=w)
    head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAR),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    F += [head]
    for subj, o, u in [("PHYSICS", "hsc_phy_obt", "hsc_phy_out"),
                       ("CHEMISTRY", "hsc_che_obt", "hsc_che_out"),
                       ("BIOLOGY", "hsc_bio_obt", "hsc_bio_out"),
                       ("ENGLISH", "hsc_eng_obt", "hsc_eng_out")]:
        r = Table([[Paragraph(subj, S_LAB), Paragraph(_v(d, o), S_VAL),
                    Paragraph(_v(d, u), S_VAL)]], colWidths=w)
        r.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("ALIGN", (1, 0), (-1, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        F += [r]
    F += [Spacer(1, 5)]
    F += [row_table([cell("12th Std Marks Out of:", _v(d, "hsc_out_of")),
                     cell("12th Std Marks Obtained:", _v(d, "hsc_obtained")),
                     cell("12th Std Marks Percentage:", _v(d, "hsc_percent"))], third)]

    # ---------------- PAGE 4 : PARALLEL RESERVATION + FEES ----------------
    F += [_page_break()]
    F += [section_bar("Parallel Reservation"), Spacer(1, 2)]
    F += [row_table([[Paragraph(
        "For a hilly area certificate, the student must study 11th &amp; 12th in a "
        "hilly area. Hilly area students' and parents' certificate is mandatory. "
        "PWD — disability certificate required. Defence reservation — certificate required.",
        S_SMALL)]], [CONTENT_W])]
    F += [row_table([cell("Does the Candidate want to claim exception:",
                          _v(d, "claim_exception")),
                     cell("Hilly Area:", _v(d, "hilly_area"))], half)]
    F += [row_table([cell("Hill Area Village:", _v(d, "hilly_village")),
                     cell("Hill Area Taluka:", _v(d, "hilly_taluka"))], half)]
    F += [row_table([cell("PWD Reservation:", _v(d, "pwd_reservation")),
                     cell("PWD Disability Certificate:", _v(d, "pwd_cert"))], half)]
    F += [row_table([cell("Defence Reservation:", _v(d, "defence_res")),
                     cell("Defence Certificate (D1 / D2 / D3):",
                          _v(d, "defence_type"))], half)]
    F += [Spacer(1, 8)]

    F += [section_bar("Application Fees"), Spacer(1, 2)]
    F += [row_table([cell("Group (A) MBBS / BDS:", _v(d, "group_a")),
                     cell("Group (B) BAMS / BHMS:", _v(d, "group_b")),
                     cell("Group (C) BPT:", _v(d, "group_c"))], third)]
    F += [row_table([cell("I want to apply for:", _v(d, "quota")),
                     cell("Application Fees:", _v(d, "app_fees")),
                     cell("Fee payment date:", _v(d, "fee_date"))], third)]

    # ---------------- PAGE 5 : DOCUMENTS ----------------
    F += [_page_break()]
    F += [section_bar("Required Documents"), Spacer(1, 2)]
    dw = [14 * mm, CONTENT_W - 14 * mm - 34 * mm - 32 * mm, 34 * mm, 32 * mm]

    def _doc_table(title, names, start_n):
        head = [[Paragraph("SR.<br/>NO.", S_TH), Paragraph(title, S_TH),
                 Paragraph("SUBMIT FOR<br/>(BFEG)", S_TH), Paragraph("BAR CODE NO.", S_TH)]]
        n = start_n
        for name_doc in names:
            n += 1
            status, barcode = doc_parts(docs.get(name_doc))
            bc = Paragraph(barcode or "—", S_VAL) if name_doc in BARCODE_DOCUMENTS else Paragraph("", S_VAL)
            head.append([Paragraph(str(n), S_LAB), Paragraph(name_doc, S_LAB),
                         Paragraph(status or "—", S_VAL), bc])
        tbl = Table(head, colWidths=dw, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BAR),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return tbl, n

    mand_tbl, last = _doc_table("MANDATORY DOCUMENTS", MANDATORY_DOCUMENTS, 0)
    opt_tbl, _ = _doc_table("OPTIONAL DOCUMENTS (if applicable)", OPTIONAL_DOCUMENTS, last)
    F += [mand_tbl, Spacer(1, 8), opt_tbl, Spacer(1, 14)]

    sign = Table([[Paragraph("Student", S_FOOT),
                   Paragraph("Parent / Guardian", S_FOOT),
                   Paragraph("BFEG Representative", S_FOOT)],
                  [Paragraph("<br/><br/>Signature / Date", S_SMALL),
                   Paragraph("<br/><br/>Signature / Date", S_SMALL),
                   Paragraph("<br/><br/>Signature / Date", S_SMALL)]],
                 colWidths=third)
    sign.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), BAR),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    F += [KeepTogether(sign)]

    doc.build(F)
    buf.seek(0)
    return _append_agreement(buf.getvalue())


def _append_agreement(form_bytes: bytes) -> bytes:
    """Attach the booklet's Marathi responsibilities / terms pages.

    Those pages are identical for every candidate and contain no student data,
    so they are carried over verbatim from the original CET booklet rather than
    re-typeset (which would need a Devanagari font).
    """
    if not AGREEMENT.exists():
        return form_bytes
    try:
        from pypdf import PdfReader, PdfWriter
        writer = PdfWriter()
        for page in PdfReader(BytesIO(form_bytes)).pages:
            writer.add_page(page)
        for page in PdfReader(str(AGREEMENT)).pages:
            writer.add_page(page)
        out = BytesIO()
        writer.write(out)
        out.seek(0)
        return out.getvalue()
    except Exception:
        # If merging fails for any reason, the filled pages still download.
        return form_bytes


def _page_break():
    from reportlab.platypus import PageBreak
    return PageBreak()
