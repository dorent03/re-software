"""
Integration test suite for the Invoice Management System.
Tests: Registration, Login, Customers, Products, Documents, Settings, Stats.
Run with: venv\Scripts\python.exe test_integration.py
"""

import json
import sys
import time
import requests

BASE = "http://localhost:8000/api/v1"
EMAIL = f"inttest_{int(time.time())}@example.com"
PASSWORD = "Test1234!"

results = []


def report(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed, detail))
    msg = f"  [{status}] {name}" + (f"  -- {detail}" if detail else "")
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def main():
    token = None
    customer_id = None
    product_id = None
    document_id = None

    print("=" * 60)
    print("INTEGRATION TEST SUITE")
    print(f"Base URL: {BASE}")
    print(f"Test user: {EMAIL}")
    print("=" * 60)

    # ── 1. HEALTH CHECK ──────────────────────────────────────────
    print("\n1) Health Check")
    try:
        r = requests.get("http://localhost:8000/docs", timeout=5)
        report("Backend erreichbar", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        report("Backend erreichbar", False, str(e))
        print("\n  Backend nicht erreichbar -- Tests abgebrochen.")
        sys.exit(1)

    # ── 2. REGISTRATION ──────────────────────────────────────────
    print("\n2) Registrierung")
    r = requests.post(f"{BASE}/auth/register", json={
        "email": EMAIL,
        "password": PASSWORD,
        "first_name": "Integration",
        "last_name": "Test",
        "company_name": "IntTest GmbH",
        "company_street": "Hauptstr 1",
        "company_zip": "10115",
        "company_city": "Berlin",
        "company_country": "DE",
    })
    report("Register", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:300]}")
    if r.status_code not in (200, 201):
        print("\n  Registrierung fehlgeschlagen -- Tests abgebrochen.")
        sys.exit(1)

    # ── 3. LOGIN ─────────────────────────────────────────────────
    print("\n3) Login")
    r = requests.post(f"{BASE}/auth/login", json={
        "email": EMAIL,
        "password": PASSWORD,
    })
    report("Login", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        report("Token erhalten", bool(token), f"Token: {str(token)[:30]}...")
    else:
        report("Token erhalten", False, r.text[:300])
        print("\n  Login fehlgeschlagen -- Tests abgebrochen.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    # ── 4. AUTH/ME ───────────────────────────────────────────────
    print("\n4) Auth: /me")
    r = requests.get(f"{BASE}/auth/me", headers=headers)
    report("GET /auth/me", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        user = r.json()
        report("User-Email korrekt", user.get("email") == EMAIL, user.get("email", "???"))

    # ── 5. COMPANY / SETTINGS ────────────────────────────────────
    print("\n5) Firmeneinstellungen")
    r = requests.get(f"{BASE}/companies/me", headers=headers)
    report("GET /companies/me", r.status_code == 200, f"HTTP {r.status_code}")
    if r.status_code == 200:
        company = r.json()
        report("Firmenname korrekt", company.get("name") == "IntTest GmbH", company.get("name", "???"))

    # Update company
    r = requests.patch(f"{BASE}/companies/me", headers=headers, json={
        "iban": "DE89370400440532013000",
        "bic": "COBADEFFXXX",
        "phone": "+49 30 12345678",
    })
    report("PATCH /companies/me", r.status_code == 200, f"HTTP {r.status_code}")

    # ── 6. CUSTOMERS ─────────────────────────────────────────────
    print("\n6) Kunden-Modul")
    r = requests.post(f"{BASE}/customers/", headers=headers, json={
        "name": "Max Mustermann",
        "street": "Kundenstr. 5",
        "zip_code": "20095",
        "city": "Hamburg",
        "country": "DE",
        "email": f"kunde_{int(time.time())}@test.de",
        "phone": "+49 40 9876543",
    })
    report("POST /customers/ (Anlegen)", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:200]}")
    if r.status_code in (200, 201):
        customer_id = r.json().get("id")
        report("Kunden-ID erhalten", bool(customer_id), customer_id)

    # List customers
    r = requests.get(f"{BASE}/customers/", headers=headers)
    report("GET /customers/ (Liste)", r.status_code == 200, f"HTTP {r.status_code}")

    # Update customer
    if customer_id:
        r = requests.patch(f"{BASE}/customers/{customer_id}", headers=headers, json={
            "name": "Max Mustermann AG",
            "street": "Kundenstr. 5",
            "zip_code": "20095",
            "city": "Hamburg",
        })
        report("PATCH /customers/:id (Update)", r.status_code == 200, f"HTTP {r.status_code} -- {r.text[:200]}")

    # Get single customer
    if customer_id:
        r = requests.get(f"{BASE}/customers/{customer_id}", headers=headers)
        report("GET /customers/:id (Detail)", r.status_code == 200, f"HTTP {r.status_code}")

    # ── 7. PRODUCTS ──────────────────────────────────────────────
    print("\n7) Produkt-Modul")
    r = requests.post(f"{BASE}/products/", headers=headers, json={
        "name": "Webentwicklung",
        "description": "Stundensatz Webentwicklung",
        "unit": "Stunde",
        "unit_price": 95.00,
        "vat_rate": 0.19,
    })
    report("POST /products/ (Anlegen)", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:200]}")
    if r.status_code in (200, 201):
        product_id = r.json().get("id")
        report("Produkt-ID erhalten", bool(product_id), product_id)

    # List products
    r = requests.get(f"{BASE}/products/", headers=headers)
    report("GET /products/ (Liste)", r.status_code == 200, f"HTTP {r.status_code}")

    # Update product
    if product_id:
        r = requests.patch(f"{BASE}/products/{product_id}", headers=headers, json={
            "unit_price": 105.00,
        })
        report("PATCH /products/:id (Update)", r.status_code == 200, f"HTTP {r.status_code} -- {r.text[:200]}")

    # ── 8. DOCUMENTS ─────────────────────────────────────────────
    print("\n8) Dokument-Modul")

    # 8a. Create document with product reference
    items_payload = []
    if product_id:
        items_payload.append({
            "product_id": product_id,
            "quantity": 10,
            "discount_percent": 5.0,
        })
    else:
        items_payload.append({
            "name": "Manuelle Position",
            "quantity": 10,
            "unit": "Stunde",
            "unit_price": 95.0,
            "vat_rate": 0.19,
            "discount_percent": 5.0,
        })

    # Add a free-text item too
    items_payload.append({
        "name": "Projektpauschale",
        "quantity": 1,
        "unit": "Pauschal",
        "unit_price": 500.0,
        "vat_rate": 0.19,
        "discount_percent": 0,
    })

    doc_payload = {
        "document_type": "INVOICE",
        "customer_id": customer_id or "000000000000000000000000",
        "items": items_payload,
        "notes": "Integrationstest-Rechnung",
        "payment_terms_days": 14,
    }

    r = requests.post(f"{BASE}/documents/", headers=headers, json=doc_payload)
    report("POST /documents/ (Rechnung)", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:300]}")
    if r.status_code in (200, 201):
        doc = r.json()
        document_id = doc.get("id")
        report("Dokument-ID erhalten", bool(document_id), document_id)
        report("Dokumentnummer erhalten", bool(doc.get("document_number")), doc.get("document_number", "???"))
        totals = doc.get("totals", {})
        report("Netto > 0", (totals.get("net", 0) or 0) > 0, f"Netto: {totals.get('net', 0)}")
        report("Brutto > 0", (totals.get("gross", 0) or 0) > 0, f"Brutto: {totals.get('gross', 0)}")
    else:
        print(f"     Response: {r.text[:500]}")

    # 8b. List documents
    r = requests.get(f"{BASE}/documents/", headers=headers)
    report("GET /documents/ (Liste)", r.status_code == 200, f"HTTP {r.status_code}")

    # 8c. Get single document
    if document_id:
        r = requests.get(f"{BASE}/documents/{document_id}", headers=headers)
        report("GET /documents/:id (Detail)", r.status_code == 200, f"HTTP {r.status_code}")

    # 8d. Change status to SENT, then add payment
    if document_id:
        r = requests.patch(f"{BASE}/documents/{document_id}/status", headers=headers, json={
            "status": "SENT",
        })
        report("PATCH /documents/:id/status (DRAFT->SENT)", r.status_code == 200, f"HTTP {r.status_code} -- {r.text[:200]}")

        r = requests.post(f"{BASE}/documents/{document_id}/payment", headers=headers, json={
            "amount": 100.0,
            "method": "BANK",
        })
        report("POST /documents/:id/payment (Teilzahlung)", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:200]}")

    # 8e. Add reminder
    if document_id:
        r = requests.post(f"{BASE}/documents/{document_id}/reminder", headers=headers, json={
            "level": 1,
            "fee": 5.0,
        })
        # Reminder might fail if not overdue; accept 200/400/422
        report("POST /documents/:id/reminder", r.status_code in (200, 201, 400, 422), f"HTTP {r.status_code} -- {r.text[:200]}")

    # 8f. PDF generate + download
    if document_id:
        r = requests.post(f"{BASE}/documents/{document_id}/pdf", headers=headers)
        report("POST /documents/:id/pdf (Generieren)", r.status_code == 200, f"HTTP {r.status_code} -- {r.text[:200]}")
        r = requests.get(f"{BASE}/documents/{document_id}/pdf/download", headers=headers)
        report("GET /documents/:id/pdf/download", r.status_code == 200, f"HTTP {r.status_code}, Content-Type: {r.headers.get('content-type', '?')}, Size: {len(r.content)} bytes")

    # 8g. Create quote and try convert -> verify CONVERTED status
    quote_id = None
    converted_invoice_id = None
    if customer_id:
        quote_payload = {
            "document_type": "QUOTE",
            "customer_id": customer_id,
            "items": [{
                "name": "Beratung",
                "quantity": 5,
                "unit": "Stunde",
                "unit_price": 120.0,
                "vat_rate": 0.19,
                "discount_percent": 0,
            }],
            "notes": "Testangebot",
            "payment_terms_days": 30,
        }
        r = requests.post(f"{BASE}/documents/", headers=headers, json=quote_payload)
        report("POST /documents/ (Angebot)", r.status_code in (200, 201), f"HTTP {r.status_code}")
        if r.status_code in (200, 201):
            quote_id = r.json().get("id")
            # Transition: DRAFT -> SENT -> ACCEPTED
            requests.patch(f"{BASE}/documents/{quote_id}/status", headers=headers, json={"status": "SENT"})
            requests.patch(f"{BASE}/documents/{quote_id}/status", headers=headers, json={"status": "ACCEPTED"})
            r2 = requests.post(f"{BASE}/documents/{quote_id}/convert", headers=headers, json={})
            report("POST /documents/:id/convert (Angebot->Rechnung)", r2.status_code in (200, 201), f"HTTP {r2.status_code} -- {r2.text[:200]}")
            if r2.status_code in (200, 201):
                converted_invoice_id = r2.json().get("id")
            # Verify quote is now CONVERTED
            r3 = requests.get(f"{BASE}/documents/{quote_id}", headers=headers)
            if r3.status_code == 200:
                quote_status = r3.json().get("status")
                report("Quote Status = CONVERTED nach Umwandlung", quote_status == "CONVERTED", f"Status: {quote_status}")

    # 8h. Partial invoice (Abschlagsrechnung)
    partial_invoice_id = None
    if document_id:
        r = requests.post(f"{BASE}/documents/{document_id}/create-partial", headers=headers, json={
            "amount": 200.0,
            "notes": "1. Abschlag",
        })
        report("POST /documents/:id/create-partial (Abschlagsrechnung)", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:300]}")
        if r.status_code in (200, 201):
            partial_data = r.json()
            partial_invoice_id = partial_data.get("id")
            report("Partial Invoice ist PARTIAL_INVOICE Typ", partial_data.get("document_type") == "PARTIAL_INVOICE", partial_data.get("document_type", "???"))
            report("Partial Invoice hat related_document_id", partial_data.get("related_document_id") == document_id, partial_data.get("related_document_id", "???"))

    # 8i. Partial invoice exceeding total should fail
    if document_id:
        r = requests.post(f"{BASE}/documents/{document_id}/create-partial", headers=headers, json={
            "amount": 999999.0,
            "notes": "Zu viel!",
        })
        report("Partial Invoice ueber Gesamtbetrag -> 400", r.status_code == 400, f"HTTP {r.status_code} -- {r.text[:200]}")

    # 8j. Reminder on partial invoice
    if partial_invoice_id:
        # First send the partial invoice
        requests.patch(f"{BASE}/documents/{partial_invoice_id}/status", headers=headers, json={"status": "SENT"})
        r = requests.post(f"{BASE}/documents/{partial_invoice_id}/reminder", headers=headers, json={"fee": 5.0})
        report("Reminder auf Partial Invoice", r.status_code in (200, 201), f"HTTP {r.status_code} -- {r.text[:200]}")

    # 8k. Related documents endpoint
    if document_id:
        r = requests.get(f"{BASE}/documents/{document_id}/related", headers=headers)
        report("GET /documents/:id/related", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            related = r.json()
            report("Related: parent ist null (Hauptrechnung)", related.get("parent") is None, str(related.get("parent")))
            children_count = len(related.get("children", []))
            report("Related: children enthalten Partial Invoice", children_count > 0, f"Anzahl: {children_count}")

    # 8l. Related documents for partial invoice (should show parent)
    if partial_invoice_id:
        r = requests.get(f"{BASE}/documents/{partial_invoice_id}/related", headers=headers)
        report("GET /documents/:id/related (Partial)", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            related = r.json()
            report("Partial Related: parent vorhanden", related.get("parent") is not None, str(related.get("parent", {}).get("document_number", "?")))

    # 8m. Create and test delivery note status flow
    if customer_id:
        r = requests.post(f"{BASE}/documents/", headers=headers, json={
            "document_type": "DELIVERY_NOTE",
            "customer_id": customer_id,
            "items": [{"name": "Lieferung", "quantity": 1, "unit": "Pauschal", "unit_price": 100.0, "vat_rate": 0.19}],
            "notes": "Testlieferschein",
            "related_document_id": document_id or "",
        })
        report("POST /documents/ (Lieferschein)", r.status_code in (200, 201), f"HTTP {r.status_code}")
        if r.status_code in (200, 201):
            dn_id = r.json().get("id")
            r2 = requests.patch(f"{BASE}/documents/{dn_id}/status", headers=headers, json={"status": "SENT"})
            report("Lieferschein DRAFT -> SENT", r2.status_code == 200, f"HTTP {r2.status_code}")

    # 8n. Create and test credit note status flow
    if customer_id:
        r = requests.post(f"{BASE}/documents/", headers=headers, json={
            "document_type": "CREDIT_NOTE",
            "customer_id": customer_id,
            "items": [{"name": "Gutschrift-Pos", "quantity": 1, "unit": "Pauschal", "unit_price": 50.0, "vat_rate": 0.19}],
            "notes": "Test-Gutschrift",
            "related_document_id": document_id or "",
        })
        report("POST /documents/ (Gutschrift direkt)", r.status_code in (200, 201), f"HTTP {r.status_code}")
        if r.status_code in (200, 201):
            cn_id = r.json().get("id")
            r2 = requests.patch(f"{BASE}/documents/{cn_id}/status", headers=headers, json={"status": "SENT"})
            report("Gutschrift DRAFT -> SENT", r2.status_code == 200, f"HTTP {r2.status_code}")

    # 8o. Related docs for converted invoice (should show quote as parent)
    if converted_invoice_id and quote_id:
        r = requests.get(f"{BASE}/documents/{converted_invoice_id}/related", headers=headers)
        report("GET related fuer umgewandelte Rechnung", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            related = r.json()
            parent = related.get("parent")
            report("Parent ist das Original-Angebot", parent is not None and parent.get("id") == quote_id,
                   f"Parent-ID: {parent.get('id', '?') if parent else 'None'}")

    # ── 9. STATISTICS ────────────────────────────────────────────
    print("\n9) Statistiken")
    r = requests.get(f"{BASE}/stats/revenue/monthly", headers=headers)
    report("GET /stats/revenue/monthly", r.status_code == 200, f"HTTP {r.status_code}")

    r = requests.get(f"{BASE}/stats/revenue/by-customer", headers=headers)
    report("GET /stats/revenue/by-customer", r.status_code == 200, f"HTTP {r.status_code}")

    # ── 10. DELETE (soft delete customer) ────────────────────────
    print("\n10) Lösch-Tests")
    if customer_id:
        r = requests.delete(f"{BASE}/customers/{customer_id}", headers=headers)
        report("DELETE /customers/:id (Soft-Delete)", r.status_code in (200, 204), f"HTTP {r.status_code}")

    if product_id:
        r = requests.delete(f"{BASE}/products/{product_id}", headers=headers)
        report("DELETE /products/:id", r.status_code in (200, 204), f"HTTP {r.status_code}")

    # ── SUMMARY ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    print(f"ERGEBNIS: {passed} bestanden, {failed} fehlgeschlagen von {len(results)} Tests")
    if failed:
        print("\nFehlgeschlagene Tests:")
        for name, p, detail in results:
            if not p:
                print(f"  X {name}: {detail}")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
