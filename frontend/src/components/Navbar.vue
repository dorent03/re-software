<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => route.meta.title || 'RE-Software')
</script>

<template>
  <header class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 md:px-6">
    <!-- Page title -->
    <h1 class="text-lg font-semibold text-gray-800 truncate ml-10 lg:ml-0">
      {{ pageTitle }}
    </h1>

    <!-- Right side -->
    <div class="flex items-center gap-4">
      <span class="hidden sm:block text-sm text-gray-600">Lokaler Modus</span>
    </div>
  </header>
</template>
