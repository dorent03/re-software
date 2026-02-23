# RE-Software — Invoice Management System v2

Production-ready invoice management system with Vue 3 frontend and FastAPI backend. Features e-invoicing (XRechnung, ZUGFeRD), payment tracking, reminder system (Mahnwesen), SEPA QR codes, and revenue statistics.

## Tech Stack

### Backend

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.103 |
| Language | Python 3.9.19 |
| Database | MongoDB (Motor async driver) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Validation | Pydantic v1 |
| PDF | WeasyPrint + Jinja2 |
| QR Code | qrcode (EPC/SEPA) |
| E-Invoice | XRechnung (UBL 2.1) + ZUGFeRD (CII) |

### Frontend

| Layer | Technology |
|-------|-----------|
| Framework | Vue 3 (Composition API + `<script setup>`) |
| Build Tool | Vite 4 |
| State | Pinia |
| Routing | Vue Router 4 |
| Styling | TailwindCSS 3 |
| HTTP | Axios (JWT-Interceptor) |
| Charts | Chart.js + vue-chartjs |
| QR Code | SEPA EPC QR via API |

## Project Structure

### Frontend (`frontend/`)

```
frontend/
  index.html
  package.json
  vite.config.js               # Vite + API-Proxy auf :8000
  tailwind.config.js
  postcss.config.js
  src/
    main.js                    # App bootstrap, Pinia, Router
    App.vue                    # Root-Komponente (Sidebar/Navbar Layout)
    assets/
      styles.css               # TailwindCSS + Custom Utility-Klassen
    router/
      index.js                 # 12 Routen, Auth-Guards, Lazy Loading
    store/
      index.js                 # Re-exports aller Stores
      auth.js                  # Login, Register, JWT, User-Profil
      customers.js             # CRUD + Pagination
      products.js              # CRUD + Pagination
      documents.js             # CRUD + Zahlungen, Mahnungen, Storno, E-Rechnung
      stats.js                 # Umsatz-Statistiken
    utils/
      api.js                   # Axios-Instanz mit JWT-Interceptor
      helpers.js               # Formatierung (EUR, Datum), Berechnungen
      validation.js            # Formvalidierung
    components/
      Sidebar.vue              # Responsive Sidebar mit Collapse
      Navbar.vue               # Kopfzeile mit User + Logout
      DataTable.vue            # Wiederverwendbar: Pagination, Sortierung, Slots
      FormInput.vue            # Wiederverwendbar: Input, Select, Textarea
      PositionTable.vue        # Inline-Editing: Positionen mit Rabatt + MwSt.
      PaymentTable.vue         # Teilzahlungen anzeigen / erfassen
      ReminderTable.vue        # Mahnungen anzeigen / erstellen
      QRCodeDisplay.vue        # SEPA EPC QR-Code
      InvoiceTotals.vue        # Netto, MwSt.-Aufschluesselung, Brutto, Restbetrag
      ChartRevenue.vue         # Balkendiagramm (Chart.js)
    views/
      Login.vue                # Anmeldung
      Register.vue             # Registrierung
      Dashboard.vue            # KPIs, Umsatz-Chart, Top-Kunden
      Customers.vue            # Kundenliste + Suche
      CustomerEditor.vue       # Kunde anlegen / bearbeiten
      Products.vue             # Produktliste + Suche
      ProductEditor.vue        # Produkt anlegen / bearbeiten
      Documents.vue            # Dokumentliste, Filter (Typ, Status), Pagination
      DocumentEditor.vue       # Dokument: Details, Positionen, Zahlungen, Mahnungen
      PDFPreview.vue           # PDF im Browser anzeigen + Download
      Settings.vue             # Firmendaten, Steuer, Bank, Logo, Fusszeile
```

### Backend (`app/`)

