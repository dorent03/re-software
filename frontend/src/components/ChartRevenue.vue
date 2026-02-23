<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  /** @type {{ month: number, year: number, total: number }[]} */
  data: { type: Array, default: () => [] },
  title: { type: String, default: 'Monatlicher Umsatz' },
})

const MONTH_LABELS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

const chartData = computed(() => {
  const arr = Array.isArray(props.data) ? props.data : []
  return {
  labels: arr.map((d) => `${MONTH_LABELS[(d.month || 1) - 1]} ${d.year || ''}`),
  datasets: [
    {
      label: 'Umsatz (€)',
      data: arr.map((d) => d.total_gross ?? d.total ?? 0),
      backgroundColor: '#3b82f6',
      borderRadius: 6,
      barThickness: 32,
    },
  ],
}
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) =>
          new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(ctx.raw),
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (v) => `${(v / 1000).toFixed(0)}k €`,
      },
    },
  },
}
</script>

<template>
  <div>
    <h3 v-if="title" class="text-sm font-semibold text-gray-700 mb-3">{{ title }}</h3>
    <div class="h-64">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
