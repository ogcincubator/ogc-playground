<template>
  <div class="d-flex flex-column justify-center">
    <codemirror
        :modelValue="modelValue"
        @update:modelValue="$emit('update:modelValue', $event)"
        :placeholder="placeholder"
        :style="textFieldStyle"
        :autofocus="autofocus"
        :indent-with-tab="true"
        :tab-size="2"
        :extensions="extensions"
        :disabled="readonly"
    />
    <v-btn-toggle
        v-if="showModeButtons"
        v-model="jsonMode"
        mandatory class="d-flex justify-center">
      <v-btn :value="true">JSON</v-btn>
      <v-btn :value="false">YAML</v-btn>
    </v-btn-toggle>
  </div>
</template>
<script>
import {StreamLanguage} from "@codemirror/language";
import {yaml as yamlMode} from "@codemirror/legacy-modes/mode/yaml";
import {json as cmJson} from "@codemirror/lang-json";
import jsYaml from "js-yaml";
import {Codemirror} from "vue-codemirror";

export default {
  components: {
    Codemirror,
  },
  props: {
    modelValue: String,
    placeholder: String,
    showModeButtons: {
      type: Boolean,
      default: true,
    },
    textFieldStyle: {
      type: Object,
      default() {
        return {
          height: '400px',
        };
      },
    },
    autofocus: Boolean,
    readonly: {
      type: Boolean,
      default: false,
    },
    mode: {
      type: String,
      default: 'json',
      validator(v) {
        return ['json', 'yaml'].includes(v);
      },
    },
  },
  data() {
    return {
      jsonExtensions: [
          cmJson(),
      ],
      yamlExtensions: [
        StreamLanguage.define(yamlMode),
      ],
      jsonMode: true,
    }
  },
  computed: {
    extensions() {
      return this.jsonMode ? this.jsonExtensions : this.yamlExtensions;
    }
  },
  watch: {
    jsonMode(v) {
      if (this.modelValue.trim()) {
        try {
          if (v) {
            this.$emit('update:modelValue', JSON.stringify(jsYaml.load(this.modelValue), null, 2));
          } else {
            this.$emit('update:modelValue', jsYaml.dump(JSON.parse(this.modelValue)));
          }
        } catch {
          // ignore
        }
      }
      this.$emit('update:mode', v ? 'json' : 'yaml');
    },
    mode(v) {
      this.jsonMode = v === 'json';
    },
  },
}
</script>