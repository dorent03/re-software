<script setup>
import { ref, onMounted } from 'vue'
import { db, nowIso } from '@/db'
import { exportAllData, importAllData } from '@/services/dataService'
import FormInput from '@/components/FormInput.vue'

const loading = ref(true)
const saving = ref(false)
const importing = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  name: '',
  street: '',
  zip: '',
  city: '',
  country: 'Deutschland',
  phone: '',
  email: '',
  website: '',
  vat_id: '',
  tax_number: '',
  iban: '',
  bic: '',
  bank_name: '',
  invoice_prefix: 'RE',
  invoice_next_number: 1,
  quote_prefix: 'AN',
  footer_text: '',
  kleinunternehmer: false,
  default_vat_rate: 0.19,
  vat_rates: '19, 7, 0',
  default_due_days: 14,
})

const logoPreview = ref('')
const companyId = ref(null)

function mapCompanyToForm(company) {
  return {
    name: company.name || '',
    street: company.street || '',
    zip: company.zip || '',
    city: company.city || '',
    country: company.country || 'Deutschland',
    phone: company.phone || '',
    email: company.email || '',
    website: company.website || '',
    vat_id: company.vat_id || '',
    tax_number: company.tax_number || '',
    iban: company.iban || '',
    bic: company.bic || '',
    bank_name: company.bank_name || '',
    invoice_prefix: company.invoice_prefix || 'RE',
    invoice_next_number: company.invoice_next_number || 1,
    quote_prefix: company.quote_prefix || 'AN',
    footer_text: company.footer_text || '',
    kleinunternehmer: !!company.kleinunternehmer,
    default_vat_rate: company.default_vat_rate ?? 0.19,
    vat_rates: (company.vat_rates || [0.19, 0.07, 0]).map((rate) => (rate * 100).toFixed(0)).join(', '),
    default_due_days: company.default_due_days ?? 14,
  }
}

async function readCompany() {
  const company = await db.company.orderBy('id').last()
  if (!company) return null
  companyId.value = company.id
  logoPreview.value = company.logo_base64 || ''
  form.value = mapCompanyToForm(company)
  return company
}

onMounted(async () => {
  try {
    await readCompany()
  } finally {
    loading.value = false
  }
})

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

async function onLogoChange(event) {
  const file = event.target.files?.[0]
  if (!file) return
  logoPreview.value = await readAsDataUrl(file)
}

async function handleSave() {
  error.value = ''
  success.value = ''
  if (!form.value.name.trim()) {
    error.value = 'Firmenname ist erforderlich'
    return
  }

  saving.value = true
  try {
    const vatRates = form.value.vat_rates
      .split(',')
      .map((entry) => Number(entry.trim()) / 100)
      .filter((entry) => Number.isFinite(entry))

    const payload = {
      ...form.value,
      name: form.value.name.trim(),
      vat_rates: vatRates,
      logo_base64: logoPreview.value,
      updated_at: nowIso(),
    }

    if (companyId.value == null) {
      const id = await db.company.add({ ...payload, created_at: nowIso() })
      companyId.value = id
    } else {
      await db.company.update(companyId.value, payload)
    }

    success.value = 'Einstellungen gespeichert'
  } catch (saveError) {
    error.value = saveError instanceof Error ? saveError.message : 'Speichern fehlgeschlagen'
  } finally {
    saving.value = false
  }
}

async function handleExport() {
  error.value = ''
  success.value = ''
  try {
    await exportAllData()
    success.value = 'Datenexport erstellt'
  } catch (exportError) {
    error.value = exportError instanceof Error ? exportError.message : 'Export fehlgeschlagen'
  }
}

async function handleImport(event) {
  const file = event.target.files?.[0]
  if (!file) return
  importing.value = true
  error.value = ''
  success.value = ''
  try {
    await importAllData(file)
    await readCompany()
    success.value = 'Daten erfolgreich importiert'
  } catch (importError) {
    error.value = importError instanceof Error ? importError.message : 'Import fehlgeschlagen'
  } finally {
    importing.value = false
    event.target.value = ''
  }
}
</script>

