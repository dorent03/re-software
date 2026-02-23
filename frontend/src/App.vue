<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import Navbar from '@/components/Navbar.vue'

const route = useRoute()
const isBlankLayout = computed(() => route.meta.layout === 'blank')
</script>

<template>
  <!-- Blank layout: Login / Register -->
  <div v-if="isBlankLayout" class="min-h-screen flex items-center justify-center bg-gray-100">
    <router-view />
  </div>

  <!-- Main layout with sidebar + navbar -->
  <div v-else class="min-h-screen flex">
    <Sidebar />
    <div class="flex-1 flex flex-col min-w-0">
      <Navbar />
      <main class="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
        <router-view />
      </main>
    </div>
  </div>
</template>
