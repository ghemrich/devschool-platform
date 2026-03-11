import base64
import io
import logging

import qrcode
from qrcode.constants import ERROR_CORRECT_M

logger = logging.getLogger(__name__)


def generate_qr_base64(url: str) -> str:
    """Generate a QR code PNG as a base64-encoded string."""
    qr = qrcode.QRCode(
        version=2,
        error_correction=ERROR_CORRECT_M,
        box_size=50,
        border=6,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
