<script setup>
import { ref, watch, nextTick } from 'vue'
import CitationCard from './CitationCard.vue'
import { Bot, User, Loader2 } from '@lucide/vue'

const props = defineProps({
  messages: { type: Array, required: true },
  isLoading: { type: Boolean, default: false },
  sessionId: { type: [String, Number], default: null }
})

const scrollContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.isLoading, scrollToBottom)
</script>

<template>
  <div ref="scrollContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
    <div v-for="msg in messages" :key="msg.id" class="flex gap-4 max-w-3xl mx-auto"
      :class="{ 'justify-end': msg.sender === 'user' }">
      <div v-if="msg.sender !== 'user'"
        class="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
        <Bot class="w-4 h-4 text-indigo-400" />
      </div>

      <div class="space-y-3 max-w-xl">
        <div class="p-4 rounded-2xl text-sm leading-relaxed" :class="[
          msg.sender === 'user'
            ? 'bg-indigo-600 text-white rounded-br-none'
            : msg.sender === 'system'
              ? 'bg-slate-800 text-slate-300 border border-slate-700'
              : 'bg-slate-800/80 text-slate-200 border border-slate-700/60 rounded-bl-none'
        ]">
          {{ msg.text }}
        </div>

        <div v-if="msg.citations && msg.citations.length > 0" class="space-y-2">
          <p class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">( Sources )</p>
          <div class="grid grid-cols-1 gap-2">
            <CitationCard v-for="(cite, idx) in msg.citations" :key="idx" :citation="cite" />
          </div>
        </div>
      </div>

      <div v-if="msg.sender === 'user'"
        class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
        <User class="w-4 h-4 text-slate-300" />
      </div>
    </div>

    <div v-if="isLoading" class="flex gap-4 max-w-3xl mx-auto items-start">
      <div
        class="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
        <Bot class="w-4 h-4 text-indigo-400" />
      </div>
      <div
        class="p-4 rounded-2xl bg-slate-800/50 border border-slate-700/40 text-sm text-slate-400 rounded-tl-none flex items-center gap-2">
        <Loader2 class="w-4 h-4 text-indigo-400 mt-0.5 animate-spin" />
        Thinking
      </div>
    </div>
  </div>
</template>