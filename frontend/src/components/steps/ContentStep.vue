<template>
  <source-loader
      @change="sourceLoaderChanged"
      class="mb-4"
      :profile-roles="['http://www.w3.org/ns/dx/prof/role/validation']"
  />
  <yaml-json-editor
      :model-value="step.contents"
      @update:modelValue="$emit('update', { contents: $event })"
      :mode="step.mode"
      @update:mode="$emit('update', { mode: $event })"
  />
</template>

<script>
import SourceLoader from "@/components/SourceLoader.vue";
import YamlJsonEditor from "@/components/YamlJsonEditor.vue";

export default {
  components: {
    YamlJsonEditor,
    SourceLoader,
  },
  props: {
    step: {
      type: Object,
      required: true,
    },
  },
  emits: [
    'update'
  ],
  data() {
    return {};
  },
  methods: {
    sourceLoaderChanged(v) {
      let mode = 'json';
      try {
        JSON.parse(v);
      } catch {
        mode = 'yaml';
      }
      this.$emit('update', {
        contents: v,
        mode,
      });
    },
  },
}
</script>