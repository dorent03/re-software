"""Customer database model shape definition."""


def new_customer_document(
    company_id: str,
    name: str,
    street: str,
    zip_code: str,
    city: str,
    country: str = "DE",
    email: str = "",
    phone: str = "",
    tax_id: str = "",
    notes: str = "",
) -> dict:
    """Return a dict representing a new customer document."""
    from app.utils.helpers import now_utc

    return {
        "company_id": company_id,
        "name": name,
        "street": street,
        "zip_code": zip_code,
        "city": city,
        "country": country,
        "email": email,
        "phone": phone,
        "tax_id": tax_id,
        "notes": notes,
        "is_active": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
