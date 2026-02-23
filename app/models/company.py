"""Company database model shape definition."""


def new_company_document(
    name: str,
    street: str,
    zip_code: str,
    city: str,
    country: str = "DE",
    tax_id: str = "",
    phone: str = "",
    email: str = "",
    website: str = "",
    bank_name: str = "",
    iban: str = "",
    bic: str = "",
    logo_path: str = "",
    is_kleinunternehmer: bool = False,
    vat_rates: list = None,
    default_vat_rate: float = 0.19,
) -> dict:
    """Return a dict representing a new company document."""
    from app.utils.helpers import now_utc

    if vat_rates is None:
        vat_rates = [0.19, 0.07, 0.0]

    return {
        "name": name,
        "street": street,
        "zip_code": zip_code,
        "city": city,
        "country": country,
        "tax_id": tax_id,
        "phone": phone,
        "email": email,
        "website": website,
        "bank_name": bank_name,
        "iban": iban,
        "bic": bic,
        "logo_path": logo_path,
        "is_kleinunternehmer": is_kleinunternehmer,
        "vat_rates": vat_rates,
        "default_vat_rate": default_vat_rate,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
