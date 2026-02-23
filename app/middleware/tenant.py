"""Multi-tenant isolation middleware and helpers."""

from fastapi import HTTPException, status


def enforce_tenant(user: dict, resource_company_id: str) -> None:
    """Raise 403 if the user's company does not match the resource's company."""
    user_company_id = str(user.get("company_id", ""))
    if user_company_id != str(resource_company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource belongs to another company",
        )