```
app/
  main.py                      # FastAPI entry point
  core/
    config.py                  # Environment configuration
    database.py                # Async MongoDB connection
    security.py                # JWT + bcrypt utilities
    dependencies.py            # Auth dependencies
    logging.py                 # Centralized logging setup
  models/                      # Database document shapes
    user.py
    company.py
    customer.py
    product.py
    document.py                # Extended: 7 doc types, payments, reminders
  schemas/                     # Pydantic DTOs
    auth.py
    company.py
    customer.py
    product.py
    document.py                # Extended: payment, reminder, discount schemas
    stats.py                   # Statistics response schemas
  repositories/                # Data access layer
    base.py
    user_repository.py
    company_repository.py
    customer_repository.py
    product_repository.py
    document_repository.py     # Extended: aggregation pipelines, payments
  services/                    # Business logic
    auth_service.py
    company_service.py
    customer_service.py
    product_service.py
    document_service.py        # Extended: payments, reminders, cancel, credit
    pdf_service.py
    einvoice_service.py        # XRechnung + ZUGFeRD XML generation
  routers/                     # API routes
    auth.py
    company.py
    customers.py
    products.py
    documents.py               # Extended: 14 endpoints
    pdf.py
  pdf/
    generator.py               # WeasyPrint + QR + VAT breakdown
    templates/
      invoice.html             # Professional HTML template
  stats/
    stats_service.py           # MongoDB aggregation pipelines
    stats_router.py            # Revenue endpoints
  utils/
    helpers.py
    pagination.py
    sepa_qr.py                 # EPC QR code generator
  middleware/
    tenant.py
    exception_handler.py       # Centralized error handling
    logging_middleware.py       # Request/response logging
```

## Local Development Setup

### Prerequisites

- **Python 3.9.19** (Backend)
- **Node.js >= 16** + npm (Frontend)
- **MongoDB** running locally on `localhost:27017`
- GTK3 runtime (Windows) or `libpango-1.0-0 libcairo2` (Linux) for WeasyPrint

### Backend starten

```bash
cd re-software

# Virtuelle Umgebung erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (macOS/Linux)
# source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# .env aus Vorlage erstellen
copy .env.example .env
# .env oeffnen und einen sicheren JWT_SECRET_KEY setzen

# Server starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend starten

```bash
cd frontend

# Dependencies installieren
npm install

