from pathlib import Path

from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def generate_certificate_pdf(
    name: str,
    course_name: str,
    cert_id: str,
    issued_date: str,
    verify_url: str,
    qr_base64: str,
) -> bytes:
    """Generate a certificate PDF from the HTML template."""
    html_content = (TEMPLATE_DIR / "certificate.html").read_text()
    html_content = html_content.replace("{{name}}", name)
    html_content = html_content.replace("{{course_name}}", course_name)
    html_content = html_content.replace("{{cert_id}}", cert_id)
    html_content = html_content.replace("{{issued_date}}", issued_date)
    html_content = html_content.replace("{{verify_url}}", verify_url)
    html_content = html_content.replace("{{qr_base64}}", qr_base64)

    return HTML(string=html_content).write_pdf()
