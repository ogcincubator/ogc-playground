<template>
  <div class="process-pill d-inline-block">
    <div class="process-pill-content d-flex" :class="{ active }">
      <div v-if="startMarker" class="start-marker" :style="{ backgroundColor: bgColor, color: textColor }">
      </div>
      <div class="content" :style="{ backgroundColor: bgColor, color: textColor }">
        <slot></slot>
      </div>
      <div v-if="endMarker" class="end-marker" :style="{ backgroundColor: bgColor, color: textColor }">
      </div>
    </div>
  </div>
</template>
<script>
export default {
  props: {
    startMarker: {
      type: Boolean,
      default: true,
    },
    endMarker: {
      type: Boolean,
      default: true,
    },
    bgColor: {
      type: String,
      default: '#00b1ff',
    },
    textColor: {
      type: String,
      default: 'white',
    },
    active: {
      type: Boolean,
      default: false,
    },
  },
}
</script>
<style>
.start-marker {
  min-width: 0.8em;
  clip-path: polygon(0% 0%, 100% 50%, 0% 100%, 100% 100%, 100% 0%);
}
.end-marker {
  min-width: 0.8em;
  clip-path: polygon(0% 0%, 100% 50%, 0% 100%);
}
.process-pill-content .content {
  padding: 0.3em 0.5em;
}
.process-pill-content {
  cursor: pointer;
}
.process-pill-content:hover {
  opacity: 0.8;
}
.process-pill-content.active {
  font-weight: bold;
}
</style>