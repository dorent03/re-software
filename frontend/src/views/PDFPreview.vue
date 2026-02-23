<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocumentsStore } from '@/store/documents'

const route = useRoute()
const router = useRouter()
const docStore = useDocumentsStore()

const pdfUrl = ref('')
const loading = ref(true)
const error = ref('')

/** PDF URL with toolbar hidden for a cleaner in-app look (Chrome/Edge support #toolbar=0). */
const pdfViewUrl = computed(() => {
  if (!pdfUrl.value) return ''
  const sep = pdfUrl.value.includes('?') ? '&' : '#'
  return `${pdfUrl.value}${sep}toolbar=0&navpanes=0&scrollbar=1`
})

onMounted(async () => {
  try {
    pdfUrl.value = await docStore.downloadPdf(route.params.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'PDF konnte nicht geladen werden'
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
  }
})

function downloadPdf() {
  if (!pdfUrl.value) return
  const a = document.createElement('a')
  a.href = pdfUrl.value
  a.download = `dokument-${route.params.id}.pdf`
  a.click()
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-100">
    <!-- Toolbar -->
    <div class="flex-shrink-0 bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
      <div class="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <button
            class="text-sm text-gray-600 hover:text-gray-900 font-medium"
            @click="router.push(`/documents/${route.params.id}`)"
          >
            &larr; Zurück
          </button>
          <span class="text-gray-400">|</span>
          <h2 class="text-base font-semibold text-gray-800">PDF-Vorschau</h2>
        </div>
        <div class="flex gap-2">
          <button
            class="btn-secondary btn-sm"
            :disabled="!pdfUrl"
            @click="pdfUrl && window.open(pdfUrl, '_blank')"
          >
            In neuem Tab
          </button>
          <button class="btn-primary btn-sm" :disabled="!pdfUrl" @click="downloadPdf">
            Herunterladen
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center py-20">
      <div class="text-center">
        <svg class="animate-spin h-10 w-10 mx-auto text-primary-500 mb-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p class="text-sm text-gray-500">PDF wird geladen...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center py-20">
      <div class="text-center max-w-md">
        <p class="text-red-600 font-medium mb-4">{{ error }}</p>
        <button class="btn-secondary btn-sm" @click="router.push('/documents')">
          Zurück zur Dokumentliste
        </button>
      </div>
    </div>

    <!-- PDF: paper-style container, no browser toolbar -->
    <div v-else class="flex-1 p-4 md:p-6 overflow-auto">
      <div class="max-w-4xl mx-auto rounded-lg bg-white shadow-lg overflow-hidden border border-gray-200">
        <iframe
          :src="pdfViewUrl"
          class="w-full block"
          style="height: calc(100vh - 140px); min-height: 560px;"
          type="application/pdf"
          title="PDF Vorschau"
        />
      </div>
    </div>
  </div>
</template>
