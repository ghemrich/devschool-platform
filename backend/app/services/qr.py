import base64
import io

import qrcode


def generate_qr_base64(url: str) -> str:
    """Generate a QR code PNG as a base64-encoded string."""
    qr = qrcode.make(url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
