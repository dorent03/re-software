<script setup>
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  error: { type: String, default: '' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  id: { type: String, default: '' },
  /** For select inputs: [{ value, label }] */
  options: { type: Array, default: () => [] },
  /** Multi-line textarea */
  rows: { type: Number, default: 3 },
})

const emit = defineEmits(['update:modelValue'])

function onInput(event) {
  const val = props.type === 'number' ? Number(event.target.value) : event.target.value
  emit('update:modelValue', val)
}
</script>

<template>
  <div>
    <label v-if="label" :for="id" class="label-text">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <!-- Select -->
    <select
      v-if="type === 'select'"
      :id="id"
      :value="modelValue"
      :disabled="disabled"
      class="input-field"
      :class="{ '!border-red-400 !ring-red-400': error }"
      @change="emit('update:modelValue', $event.target.value)"
    >
      <option value="" disabled>{{ placeholder || 'Bitte wählen' }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>

    <!-- Textarea -->
    <textarea
      v-else-if="type === 'textarea'"
      :id="id"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows"
      class="input-field resize-y"
      :class="{ '!border-red-400 !ring-red-400': error }"
      @input="onInput"
    />

    <!-- Standard input -->
    <input
      v-else
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :step="type === 'number' ? 'any' : undefined"
      class="input-field"
      :class="{ '!border-red-400 !ring-red-400': error }"
      @input="onInput"
    />

    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>
  </div>
</template>
