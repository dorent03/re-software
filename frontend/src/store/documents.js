import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

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
   * Fetch paginated document list with optional filters.
   * @param {{ page?: number, limit?: number, search?: string, document_type?: string, status?: string }} params
   */
  async function fetchDocuments(params = {}) {
    loading.value = true
    try {
      const pageNum = params.page ?? page.value
      const size = params.limit ?? pageSize.value
      const query = {
        page: pageNum,
        page_size: size,
      }
      if (params.search || search.value) query.search = params.search || search.value
      if (params.document_type || filterType.value) query.document_type = params.document_type || filterType.value
      if (params.status || filterStatus.value) query.status = params.status || filterStatus.value

      const { data } = await api.get('/documents/', { params: query })
      documents.value = data.items ?? []
      total.value = data.total ?? documents.value.length
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
      const { data } = await api.get(`/documents/${id}`)
      currentDocument.value = data
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new document.
   * @param {object} payload
   */
  async function createDocument(payload) {
    const { data } = await api.post('/documents/', payload)
    return data
  }

  /**
   * Update an existing document.
   * @param {string} id
   * @param {object} payload
   */
  async function updateDocument(id, payload) {
    const { data } = await api.patch(`/documents/${id}`, payload)
    return data
  }

  /**
   * Delete a draft document.
   * @param {string} id
   */
  async function deleteDocument(id) {
    await api.delete(`/documents/${id}`)
  }

  /**
   * Add a partial payment to a document.
   * @param {string} id – document id
   * @param {{ amount: number, payment_method: string, note?: string }} payload
   */
  async function addPayment(id, payload) {
    const { data } = await api.post(`/documents/${id}/payment`, payload)
    currentDocument.value = data
    return data
  }

  /**
   * Add a reminder (Mahnung) to a document.
   * @param {string} id
   * @param {{ fee?: number, note?: string }} payload
   */
  async function addReminder(id, payload) {
    const { data } = await api.post(`/documents/${id}/reminder`, payload)
    currentDocument.value = data
    return data
  }

  /**
   * Update a document's status.
   * @param {string} id
   * @param {string} status
   */
  async function updateStatus(id, status) {
    const { data } = await api.patch(`/documents/${id}/status`, { status })
    currentDocument.value = data
    return data
  }

  /**
   * Create a partial invoice from an existing invoice.
   * @param {string} id - parent invoice id
   * @param {{ amount: number, notes?: string }} payload
   */
  async function createPartialInvoice(id, payload) {
    const { data } = await api.post(`/documents/${id}/create-partial`, payload)
    return data
  }

  /**
   * Fetch related documents (parent + children) for a document.
   * @param {string} id
   * @returns {{ parent: object|null, children: object[] }}
   */
  async function fetchRelatedDocuments(id) {
    const { data } = await api.get(`/documents/${id}/related`)
    return data
  }

  /**
   * Cancel a document (Storno).
   * @param {string} id
   */
  async function cancelDocument(id) {
    const { data } = await api.post(`/documents/${id}/cancel`)
    return data
  }

  /**
   * Create a credit note from a document.
   * @param {string} id
   */
  async function createCreditNote(id) {
    const { data } = await api.post(`/documents/${id}/credit`)
    return data
  }

  /**
   * Convert a quote to an invoice.
   * @param {string} id
   */
  async function convertToInvoice(id) {
    const { data } = await api.post(`/documents/${id}/convert`)
    return data
  }

  /**
   * Generate the PDF for a document (must be called before preview/download).
   * @param {string} id
   */
  async function generatePdf(id) {
    const { data } = await api.post(`/documents/${id}/pdf`)
    return data
  }

  /**
   * Download PDF for a document.
   * @param {string} id
   * @returns {string} blob URL
   */
  async function downloadPdf(id) {
    // Ensure PDF is generated first
    await api.post(`/documents/${id}/pdf`)
    const { data } = await api.get(`/documents/${id}/pdf/download`, { responseType: 'blob' })
    return URL.createObjectURL(data)
  }

  /**
   * Get XRechnung XML.
   * @param {string} id
   */
  async function getXRechnung(id) {
    const { data } = await api.get(`/documents/${id}/xrechnung`, { responseType: 'blob' })
    return URL.createObjectURL(data)
  }

  /**
   * Get ZUGFeRD PDF+XML.
   * @param {string} id
   */
  async function getZugferd(id) {
    const { data } = await api.get(`/documents/${id}/zugferd`, { responseType: 'blob' })
    return URL.createObjectURL(data)
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
