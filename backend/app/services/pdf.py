import logging

import qrcode
from fpdf import FPDF
from qrcode.constants import ERROR_CORRECT_M

logger = logging.getLogger(__name__)


def _draw_qr(pdf: FPDF, url: str, x: float, y: float, size: float) -> None:
    """Draw a QR code directly as PDF rectangles (no image scaling)."""
    qr = qrcode.QRCode(version=1, error_correction=ERROR_CORRECT_M, box_size=1, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    modules = len(matrix)
    module_size = size / modules

    pdf.set_fill_color(0, 0, 0)
    for row_idx, row in enumerate(matrix):
        for col_idx, val in enumerate(row):
            if val:
                pdf.rect(
                    x + col_idx * module_size,
                    y + row_idx * module_size,
                    module_size,
                    module_size,
                    "F",
                )


def generate_certificate_pdf(
    name: str,
    course_name: str,
    cert_id: str,
    issued_date: str,
    verify_url: str,
    qr_base64: str,
) -> bytes:
    """Generate a certificate PDF using fpdf2."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # Border
    pdf.set_draw_color(44, 62, 80)
    pdf.set_line_width(1.5)
    pdf.rect(10, 10, 277, 190)
    pdf.set_line_width(0.5)
    pdf.rect(13, 13, 271, 184)

    # Title
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(44, 62, 80)
    pdf.set_y(30)
    pdf.cell(0, 15, "OpenSchool", ln=True, align="C")

    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 10, "Tanúsítvány a tanfolyam elvégzéséről", ln=True, align="C")

    # Recipient
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Ez igazolja, hogy", ln=True, align="C")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(231, 76, 60)
    pdf.cell(0, 15, name, ln=True, align="C")

    # Course
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "sikeresen elvégezte a következő kurzust", ln=True, align="C")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 12, course_name, ln=True, align="C")

    # Date
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(0, 8, f"Kiadva: {issued_date}", ln=True, align="C")

    # QR code — drawn as native PDF rectangles
    _draw_qr(pdf, verify_url, x=125, y=140, size=40)

    # Certificate ID & verify URL
    pdf.set_y(182)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 5, f"Tanúsítvány azonosító: {cert_id}", ln=True, align="C")
    pdf.cell(0, 5, f"Ellenőrzés: {verify_url}", ln=True, align="C")

    return pdf.output()
