"""Product database model shape definition."""


def new_product_document(
    company_id: str,
    name: str,
    description: str = "",
    unit: str = "Stück",
    unit_price: float = 0.0,
    vat_rate: float = 0.19,
) -> dict:
    """Return a dict representing a new product document."""
    from app.utils.helpers import now_utc

    return {
        "company_id": company_id,
        "name": name,
        "description": description,
        "unit": unit,
        "unit_price": unit_price,
        "vat_rate": vat_rate,
        "is_active": True,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
