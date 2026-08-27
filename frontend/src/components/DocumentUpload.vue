<script setup>
import { ref, computed } from 'vue'
import { uploadPdf, deleteDocument } from '../services/api'
import { UploadCloud, Loader2, FileText, CheckCircle2, Trash } from '@lucide/vue'

const props = defineProps({
  sessionId: {
    type: String,
    default: null
  },
  documents: {
    type: Array,
    default: () => []
  },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['uploaded', 'deleted'])
const isUploading = ref(false)
const errorMsg = ref('')
const uploadedFiles = ref([])

// Combine prop documents with locally uploaded ones to eliminate duplicates
const allDocuments = computed(() => {
  const propList = props.documents.map(doc => (typeof doc === 'string' ? doc : doc.filename))
  const combined = [...propList, ...uploadedFiles.value]
  return [...new Set(combined)]
})

const handleFileUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  if (file.type !== 'application/pdf') {
    errorMsg.value = 'Please select a valid PDF file.'
    return
  }

  errorMsg.value = ''
  isUploading.value = true

  try {
    const res = await uploadPdf(file, props.sessionId)
    const newFilename = res.filename || file.name
    if (!uploadedFiles.value.includes(newFilename)) {
      uploadedFiles.value.push(newFilename)
    }
    emit('uploaded', newFilename)
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Failed to upload PDF.'
  } finally {
    isUploading.value = false
    event.target.value = ''
  }
}

const handleRemoveDoc = async (docId) => {
  try {
    await deleteDocument(docId)
    emit('deleted', docId)
  } catch (err) {
    console.error('Failed to delete document:', err)
  }
}
</script>

<template>
  <div class="space-y-3">
    <label class="block text-[14px] font-light tracking-wider text-slate-400">
      Add Knowledge Source
    </label>

    <label
      class="flex flex-col items-center justify-center p-6 border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl cursor-pointer bg-slate-900/50 hover:bg-slate-900 transition-all text-center group"
      :class="{ 'opacity-50 pointer-events-none': isUploading || disabled }"
    >
      <Loader2 v-if="isUploading" class="w-8 h-8 text-indigo-400 animate-spin mb-2" />
      <UploadCloud v-else class="w-8 h-8 text-slate-400 group-hover:text-indigo-400 mb-2 transition-colors" />

      <span class="text-sm font-medium text-slate-300">
        {{ isUploading ? 'Processing PDF...' : 'Upload PDF Document' }}
      </span>
      <span class="text-xs text-slate-500 mt-1">Drag & drop or click to browse</span>

      <input type="file" accept=".pdf" class="hidden" :disabled="isUploading || disabled" @change="handleFileUpload" />
    </label>

    <!-- Uploaded Documents List -->
    <div v-if="documents.length > 0" class="space-y-2 max-h-48 overflow-y-auto pr-1">
      <div v-for="doc in documents" :key="doc.id" class="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800 text-xs">
        <div class="flex items-center gap-2 truncate">
          <FileText class="w-4 h-4 text-indigo-400 shrink-0" />
          <span class="text-slate-300 truncate">{{ doc.filename }}</span>
        </div>
        <button @click="handleRemoveDoc(doc.id)" class="p-1 text-slate-500 hover:text-red-400 transition-colors bg-indigo-500/10 rounded-xl hover:bg-indigo-500/20" title="Remove document">
          <Trash class="w-3.5 h-3.5 text-indigo-500" />
        </button>
      </div>
    </div>

    <p v-if="errorMsg" class="text-xs text-rose-400 mt-1">{{ errorMsg }}</p>
  </div>
</template>