import { defineStore } from 'pinia'
import { ref } from 'vue'
import { db, nowIso } from '@/db'
import {
  createDocument as createDocumentEntry,
  updateDocument as updateDocumentEntry,
  addPayment as addPaymentEntry,
  addReminder as addReminderEntry,
  updateStatus as updateStatusEntry,
  createPartialInvoice as createPartialInvoiceEntry,
  listRelatedDocuments,
  cancelDocument as cancelDocumentEntry,
  createCreditNote as createCreditNoteEntry,
  convertQuoteToInvoice,
} from '@/services/documentService'
import { buildDocumentPdfBlob } from '@/services/pdfService'
import { buildXRechnungXml, buildZugferdXml, downloadXml } from '@/services/einvoiceService'

const pdfBlobCache = new Map()

export const useDocumentsStore = defineStore('documents', () => {
  const documents = ref([])
  const currentDocument = ref(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const search = ref('')
  const filterType = ref('')
  const filterStatus = ref('')

  /**
   * Fetch paginated document list with optional filters from IndexedDB.
   * @param {{ page?: number, limit?: number, search?: string, document_type?: string, status?: string }} params
   */
  async function fetchDocuments(params = {}) {
    loading.value = true
    try {
      const pageNum = params.page ?? page.value
      const size = params.limit ?? pageSize.value
      const searchQuery = String(params.search ?? search.value ?? '').trim().toLowerCase()
      const documentType = params.document_type ?? filterType.value
      const status = params.status ?? filterStatus.value

      const allDocuments = await db.documents.toArray()
      const filtered = allDocuments
        .filter((entry) => !documentType || entry.document_type === documentType)
        .filter((entry) => !status || entry.status === status)
        .filter((entry) => {
          if (!searchQuery) return true
          const values = [entry.document_number, entry.customer_name, entry.notes].map((value) =>
            String(value || '').toLowerCase()
          )
          return values.some((value) => value.includes(searchQuery))
        })
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

      total.value = filtered.length
      const start = (pageNum - 1) * size
      documents.value = filtered.slice(start, start + size).map((entry) => ({ id: String(entry.id), ...entry }))
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single document by id.
   * @param {string} id
   */
  async function fetchDocument(id) {
    loading.value = true
    try {
      const data = await db.documents.get(Number(id))
      currentDocument.value = data ? { id: String(data.id), ...data } : null
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new document.
   * @param {object} payload
   */
  async function createDocument(payload) {
    return createDocumentEntry(payload)
  }

  /**
   * Update an existing document.
   * @param {string} id
   * @param {object} payload
   */
  async function updateDocument(id, payload) {
    return updateDocumentEntry(id, payload)
  }

  /**
   * Delete a draft document.
   * @param {string} id
   */
  async function deleteDocument(id) {
    const current = await db.documents.get(Number(id))
    if (!current) return
    if (current.status !== 'DRAFT') throw new Error('Nur Entwürfe können gelöscht werden')
    await db.documents.delete(Number(id))
  }

  /**
   * Add a partial payment to a document.
   * @param {string} id – document id
   * @param {{ amount: number, payment_method: string, note?: string }} payload
   */
  async function addPayment(id, payload) {
    const data = await addPaymentEntry(id, payload)
    currentDocument.value = data
    return data
  }

  /**
   * Add a reminder (Mahnung) to a document.
   * @param {string} id
   * @param {{ fee?: number, note?: string }} payload
   */
  async function addReminder(id, payload) {
    const data = await addReminderEntry(id, payload)
    currentDocument.value = data
    return data
  }

  /**
   * Update a document's status.
   * @param {string} id
   * @param {string} status
   */
  async function updateStatus(id, status) {
    const data = await updateStatusEntry(id, status)
    currentDocument.value = data
    return data
  }

  /**
   * Create a partial invoice from an existing invoice.
   * @param {string} id - parent invoice id
   * @param {{ amount: number, notes?: string }} payload
   */
  async function createPartialInvoice(id, payload) {
    return createPartialInvoiceEntry(id, payload)
  }

  /**
   * Fetch related documents (parent + children) for a document.
   * @param {string} id
   * @returns {{ parent: object|null, children: object[] }}
   */
  async function fetchRelatedDocuments(id) {
    return listRelatedDocuments(id)
  }

  /**
   * Cancel a document (Storno).
   * @param {string} id
   */
  async function cancelDocument(id) {
    return cancelDocumentEntry(id)
  }

  /**
   * Create a credit note from a document.
   * @param {string} id
   */
  async function createCreditNote(id) {
    return createCreditNoteEntry(id)
  }

  /**
   * Convert a quote to an invoice.
   * @param {string} id
   */
  async function convertToInvoice(id) {
    return convertQuoteToInvoice(id)
  }

  /**
   * Generate a PDF for a document and keep it in memory cache.
   * @param {string} id
   */
  async function generatePdf(id) {
    const document = await db.documents.get(Number(id))
    if (!document) throw new Error('Dokument nicht gefunden')
    const company = await db.company.orderBy('id').last()
    const customer = await db.customers.get(Number(document.customer_id))
    const blob = await buildDocumentPdfBlob(document, company, customer)
    pdfBlobCache.set(String(id), blob)
    await db.documents.update(Number(id), { ...document, updated_at: nowIso() })
    return { ok: true }
  }

  /**
   * Download PDF for a document.
   * @param {string} id
   * @returns {string} blob URL
   */
  async function downloadPdf(id) {
    if (!pdfBlobCache.has(String(id))) {
      await generatePdf(id)
    }
    return URL.createObjectURL(pdfBlobCache.get(String(id)))
  }

  /**
   * Generate and download XRechnung XML.
   * @param {string} id
   */
  async function getXRechnung(id) {
    const document = await db.documents.get(Number(id))
    if (!document) throw new Error('Dokument nicht gefunden')
    const company = await db.company.orderBy('id').last()
    const customer = await db.customers.get(Number(document.customer_id))
    const xml = buildXRechnungXml(document, company, customer)
    downloadXml(`${document.document_number || 'xrechnung'}.xml`, xml)
    return xml
  }

  /**
   * Generate and download ZUGFeRD XML.
   * @param {string} id
   */
  async function getZugferd(id) {
    const document = await db.documents.get(Number(id))
    if (!document) throw new Error('Dokument nicht gefunden')
    const company = await db.company.orderBy('id').last()
    const customer = await db.customers.get(Number(document.customer_id))
    const xml = buildZugferdXml(document, company, customer)
    downloadXml(`${document.document_number || 'zugferd'}.xml`, xml)
    return xml
  }

  return {
    documents, currentDocument, total, page, pageSize, loading, search,
    filterType, filterStatus,
    fetchDocuments, fetchDocument, createDocument, updateDocument, deleteDocument,
    updateStatus, createPartialInvoice, fetchRelatedDocuments,
    addPayment, addReminder, cancelDocument, createCreditNote, convertToInvoice,
    generatePdf, downloadPdf, getXRechnung, getZugferd,
  }
})
