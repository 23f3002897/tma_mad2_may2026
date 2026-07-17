<template>
  <div v-if="message" :class="['alert', `alert-${type}`, dismissible ? 'alert-dismissible fade show' : '']" role="alert">
    <div class="d-flex align-items-center">
      <span class="me-2 fs-5">
        <i v-if="type === 'success'" class="bi bi-check-circle-fill">✅</i>
        <i v-else-if="type === 'danger'" class="bi bi-exclamation-triangle-fill">⚠️</i>
        <i v-else-if="type === 'warning'" class="bi bi-exclamation-circle-fill">⚡</i>
        <i v-else class="bi bi-info-circle-fill">ℹ️</i>
      </span>
      <div>{{ message }}</div>
    </div>
    <button v-if="dismissible" type="button" class="btn-close" @click="$emit('close')" aria-label="Close"></button>
  </div>
</template>

<script>
export default {
  name: 'Alert',
  props: {
    message: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'info' // success, danger, warning, info
    },
    dismissible: {
      type: Boolean,
      default: true
    }
  },
  emits: ['close']
}
</script>
