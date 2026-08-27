<script setup>
import { ref, onMounted } from 'vue'
import ChatWindow from './components/ChatWindow.vue'
import ChatInput from './components/ChatInput.vue'
import {
  createSession,
  getSessions,
  getSessionDocuments,
  getSessionMessages,
  deleteSession,
  queryDocument
} from './services/api'
import { Plus, Trash2, MessageSquarePlus } from '@lucide/vue'


const sessions = ref([])
const activeSessionId = ref(null)
const currentDocument = ref(null)
const sessionDocuments = ref([])
const messages = ref([])
const isLoading = ref(false)

const sessionToDelete = ref(null)
const isDeleteModalOpen = ref(false)

const loadSessions = async () => {
  try {
    const data = await getSessions()
    sessions.value = data
    if (data.length > 0 && !activeSessionId.value) {
      await selectSession(data[0].id)
    }
  } catch (err) {
    console.error('Failed to load sessions:', err)
  }
}

const handleNewSession = async () => {
  try {
    const newSession = await createSession()
    sessions.value.push(newSession)
    currentDocument.value = null
    await selectSession(newSession.id)
  } catch (err) {
    console.error('Failed to create session:', err)
  }
}

const openDeleteModal = (session) => {
  sessionToDelete.value = session
  isDeleteModalOpen.value = true
}

const confirmDeleteSession = async () => {
  if (!sessionToDelete.value) return
  const session = sessionToDelete.value

  try {
    await deleteSession(session.id)
    const remainingSessions = sessions.value.filter(item => item.id !== session.id)
    sessions.value = remainingSessions

    if (session.id === activeSessionId.value) {
      activeSessionId.value = null
      messages.value = []
      currentDocument.value = null
      
      if (remainingSessions.length > 0) {
        await selectSession(remainingSessions[0].id)
      }
    }
  } catch (err) {
    console.error('Failed to delete session:', err)
  } finally {
    isDeleteModalOpen.value = false
    sessionToDelete.value = null
  }
}

const selectSession = async (sessionId) => {
  activeSessionId.value = sessionId
  currentDocument.value = null
  isLoading.value = true
  try {
    const [rawMessages, docs] = await Promise.all([
      getSessionMessages(sessionId),
      getSessionDocuments(sessionId)
    ])
    messages.value = rawMessages.map(msg => ({
      id: msg.id,
      sender: msg.sender,
      text: msg.text,
      citations: msg.citations_json ? JSON.parse(msg.citations_json) : []
    }))
    sessionDocuments.value = docs
  } catch (err) {
    console.error('Failed to load message history:', err)
  } finally {
    isLoading.value = false
  }
}

const handleDocumentUploaded = async (filename) => {
  currentDocument.value = filename
  if (activeSessionId.value) {
    sessionDocuments.value = await getSessionDocuments(activeSessionId.value)
  }
  messages.value.push({
    id: Date.now(),
    sender: 'system',
    text: `Document "${filename}" processed and indexed successfully.`
  })
}

const handleSendMessage = async (question) => {
  if (!question.trim() || isLoading.value || !activeSessionId.value) return

  messages.value.push({
    id: Date.now(),
    sender: 'user',
    text: question
  })

  isLoading.value = true

  try {
    const response = await queryDocument(question, activeSessionId.value)
    messages.value.push({
      id: Date.now() + 1,
      sender: 'assistant',
      text: response.answer,
      citations: response.citations || []
    })
  } catch (error) {
    messages.value.push({
      id: Date.now() + 1,
      sender: 'assistant',
      text: 'Sorry, an error occurred while processing your request.',
      isError: true
    })
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<template>
  <div class="flex h-screen bg-slate-900 text-slate-100 font-sans relative">
    <aside class="w-80 border-r border-slate-800 p-6 flex flex-col justify-between bg-slate-950">
      <div class="space-y-6 flex flex-col h-full overflow-hidden">
        <div class="flex items-center justify-center pb-6 border-b border-slate-800">
          <p class="text-[32px]/7 font-light tracking-widest">Ragify</p>
        </div>

        <div class="flex-1 overflow-y-auto space-y-2 pr-1">
          <button @click="handleNewSession"
            class="p-2 mt-2 bg-transparent flex gap-2 items-center border border-indigo-500 py-1 w-full hover:bg-indigo-500/10 text-white rounded-lg transition-colors shrink-0 text-sm mb-4 justify-center"
            title="New Conversation">
            <Plus class="w-4 h-4" />
            New Conversation
          </button>

          <div v-for="s in sessions" :key="s.id" @click="selectSession(s.id)"
            class="p-2 rounded-lg flex items-center gap-2 cursor-pointer text-xs transition-colors" :class="[
              s.id === activeSessionId
                ? 'bg-indigo-600/20 border border-indigo-500/40 text-indigo-300'
                : 'bg-slate-900/60 hover:bg-slate-900 text-slate-400 border border-slate-800/80'
            ]">
            <span class="truncate">{{ s.title }}</span>
            <button @click.stop="openDeleteModal(s)"
              class="ml-auto shrink-0 p-1 text-slate-500 hover:text-red-400 transition-colors"
              :aria-label="`Delete ${s.title}`" title="Delete chat">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col h-full bg-slate-900">
      <template v-if="activeSessionId">
        <ChatWindow :messages="messages" :is-loading="isLoading" :session-id="activeSessionId"
          />
        <ChatInput
          :disabled="isLoading || !activeSessionId"
          :session-id="activeSessionId"
          :documents="sessionDocuments"
          @send="handleSendMessage"
          @uploaded="handleDocumentUploaded"
          @document-deleted="selectSession(activeSessionId)"        />
      </template>

      <div v-else class="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div class="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-full mb-4 text-indigo-400">
          <MessageSquarePlus class="w-10 h-10" />
        </div>
        <h2 class="text-xl font-semibold text-slate-200 mb-2">No active session</h2>
        <p class="text-slate-400 text-sm max-w-sm mb-6">
          Start a new conversation to begin uploading documents and querying the assistant.
        </p>
      </div>
    </main>

    <div v-if="isDeleteModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div class="bg-slate-950 border border-slate-800 rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
        <h3 class="text-lg font-semibold text-slate-100">Delete Conversation</h3>
        <p class="text-slate-400 text-sm pb-6">
          Are you sure you want to delete <span class="text-slate-200 font-medium">"{{ sessionToDelete?.title }}"</span>? This will permanently erase all associated messages.
        </p>
        <div class="flex justify-end gap-3 pt-2">
          <button @click="isDeleteModalOpen = false"
            class="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg transition-colors">
            Cancel
          </button>
          <button @click="confirmDeleteSession"
            class="px-4 py-2 text-xs font-medium text-white bg-red-600 hover:bg-red-500 rounded-lg transition-colors shadow-lg shadow-red-600/20">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