# Dev-Server starten (Port 3000, Proxy auf Backend :8000)
npm run dev
```

### Production Build (Frontend)

```bash
cd frontend
npm run build
# Output in frontend/dist/ — kann von jedem Static-Server ausgeliefert werden
```

### Nach dem Start

| Was | URL |
|-----|-----|
| **Frontend** (Vue App) | http://localhost:3000 |
| **Swagger UI** (API testen) | http://localhost:8000/docs |
| **ReDoc** (Dokumentation) | http://localhost:8000/redoc |
| **Health-Check** | http://localhost:8000/health |

> **Ablauf:** http://localhost:3000 oeffnen > Registrieren > Anmelden > Firmendaten unter Einstellungen pflegen > Kunden und Produkte anlegen > Dokumente erstellen.

### Windows: Fontconfig-Fehler

Falls beim Start oder bei der PDF-Erzeugung erscheint:
`Fontconfig error: Cannot load default config file: No such file: (null)` —

- **Automatisch:** Die App setzt beim Start `FONTCONFIG_FILE` auf das mitgelieferte `fonts/fonts.conf` (verweist auf `C:\Windows\Fonts`). Ein Neustart reicht oft.
- **Falls es weiterhin fehlschlaegt:** Pango/Fontconfig per [MSYS2](https://www.msys2.org/) installieren:
  1. MSYS2 installieren, dann in der MSYS2-Shell: `pacman -S mingw-w64-x86_64-pango`
  2. Vor dem Start der App setzen: `set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin` (Pfad ggf. anpassen)
  3. Server wie gewohnt starten.

## Frontend Features

### Seiten und Routen

| Route | Seite | Beschreibung |
|-------|-------|-------------|
| `/login` | Login | E-Mail + Passwort Anmeldung |
| `/register` | Register | Neues Konto erstellen |
| `/dashboard` | Dashboard | KPIs, Umsatz-Chart, Top-Kunden, offene/bezahlte/ueberfaellige Rechnungen |
| `/customers` | Kunden | Liste mit Suche, Pagination, CRUD |
| `/customers/:id` | Kunde bearbeiten | Formular mit Adresse, USt-IdNr., Notizen |
| `/products` | Produkte | Liste mit Suche, Pagination, CRUD |
| `/products/:id` | Produkt bearbeiten | Name, Preis, Einheit, MwSt.-Satz |
| `/documents` | Dokumente | Filterliste (Typ, Status), Pagination, Suche |
| `/documents/:id` | Dokument bearbeiten | 4 Tabs: Details, Positionen, Zahlungen, Mahnungen |
| `/documents/:id/pdf` | PDF Vorschau | Eingebettete PDF-Anzeige + Download |
| `/settings` | Einstellungen | Firmendaten, Steuer, Bank, Logo, Rechnungsnummern |

### Reusable Components

| Komponente | Beschreibung |
|-----------|-------------|
| `DataTable` | Generische Tabelle mit Pagination, Sortierung, Slots fuer Custom Cells |
| `FormInput` | Input, Select, Textarea mit Label, Fehleranzeige, Validierung |
| `PositionTable` | Inline-Editing von Rechnungspositionen mit Rabatt und MwSt. |
| `PaymentTable` | Teilzahlungen anzeigen und neue erfassen (Betrag, Zahlungsart, Notiz) |
| `ReminderTable` | Mahnungen (Stufe 1-3) anzeigen und erstellen |
| `QRCodeDisplay` | SEPA EPC QR-Code fuer Ueberweisungen |
| `InvoiceTotals` | Netto, MwSt.-Aufschluesselung, Brutto, bezahlt, Restbetrag |
| `ChartRevenue` | Balkendiagramm fuer monatlichen Umsatz (Chart.js) |

### Dokumenten-Editor Features

- **4 Tabs:** Details | Positionen | Zahlungen | Mahnungen
- **Positionstabelle:** Inline-Editing mit Beschreibung, Menge, Einheit, Einzelpreis, Rabatt %, MwSt.-Satz
- **Produkt-Schnelleinfuegung:** Dropdown zum Hinzufuegen von Produkten aus dem Katalog
- **Live-Berechnung:** Netto, MwSt.-Aufschluesselung und Brutto werden in Echtzeit berechnet
- **Teilzahlungen:** Betrag, Zahlungsart, Notiz erfassen — Status auto-aktualisiert
- **Mahnungen:** Stufe, Gebuehr, Notiz — bis zu 3 Mahnstufen
- **Aktionsbuttons:** PDF, Vorschau, XRechnung, ZUGFeRD, Stornieren, Gutschrift, Angebot > Rechnung
- **SEPA QR-Code:** Automatisch angezeigt fuer Rechnungen wenn IBAN konfiguriert

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user + company |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh tokens |
| GET | `/api/v1/auth/me` | Current user profile |

### Company
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/companies/me` | Get company profile |
| PATCH | `/api/v1/companies/me` | Update company (incl. VAT settings) |
| POST | `/api/v1/companies/me/logo` | Upload company logo |

### Customers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/customers/` | Create customer |
| GET | `/api/v1/customers/` | List (paginated, searchable) |
| GET | `/api/v1/customers/{id}` | Get customer |
| PATCH | `/api/v1/customers/{id}` | Update customer |
| DELETE | `/api/v1/customers/{id}` | Deactivate customer |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products/` | Create product |
| GET | `/api/v1/products/` | List (paginated, searchable) |
| GET | `/api/v1/products/{id}` | Get product |
| PATCH | `/api/v1/products/{id}` | Update product |
| DELETE | `/api/v1/products/{id}` | Deactivate product |

### Documents (Invoices, Quotes, and more)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/` | Create document |
| GET | `/api/v1/documents/` | List (paginated, filterable) |
| GET | `/api/v1/documents/{id}` | Get document |
| PATCH | `/api/v1/documents/{id}` | Update draft |
| PATCH | `/api/v1/documents/{id}/status` | Change status |
| POST | `/api/v1/documents/{id}/convert` | Convert quote to invoice |
| POST | `/api/v1/documents/{id}/payment` | Record payment |
| POST | `/api/v1/documents/{id}/reminder` | Add reminder (Mahnung) |
| POST | `/api/v1/documents/{id}/cancel` | Cancel + generate Storno |
| POST | `/api/v1/documents/{id}/credit` | Generate credit note |
| GET | `/api/v1/documents/{id}/xrechnung` | Download XRechnung XML |
| GET | `/api/v1/documents/{id}/zugferd` | Download ZUGFeRD XML |

