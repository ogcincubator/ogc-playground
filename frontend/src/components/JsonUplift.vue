<template>
  <v-container>
    <v-row>
      <v-col>
        <h1 class="text-center">JSON Uplift</h1>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" md="6">
        <div>Context definition (YAML)</div>
        <codemirror
          v-model="yamlContext"
          :placeholder="yamlContextPlaceholder"
          :style="{ height: '400px' }"
          :autofocus="true"
          :indent-with-tab="true"
          :tab-size="2"
          :extensions="yamlExtensions"
        />
      </v-col>
      <v-col cols="12" md="6">
        <div>JSON content</div>
        <codemirror
          v-model="jsonContent"
          :placeholder="jsonPlaceholder"
          :style="{ height: '400px' }"
          :indent-with-tab="true"
          :tab-size="2"
          :extensions="jsonExtensions"
        />
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-col class="text-center" xs="6" sm="4">
        <v-select
          v-model="outputFormat"
          label="Output format"
          :items="outputFormats"
        >
        </v-select>
        <v-text-field
          v-model="baseUri"
          label="Base URI"
        >
        </v-text-field>
        <v-btn @click.prevent="uplift" :disabled="!jsonContent || !jsonContent.trim()">JSON Uplift</v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <div v-if="outputError" class="text-red-lighten-1">
          {{ outputError }}
        </div>
        <v-textarea
          variant="filled"
          v-if="outputText"
          class="output"
          v-model="outputText"
          auto-grow
        ></v-textarea>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { Codemirror } from 'vue-codemirror';
import { StreamLanguage } from '@codemirror/language';
import { yaml } from '@codemirror/legacy-modes/mode/yaml';
import { json as cmJson } from '@codemirror/lang-json';
import axios from 'axios';

const BACKEND_URL = process.env.VUE_APP_BACKEND_URL;

export default {
  name: 'JsonUplift',
  components: {
    Codemirror,
  },
  data: () => ({
    yamlContext: '',
    yamlContextPlaceholder: "transform:\n  - 'jq expression'\n\ncontext:\n  '$': {...}",
    yamlExtensions: [
      StreamLanguage.define(yaml),
    ],
    jsonContent: '',
    jsonPlaceholder: '{\n  "property": "value"\n}',
    jsonExtensions: [
        cmJson(),
    ],
    outputFormats: [
      { value: 'ttl', title: 'Turtle' },
      { value: 'json', title: 'Uplifted JSON-LD' },
      { value: 'expanded', title: 'Expanded JSON-LD' },
    ],
    outputFormat: 'ttl',
    baseUri: '',
    outputText: '',
    outputError: null,
  }),
  mounted() {
    this.yamlContext = localStorage.getItem("ogcPlayground.lastContext") || '';
    this.jsonContent = localStorage.getItem("ogcPlayground.lastJson") || '';
    this.baseUri = localStorage.getItem("ogcPlayground.lastBaseUri") || '';
  },
  methods: {
    uplift() {
      const formData = new FormData();
      localStorage.setItem("ogcPlayground.lastContext", this.yamlContext);
      localStorage.setItem("ogcPlayground.lastJson", this.jsonContent);
      localStorage.setItem("ogcPlayground.lastBaseUri", this.baseUri);
      formData.append('context', this.yamlContext);
      formData.append('json', this.jsonContent);
      formData.append('output', this.outputFormat);
      formData.append('base', this.baseUri);
      axios.post(`${BACKEND_URL}/json-uplift`, formData)
        .then(res => {
          this.outputText = typeof res.data === 'object' ? JSON.stringify(res.data, null, 2) : res.data;
          this.outputError = null;
        })
        .catch(err => {
          console.log(err);
          this.outputText = null;
          this.outputError = err;
        });
    },
  },
}
</script>
