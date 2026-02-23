<script setup>
import Sidebar from '@/components/Sidebar.vue'
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <div class="min-h-screen flex">
    <Sidebar />
    <div class="flex-1 flex flex-col min-w-0">
      <Navbar />
      <main class="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
        <router-view />
      </main>
    </div>
  </div>
</template>
