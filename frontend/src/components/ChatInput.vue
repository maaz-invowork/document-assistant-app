<script setup>
import { ref } from 'vue'
import { ArrowRight, Paperclip, X } from '@lucide/vue'
import DocumentUpload from './DocumentUpload.vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  sessionId: { type: [String, Number], default: null },
  documents: { type: Array, default: () => [] },
})

const emit = defineEmits(['send', 'uploaded', 'document-deleted'])
const inputQuery = ref('')
const isUploadModalOpen = ref(false)

const handleUploaded = (filename) => {
  isUploadModalOpen.value = false
  emit('uploaded', filename)
}

const submit = () => {
  if (inputQuery.value.trim() && !props.disabled) {
    emit('send', inputQuery.value)
    inputQuery.value = ''
  }
}

const handleDeleted = (docId) => {
  emit('document-deleted', docId)
}
</script>

<template>
  <div class="p-4 border-t border-slate-800 bg-slate-950/50">
    <form @submit.prevent="submit" class="max-w-3xl mx-auto flex items-center gap-2">
      <button type="button" :disabled="disabled"
        class="relative shrink-0 p-3 border border-slate-700/80 rounded-full text-slate-400 hover:text-indigo-400 hover:border-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Manage context files" aria-label="Manage context files" @click="isUploadModalOpen = true">
        <Paperclip class="w-4 h-4" />
        <span v-if="documents.length > 0"
          class="absolute -top-1 -right-1 bg-indigo-600 text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center border-2 border-slate-950">
          {{ documents.length }}
        </span>
      </button>
      <div class="bg-transparent flex justify-center items-center gap-2 w-full border border-slate-500 rounded-full">
        <input v-model="inputQuery" type="text" placeholder="Ask a question" :disabled="disabled"
          class="bg-transparent border-0 px-3 py-3 text-sm text-slate-100 placeholder-slate-500 disabled:opacity-50 flex-1 min-w-0 focus:outline-none" />
        <button type="submit" :disabled="disabled || !inputQuery.trim()"
          class="bg-indigo-500 hover:bg-indigo-400 text-white px-2 py-2 mr-2 flex items-center justify-center transition-colors rounded-full">
          <ArrowRight class="w-4 h-4" />
        </button>
      </div>
    </form>

    <div v-if="isUploadModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div class="relative w-full max-w-md rounded-xl border border-slate-800 bg-slate-950 p-6 shadow-2xl">
        <button type="button" class="absolute right-4 top-4 text-slate-500 hover:text-slate-200 transition-colors"
          title="Close upload dialog" aria-label="Close upload dialog" @click="isUploadModalOpen = false">
          <X class="w-5 h-5" />
        </button>
        <DocumentUpload :session-id="sessionId" :documents="documents" :disabled="disabled" @uploaded="handleUploaded" @deleted="handleDeleted" />
      </div>
    </div>
  </div>
</template>