<template>
  <div class="w-full">
    <div class="mb-6">
      <h2 class="text-xl font-bold text-gray-900">Einstellungen</h2>
      <p class="text-sm text-gray-500 mt-1">Lokale Firmendaten, Dokument-Defaults und Backups</p>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <svg class="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <template v-else>
      <div class="flex flex-col xl:flex-row gap-8 xl:gap-10">
        <div class="flex-1 min-w-0 max-w-3xl">
          <div v-if="error" class="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {{ error }}
          </div>
          <div v-if="success" class="mb-4 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
            {{ success }}
          </div>

          <form class="space-y-6" @submit.prevent="handleSave">
        <!-- Company info -->
        <div class="card space-y-5">
          <h3 class="text-base font-semibold text-gray-800">Firmeninformationen</h3>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormInput v-model="form.name" label="Firmenname" required />
            <FormInput v-model="form.email" label="E-Mail" type="email" />
            <FormInput v-model="form.phone" label="Telefon" />
            <FormInput v-model="form.website" label="Website" />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="sm:col-span-2">
              <FormInput v-model="form.street" label="Straße" />
            </div>
            <FormInput v-model="form.zip" label="PLZ" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormInput v-model="form.city" label="Stadt" />
            <FormInput v-model="form.country" label="Land" />
          </div>
        </div>

        <!-- Tax info -->
        <div class="card space-y-5">
          <h3 class="text-base font-semibold text-gray-800">Steuerliche Informationen</h3>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormInput v-model="form.vat_id" label="USt-IdNr." placeholder="DE123456789" />
            <FormInput v-model="form.tax_number" label="Steuernummer" placeholder="12/345/67890" />
          </div>

          <div class="flex items-center gap-3">
            <input
              id="kleinunternehmer"
              v-model="form.kleinunternehmer"
              type="checkbox"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label for="kleinunternehmer" class="text-sm text-gray-700">
              Kleinunternehmerregelung (§ 19 UStG) — keine MwSt. auf Rechnungen
            </label>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="label-text">Standard MwSt.-Satz</label>
              <select v-model="form.default_vat_rate" class="input-field">
                <option :value="0.19">19%</option>
                <option :value="0.07">7%</option>
                <option :value="0">0%</option>
              </select>
            </div>
            <FormInput
              v-model="form.vat_rates"
              label="Verfügbare MwSt.-Sätze (%)"
              placeholder="19, 7, 0"
            />
          </div>
        </div>

        <!-- Bank info -->
        <div class="card space-y-5">
          <h3 class="text-base font-semibold text-gray-800">Bankverbindung</h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <FormInput v-model="form.iban" label="IBAN" placeholder="DE89370400440532013000" />
            <FormInput v-model="form.bic" label="BIC" placeholder="COBADEFFXXX" />
            <FormInput v-model="form.bank_name" label="Bankname" placeholder="Commerzbank" />
          </div>
        </div>

        <!-- Invoice settings -->
        <div class="card space-y-5">
          <h3 class="text-base font-semibold text-gray-800">Rechnungseinstellungen</h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <FormInput v-model="form.invoice_prefix" label="Rechnungspräfix" placeholder="RE" />
            <FormInput v-model="form.invoice_next_number" label="Nächste Rechnungsnr." type="number" />
            <FormInput v-model="form.quote_prefix" label="Angebotspräfix" placeholder="AN" />
          </div>
          <FormInput v-model="form.default_due_days" label="Standard Zahlungsziel (Tage)" type="number" />
          <FormInput v-model="form.footer_text" label="Fußzeile" type="textarea" placeholder="Text für die PDF-Fußzeile..." />
        </div>

        <!-- Logo -->
        <div class="card space-y-4">
          <h3 class="text-base font-semibold text-gray-800">Logo</h3>
          <div class="flex items-center gap-6">
            <div v-if="logoPreview" class="w-24 h-24 rounded-lg border border-gray-200 overflow-hidden bg-gray-50 flex items-center justify-center">
              <img :src="logoPreview" alt="Logo" class="max-w-full max-h-full object-contain" />
            </div>
            <div>
              <input
                type="file"
                accept="image/png,image/jpeg,image/svg+xml"
                class="block text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                @change="onLogoChange"
              />
              <p class="text-xs text-gray-400 mt-1">PNG, JPEG oder SVG. Wird lokal gespeichert.</p>
            </div>
          </div>
        </div>

        <div class="card space-y-4">
          <h3 class="text-base font-semibold text-gray-800">Daten-Backup</h3>
          <p class="text-sm text-gray-500">
            Exportieren Sie Ihre lokalen Daten als JSON-Datei oder importieren Sie eine vorhandene Sicherung.
          </p>
          <div class="flex flex-col sm:flex-row gap-3">
            <button type="button" class="btn-secondary" @click="handleExport">Daten exportieren</button>
            <label class="btn-secondary cursor-pointer text-center">
              {{ importing ? 'Import läuft...' : 'Daten importieren' }}
              <input
                type="file"
                accept="application/json"
                class="hidden"
                :disabled="importing"
                @change="handleImport"
              />
            </label>
          </div>
        </div>

        <!-- Save -->
        <div class="flex gap-3">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Speichern...' : 'Einstellungen speichern' }}
          </button>
        </div>
      </form>
        </div>

        <!-- Vorschau (rechts) -->
        <aside class="xl:w-[380px] xl:flex-shrink-0">
          <div class="xl:sticky xl:top-6">
            <h3 class="text-base font-semibold text-gray-800 mb-1">Vorschau</h3>
            <p class="text-sm text-gray-500 mb-3">Beispielrechnung mit Ihren Einstellungen</p>
            <div class="rounded-xl border border-gray-200 bg-white shadow-md overflow-hidden">
              <div class="bg-gray-50 px-4 py-2 border-b border-gray-200 text-[10px] text-gray-500">
                So erscheint die PDF
              </div>
              <div class="p-4 max-h-[calc(100vh-12rem)] overflow-auto">
                <article class="text-gray-800" style="font-size: 10px; line-height: 1.45;">
                  <header class="flex justify-between items-start border-b-2 border-primary-500 pb-2 mb-2">
                    <div class="flex-1 min-w-0 pr-2">
                      <img v-if="logoPreview" :src="logoPreview" alt="" class="max-h-14 max-w-[140px] object-contain mb-1" />
                      <div class="font-bold text-gray-900" style="font-size: 13px;">{{ form.name || 'Ihre Firma GmbH' }}</div>
                      <div class="text-gray-500 text-[9px] mt-0.5">
                        <template v-if="form.street">{{ form.street }}<br /></template>
                        <template v-if="form.zip || form.city">{{ form.zip }} {{ form.city }}<br /></template>
                        <span v-if="form.country">{{ form.country }}</span>
                        <span v-if="form.phone"> · {{ form.phone }}</span>
                        <span v-if="form.email"> · {{ form.email }}</span>
                      </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                      <div class="font-bold text-primary-600" style="font-size: 12px;">Rechnung</div>
                      <div class="text-gray-500 text-[9px]">{{ form.invoice_prefix }}-000042</div>
                      <div class="text-gray-500 text-[9px]">11.02.2025</div>
                      <div class="text-gray-500 text-[8px] mt-0.5">Zahlbar bis 25.02.2025</div>
                    </div>
                  </header>
                  <div class="flex justify-between gap-4 mb-3">
                    <div class="w-1/2">
                      <div class="text-[8px] uppercase text-gray-400 font-semibold mb-0.5">Rechnungsadresse</div>
                      <div class="text-[9px] font-semibold">Bäckerei Schmidt GmbH</div>
                      <div class="text-[9px] text-gray-600">
                        Hauptstraße 42<br />
                        80331 München<br />
                        Deutschland
                      </div>
                    </div>
                  </div>
                  <table class="w-full border-collapse mb-2" style="font-size: 9px;">
                    <thead>
                      <tr class="bg-gray-100">
                        <th class="text-left py-1.5 px-1.5 font-semibold text-gray-600 w-6">Pos.</th>
                        <th class="text-left py-1.5 px-1.5 font-semibold text-gray-600">Bezeichnung</th>
                        <th class="text-right py-1.5 px-1.5 font-semibold text-gray-600 w-10">Menge</th>
                        <th class="text-left py-1.5 px-1.5 font-semibold text-gray-600 w-12">Einheit</th>
                        <th class="text-right py-1.5 px-1.5 font-semibold text-gray-600 w-14">Einzelpreis</th>
                        <th class="text-right py-1.5 px-1.5 font-semibold text-gray-600 w-14">Netto</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr class="border-b border-gray-100">
                        <td class="py-1 px-1.5">1</td>
                        <td class="py-1 px-1.5">Beratung Projekt Website</td>
                        <td class="py-1 px-1.5 text-right">10</td>
                        <td class="py-1 px-1.5">Stunden</td>
                        <td class="py-1 px-1.5 text-right">95,00 €</td>
                        <td class="py-1 px-1.5 text-right">950,00 €</td>
                      </tr>
                      <tr class="border-b border-gray-100">
                        <td class="py-1 px-1.5">2</td>
                        <td class="py-1 px-1.5">Design Konzept & Wireframes</td>
                        <td class="py-1 px-1.5 text-right">1</td>
                        <td class="py-1 px-1.5">Stück</td>
                        <td class="py-1 px-1.5 text-right">450,00 €</td>
                        <td class="py-1 px-1.5 text-right">450,00 €</td>
                      </tr>
                      <tr class="border-b border-gray-100">
                        <td class="py-1 px-1.5">3</td>
                        <td class="py-1 px-1.5">Hosting (Jahresabo)</td>
                        <td class="py-1 px-1.5 text-right">1</td>
                        <td class="py-1 px-1.5">Jahr</td>
                        <td class="py-1 px-1.5 text-right">120,00 €</td>
                        <td class="py-1 px-1.5 text-right">120,00 €</td>
                      </tr>
                    </tbody>
                  </table>
                  <div class="flex justify-end mb-2">
                    <table style="min-width: 150px; font-size: 9px;">
                      <tr><td class="text-gray-500 py-0.5">Netto</td><td class="text-right py-0.5">1.520,00 €</td></tr>
                      <tr v-if="!form.kleinunternehmer"><td class="text-gray-500 py-0.5">MwSt. 19%</td><td class="text-right py-0.5">288,80 €</td></tr>
                      <tr class="border-t-2 border-primary-500 font-bold text-gray-900 pt-1.5 mt-0.5"><td>Gesamt</td><td class="text-right">{{ form.kleinunternehmer ? '1.520,00 €' : '1.808,80 €' }}</td></tr>
                    </table>
                  </div>
                  <div class="text-[8px] text-gray-500 mb-2">
                    Zahlung per Überweisung an: {{ form.bank_name || 'Ihre Bank' }} · IBAN DE89 3704 0044 0532 0130 00
                  </div>
                  <footer class="border-t border-gray-200 pt-2 text-center text-gray-500 text-[8px] whitespace-pre-line">
                    {{ form.footer_text || 'Vielen Dank für Ihr Vertrauen. Bei Fragen stehen wir gern zur Verfügung.' }}
                  </footer>
                </article>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>
