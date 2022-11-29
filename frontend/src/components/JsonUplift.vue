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
        <v-select
            v-model="yamlContext.type"
            label="Source"
            :items="inputSources"
        ></v-select>
        <codemirror
            v-if="yamlContext.type == 'content'"
            v-model="yamlContext.content"
            :placeholder="yamlContext.placeholder"
            :style="{ height: '400px' }"
            :autofocus="true"
            :indent-with-tab="true"
            :tab-size="2"
            :extensions="yamlExtensions"
        />
        <v-text-field
            v-if="yamlContext.type == 'url'"
            v-model="yamlContext.url"
            label="YAML context definition URL"
            placeholder="https://..."
        ></v-text-field>
        <v-file-input
            v-if="yamlContext.type == 'file'"
            v-model="yamlContext.file"
            label="YAML context definition file"
        ></v-file-input>
      </v-col>
      <v-col cols="12" md="6">
        <div>JSON content</div>
        <v-select
            v-model="jsonContent.type"
            label="Source"
            :items="inputSources"
        ></v-select>
        <codemirror
            v-if="jsonContent.type == 'content'"
            v-model="jsonContent.content"
            :placeholder="jsonContent.placeholder"
            :style="{ height: '400px' }"
            :indent-with-tab="true"
            :tab-size="2"
            :extensions="jsonExtensions"
        />
        <v-text-field
            v-if="jsonContent.type == 'url'"
            v-model="jsonContent.url"
            label="JSON document URL"
            placeholder="https://..."
        ></v-text-field>
        <v-file-input
            v-if="jsonContent.type == 'file'"
            v-model="jsonContent.file"
            label="JSON input file"
        ></v-file-input>
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
        <v-btn @click.prevent="uplift" :disabled="!canSubmit">JSON Uplift</v-btn>
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
            :rows="10"
        ></v-textarea>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import {Codemirror} from 'vue-codemirror';
import {StreamLanguage} from '@codemirror/language';
import {yaml} from '@codemirror/legacy-modes/mode/yaml';
import {json as cmJson} from '@codemirror/lang-json';
import axios from 'axios';

const BACKEND_URL = process.env.VUE_APP_BACKEND_URL;

export default {
  name: 'JsonUplift',
  components: {
    Codemirror,
  },
  data: () => ({
    inputSources: [
      {value: 'content', title: 'Text content'},
      {value: 'file', title: 'File'},
      {value: 'url', title: 'URL'},
    ],
    yamlContext: {
      type: 'content',
      content: '',
      file: [],
      url: null,
      placeholder: "transform:\n  - 'jq expression'\n\ncontext:\n  '$': {...}",
    },
    yamlExtensions: [
      StreamLanguage.define(yaml),
    ],
    jsonContent: {
      content: '',
      file: [],
      url: null,
      placeholder: '{\n  "property": "value"\n}',
    },
    jsonExtensions: [
      cmJson(),
    ],
    outputFormats: [
      {value: 'ttl', title: 'Turtle'},
      {value: 'json', title: 'Uplifted JSON-LD'},
      {value: 'expanded', title: 'Expanded JSON-LD'},
    ],
    outputFormat: 'ttl',
    baseUri: '',
    outputText: '',
    outputError: null,
  }),
  mounted() {
    this.yamlContext.type = localStorage.getItem("ogcPlayground.lastContextType") || 'content';
    this.yamlContext.content = localStorage.getItem("ogcPlayground.lastContext") || '';
    this.yamlContext.url = localStorage.getItem("ogcPlayground.lastContextUrl") || '';
    this.jsonContent.type = localStorage.getItem("ogcPlayground.lastJsonType") || 'content';
    this.jsonContent.content = localStorage.getItem("ogcPlayground.lastJson") || '';
    this.jsonContent.url = localStorage.getItem("ogcPlayground.lastJsonUrl") || '';
    this.baseUri = localStorage.getItem("ogcPlayground.lastBaseUri") || '';
    this.outputFormat = localStorage.getItem("ogcPlayground.lastOutputFormat") || 'ttl';
  },
  computed: {
    canSubmit() {
      switch (this.jsonContent.type) {
        case 'content':
          return this.jsonContent.content && !!this.jsonContent.content.trim();
        case 'url':
          return !!this.jsonContent.url;
        case 'file':
          return !!this.jsonContent.file.length;
      }
      return true;
    },
  },
  methods: {
    uplift() {
      const formData = new FormData();
      switch (this.yamlContext.type) {
        case 'content':
          localStorage.setItem("ogcPlayground.lastContext", this.yamlContext.content);
          formData.append('context', this.yamlContext.content);
          break;
        case 'url':
          localStorage.setItem("ogcPlayground.lastContextUrl", this.yamlContext.url);
          formData.append('contexturl', this.yamlContext.url);
          break;
        case 'file':
          formData.append('context', this.yamlContext.file[0]);
          break;
      }

      switch (this.jsonContent.type) {
        case 'content':
          localStorage.setItem("ogcPlayground.lastJson", this.jsonContent.content);
          formData.append('json', this.jsonContent.content);
          break;
        case 'url':
          localStorage.setItem("ogcPlayground.lastJsonUrl", this.jsonContent.url);
          formData.append('jsonurl', this.jsonContent.url);
          break;
        case 'file':
          formData.append('json', this.jsonContent.file[0]);
          break;
      }

      localStorage.setItem("ogcPlayground.lastContextType", this.yamlContext.type);
      localStorage.setItem("ogcPlayground.lastJsonType", this.jsonContent.type);
      localStorage.setItem("ogcPlayground.lastBaseUri", this.baseUri);
      localStorage.setItem("ogcPlayground.lastOutputFormat", this.outputFormat);

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
            const detail = err.response?.data?.detail;
            if (detail.msg) {
              this.outputError = detail.msg;
              if (detail.cause) {
                const msg = detail.cause.split('|', 2)[1];
                this.outputError += ': ' + msg;
              }
            } else {
              this.outputError = err;
            }
          });
    },
  },
}
</script>
