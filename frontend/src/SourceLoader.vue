<template>
  <v-menu>
    <template v-slot:activator="{ props }">
      <v-btn
        color="primary"
        v-bind="props"
        class="ml-1"
      >
        Load from...
        <v-icon>mdi-menu-down</v-icon>
      </v-btn>
    </template>
    <v-list density="compact">
      <v-list-item v-for="opt of menuOptions" :key="opt.text" :link="true">
        <v-list-item-title v-if="showFile" @click="clickedOption(opt.click)">
          <v-icon v-if="opt.icon" :icon="'mdi-' + opt.icon"></v-icon>
          {{ opt.text }}
        </v-list-item-title>
      </v-list-item>
    </v-list>

    <input type="file" ref="fileField" @change="fileSelected" :accept="fileAccept"/>

  </v-menu>
</template>
<script>
export default {
  props: {
    showFile: {
      type: Boolean,
      default: true,
    },
    showUrl: {
      type: Boolean,
      default: true,
    },
    fileAccept: {
      type: String,
      default: '.yml,.yaml,.json,.jsonld,.json-ld,text/yaml,application/json,application/x-yaml,application/ld+json',
    },
  },
  data() {
    return {
      file: null,
    };
  },
  methods: {
    clickedOption(func) {
      this[func]();
    },
    loadFile() {
      this.$refs.fileField.click();
    },
    loadUrl() {
      console.log('url');
    },
    fileSelected(ev) {
      const files = ev.target.files;
      if (files && files.length) {
        const file = files[0];
        const reader = new FileReader();
        reader.onload = (res) => {
          this.$emit('change', res.target.result);
        };
        reader.onerror = (err) => {
          alert('An error was encountered while reading the file');
          console.log(err);
        };
        reader.readAsText(file);
      }
    },
  },
  computed: {
    menuOptions() {
      const opts = [];
      if (this.showFile) {
        opts.push({ icon: 'file', text: 'File', click: 'loadFile' });
      }
      if (this.showUrl) {
        opts.push({ icon: 'web', text: 'URL', click: 'loadUrl' })
      }
      return opts;
    },
  },
}
</script>
<style>
input[type=file] {
  display: none;
}
</style>