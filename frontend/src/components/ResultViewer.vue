<template>
  <v-row v-if="output && formats && formats.length">
    <v-col>
      <v-row no-gutters>
        <v-col sm="9" md="6">
          <v-select
              v-model="selectedFormat"
              label="Output format"
              :items="formats"
          />
        </v-col>
        <v-col sm="3" md="6" class="text-right">
          <v-tooltip :text="copyToClipboardTooltip">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" @click.prevent="copyToClipboard" :icon="copyToClipboardIcon"></v-btn>
            </template>
          </v-tooltip>
        </v-col>
      </v-row>
      <v-row no-gutters>
        <v-col>
          <v-textarea
              variant="filled"
              class="output"
              v-model="outputText"
              :rows="15"
              :readonly="true"
          ></v-textarea>
        </v-col>
      </v-row>
    </v-col>
  </v-row>
  <v-row v-else>
    <v-col>
      <slot name="empty-text">No output is available for display.</slot>
    </v-col>
  </v-row>
</template>
<script>
export default {
  props: {
    formats: {
      type: Array,
      validator(v) {
        return Array.isArray(v) && v.every(e => e.value && e.title);
      },
    },
    output: {
      type: Object,
    },
    format: {
      type: String,
    },
  },
  data() {
    return {
      selectedFormat: null,
      copyToClipboardIcon: 'mdi-content-copy',
      copyToClipboardTimeout: null,
      copyToClipboardTooltip: 'Copy result to clipboard',
    };
  },
  mounted() {
    this.updateSelectedFormat();
  },
  methods: {
    copyToClipboard() {
      clearTimeout(this.copyToClipboardTimeout);
      this.copyToClipboardIcon = 'mdi-check-bold';
      this.copyToClipboardTooltip = 'Copied!'
      this.copyToClipboardTimeout = setTimeout(() => {
        this.copyToClipboardIcon = 'mdi-content-copy';
        this.copyToClipboardTooltip = 'Copy result to clipboard';
      }, 2000);
      navigator.clipboard.writeText(this.outputText);
    },
    updateSelectedFormat() {
      const v = this.formats;
      console.log("!formats")
      console.log(v, v.length, this.selectedFormat, v.find(e => e.value == this.selectedFormat));
      if (!v || !v.length || v.find(e => e.value == this.selectedFormat)) {
        return;
      }
      this.selectedFormat = v[0].value;
    },
  },
  computed: {
    outputText() {
      return this.output[this.selectedFormat] || '';
    },
  },
  watch: {
    format(v) {
      this.selectedFormat = v;
    },
    formats() {
      this.updateSelectedFormat();
    },
    selectedFormat(v) {
      this.$emit('update:format', v);
    },
  }
}
</script>
<style>
textarea {
  font-family: monospace;
}
</style>