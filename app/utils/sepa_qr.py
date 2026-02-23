"""SEPA EPC QR code generator for invoices."""

import io
import logging
from pathlib import Path
from typing import Any, Dict

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.core.config import settings

logger = logging.getLogger(__name__)

QR_DIR = settings.PDF_DIR / "qr"
QR_DIR.mkdir(parents=True, exist_ok=True)


def build_epc_payload(
    iban: str,
    bic: str,
    recipient_name: str,
    amount: float,
    reference: str,
) -> str:
    """Build the EPC 069-12 payload string for a SEPA credit transfer QR code.

    Format specification:
    - Service tag: BCD
    - Version: 002
    - Encoding: 1 (UTF-8)
    - SCT (SEPA Credit Transfer)
    - BIC
    - Beneficiary name (max 70 chars)
    - IBAN
    - Amount as EUR{amount}
    - Purpose (empty)
    - Reference (remittance information, max 140 chars)
    - Display text (empty)
    """
    # Sanitize values
    recipient_name = recipient_name[:70]
    reference = reference[:140]
    amount_str = f"EUR{amount:.2f}"

    lines = [
        "BCD",
        "002",
        "1",
        "SCT",
        bic or "",
        recipient_name,
        iban,
        amount_str,
        "",
        reference,
        "",
    ]
    return "\n".join(lines)


def generate_sepa_qr_image(
    document: Dict[str, Any],
    company: Dict[str, Any],
) -> str:
    """Generate a SEPA EPC QR code PNG and return the file path.

    Returns an empty string if IBAN is not configured on the company.
    """
    iban = company.get("iban", "")
    if not iban:
        logger.warning("No IBAN configured — skipping QR code generation")
        return ""

    totals = document.get("totals", {})
    amount = totals.get("remaining_amount", totals.get("gross", 0))
    if amount <= 0:
        return ""

    bic = company.get("bic", "")
    recipient = company.get("name", "")
    reference = document.get("document_number", "")

    payload = build_epc_payload(
        iban=iban,
        bic=bic,
        recipient_name=recipient,
        amount=amount,
        reference=reference,
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qr_{reference}.png"
    filepath = QR_DIR / filename
    img.save(str(filepath))

    logger.info("Generated SEPA QR code: %s", filename)
    return str(filepath)
