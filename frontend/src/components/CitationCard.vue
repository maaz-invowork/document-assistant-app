<script setup>

defineProps({
  citation: {
    type: Object,
    required: true
    // Structure: { filename: string, page_number: number, source_text: string }
  }
})
</script>

<template>
  <div class="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs text-slate-300 space-y-1">
    <div class="flex items-center font-semibold text-indigo-400">
      <span>{{citation.filename}} - Page {{ citation.page_number}}</span>
    </div>
    <p class="text-slate-400 italic leading-relaxed">
      "{{ citation.source_text}}"
    </p>
  </div>
</template>