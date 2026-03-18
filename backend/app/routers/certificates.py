import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.user import User
from app.services.certificate import is_course_completed
from app.services.discord import notify_certificate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["certificates"])

CERT_DIR = Path(__file__).parent.parent.parent / "data" / "certificates"


@router.get("/api/me/certificates")
def my_certificates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List the current user's certificates."""
    certs = db.query(Certificate).filter(Certificate.user_id == current_user.id).all()
    return [
        {
            "cert_id": c.cert_id,
            "course_id": c.course_id,
            "issued_at": c.issued_at.isoformat() if c.issued_at else None,
        }
        for c in certs
    ]


@router.post("/api/me/courses/{course_id}/certificate", status_code=201)
def request_certificate(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request a certificate for a completed course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = (
        db.query(Certificate).filter(Certificate.user_id == current_user.id, Certificate.course_id == course_id).first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Certificate already exists for this course")

    if not is_course_completed(db, current_user.id, course_id):
        raise HTTPException(status_code=400, detail="Course not yet completed")

    cert = Certificate(user_id=current_user.id, course_id=course_id)
    db.add(cert)
    db.commit()
    db.refresh(cert)

    # Generate PDF
    verify_url = f"{settings.base_url}/verify/{cert.cert_id}"
    try:
        from app.services.pdf import generate_certificate_pdf
        from app.services.qr import generate_qr_base64

        qr_b64 = generate_qr_base64(verify_url)
        pdf_bytes = generate_certificate_pdf(
            name=current_user.username,
            course_name=course.name,
            cert_id=cert.cert_id,
            issued_date=cert.issued_at.strftime("%Y-%m-%d") if cert.issued_at else "",
            verify_url=verify_url,
            qr_base64=qr_b64,
        )
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = CERT_DIR / f"{cert.cert_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        cert.pdf_path = f"{cert.cert_id}.pdf"
        db.commit()
        logger.info(
            "Certificate generated: cert_id=%s user=%s course=%s",
            cert.cert_id,
            current_user.username,
            course.name,
        )
    except ImportError:
        pass

    notify_certificate(current_user.username, course.name, cert.cert_id)

    return {"cert_id": cert.cert_id, "course_id": course_id, "issued_at": cert.issued_at.isoformat()}


@router.get("/api/me/certificates/{cert_id}/pdf")
def download_certificate_pdf(
    cert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the PDF for a certificate."""
    cert = db.query(Certificate).filter(Certificate.cert_id == cert_id, Certificate.user_id == current_user.id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Regenerate PDF if missing (e.g. after container recreate)
    resolved_path = (CERT_DIR / cert.pdf_path).resolve() if cert.pdf_path else None
    if not resolved_path or not resolved_path.is_file():
        course = db.query(Course).filter(Course.id == cert.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="PDF not found")
        try:
            from app.services.pdf import generate_certificate_pdf
            from app.services.qr import generate_qr_base64

            verify_url = f"{settings.base_url}/verify/{cert.cert_id}"
            qr_b64 = generate_qr_base64(verify_url)
            pdf_bytes = generate_certificate_pdf(
                name=current_user.username,
                course_name=course.name,
                cert_id=cert.cert_id,
                issued_date=cert.issued_at.strftime("%Y-%m-%d") if cert.issued_at else "",
                verify_url=verify_url,
                qr_base64=qr_b64,
            )
            CERT_DIR.mkdir(parents=True, exist_ok=True)
            pdf_path = CERT_DIR / f"{cert.cert_id}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            cert.pdf_path = f"{cert.cert_id}.pdf"
            db.commit()
            logger.info("Certificate PDF regenerated: cert_id=%s", cert.cert_id)
        except Exception:
            logger.exception("Failed to regenerate certificate PDF: cert_id=%s", cert.cert_id)
            raise HTTPException(status_code=500, detail="Failed to generate PDF") from None
        resolved_path = (CERT_DIR / cert.pdf_path).resolve()

    # Validate the resolved path is within CERT_DIR to prevent path traversal
    if not resolved_path.is_relative_to(CERT_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Invalid certificate path")

    return FileResponse(str(resolved_path), media_type="application/pdf", filename=f"certificate-{cert_id}.pdf")


@router.get("/api/verify/{cert_id}")
def verify_certificate(cert_id: str, db: Session = Depends(get_db)):
    """Public endpoint to verify a certificate."""
    cert = db.query(Certificate).filter(Certificate.cert_id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    user = db.query(User).filter(User.id == cert.user_id).first()
    course = db.query(Course).filter(Course.id == cert.course_id).first()

    return {
        "valid": True,
        "name": user.username if user else None,
        "course": course.name if course else None,
        "issued_at": cert.issued_at.isoformat() if cert.issued_at else None,
        "cert_id": cert.cert_id,
    }