### PDF
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/{id}/pdf` | Generate PDF |
| GET | `/api/v1/documents/{id}/pdf/preview` | Preview PDF (inline) |
| GET | `/api/v1/documents/{id}/pdf/download` | Download PDF |

### Statistics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stats/revenue/monthly` | Monthly revenue (PAID invoices) |
| GET | `/api/v1/stats/revenue/by-customer` | Revenue per customer |

## Document Types

| Type | Prefix | Description |
|------|--------|-------------|
| `INVOICE` | INV | Standard invoice |
| `QUOTE` | QUO | Quote / offer |
| `DELIVERY_NOTE` | LS | Delivery note (Lieferschein) |
| `ORDER_CONFIRMATION` | AB | Order confirmation |
| `PARTIAL_INVOICE` | TINV | Partial invoice (Abschlagsrechnung) |
| `CREDIT_NOTE` | GS | Credit note (Gutschrift) |
| `CANCELLATION` | ST | Cancellation (Stornorechnung) |

## Business Rules

### Payments (Teilzahlungen)
- Record partial or full payments via `POST /documents/{id}/payment`
- `paidAmount` and `remainingAmount` updated atomically
- Status auto-transitions: `PARTIALLY_PAID` when partial, `PAID` when full

### Reminders (Mahnwesen)
- Up to 3 reminder levels via `POST /documents/{id}/reminder`
- Optional reminder fee per level
- Status transitions to `OVERDUE`

### Cancellation (Storno)
- `POST /documents/{id}/cancel` marks original as `CANCELLED`
- Generates a `CANCELLATION` document with negative totals
- Linked via `related_document_id`

### Credit Notes (Gutschriften)
- `POST /documents/{id}/credit` generates a `CREDIT_NOTE`
- Negative totals, linked to original invoice

### Discounts
- Per-position `discount_percent` field (0-100%)
- Net calculated after discount: `(qty * price) - discount`
- VAT calculated on discounted net amount

### VAT (MwSt.)
- Configurable per company: `vat_rates`, `default_vat_rate`
- Kleinunternehmer mode: forces 0% VAT, hides VAT in PDF
- VAT breakdown table in PDF grouped by rate

### Sequential Numbering
- Atomic `findOneAndUpdate` with `$inc` per company per document type
- Format: `{PREFIX}-{000001}`

## E-Invoicing

### XRechnung
- UBL 2.1 XML conforming to XRechnung 2.0 profile
- Endpoint: `GET /documents/{id}/xrechnung`

### ZUGFeRD
- Cross-Industry Invoice (CII) XML, Comfort profile
- Endpoint: `GET /documents/{id}/zugferd`

## SEPA QR Code
- EPC 069-12 standard for SEPA credit transfers
- Embedded in invoice PDFs automatically when IBAN is configured
- Contains: IBAN, BIC, amount, recipient, invoice number reference

## Status Transitions

### Invoices / Partial Invoices
```
DRAFT > SENT > PARTIALLY_PAID > PAID
DRAFT > SENT > OVERDUE > PAID
DRAFT > SENT > CANCELLED
Any non-PAID > CANCELLED (generates Storno document)
```

### Quotes
```
DRAFT > SENT > ACCEPTED (> convert to invoice)
DRAFT > SENT > REJECTED
DRAFT/SENT > CANCELLED
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `re_software` | Database name |
| `JWT_SECRET_KEY` | (change me) | Secret for JWT signing |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `UPLOAD_DIR` | `uploads` | Upload storage directory |
| `PDF_DIR` | `pdfs` | Generated PDF storage directory |

## Multi-Tenancy

Every user belongs to a `company_id`. All data queries are automatically scoped to the user's company, preventing cross-tenant data access.
