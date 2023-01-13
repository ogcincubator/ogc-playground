<template>
  <v-container>
    <v-row align="center">
      <v-col cols="12" md="2">
        <a href="https://www.ogc.org" target="_blank">
          <v-img
              id="ogc-logo"
              :src="logoUrl"
              alt="Open Geospatial Consortium Logo"
              title="Open Geospatial Consortium"
              max-height="90"

          />
        </a>
      </v-col>
      <v-col cols="12" md="8">
        <h1 class="text-center" id="main-header">
          JSON-LD Uplift
        </h1>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" class="text-right">
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn color="primary" v-bind="props" append-icon="mdi-menu-down" class="mr-2">
              Examples
            </v-btn>
          </template>
          <v-list>
            <v-list-item
                v-for="(example, index) in filteredExamples"
                :key="index"
                @click="loadExample(example)"
            >
              <v-list-item-title>{{ example.title }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn color="primary" v-bind="props" append-icon="mdi-menu-down">
              Help links
            </v-btn>
          </template>
          <v-list>
            <v-list-item
                v-for="(helpItem, index) in helpItems"
                :key="index"
                :href="helpItem.link"
                target="_blank"
            >
              <v-list-item-title>
                {{ helpItem.title }}
                <v-icon>mdi-open-in-new</v-icon>
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" md="6">
        <div>Context definition (YAML)</div>
        <v-select
            v-model="yamlContext.type"
            label="Source"
            :items="filteredInputSources"
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
            :hint="remoteFetchHint"
            persistent-hint
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
            :items="filteredInputSources"
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
            :hint="remoteFetchHint"
            persistent-hint
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
        <v-btn @click.prevent="uplift" :disabled="!canSubmit" :loading="processing">JSON Uplift</v-btn>
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
            :disabled="processing"
            :class="{ 'fade-loading': processing }"
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
import examples from '@/assets/json-uplift-examples.json';

import logoUrl from '@/assets/logo.png';

const BACKEND_URL = window.ogcPlayground.BACKEND_URL;

export default {
  name: 'JsonUplift',
  components: {
    Codemirror,
  },
  data: () => ({
    processing: false,
    logoUrl,
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
    remoteFetchRegex: null,
    examples,
    helpItems: [
      {
        title: 'ingest_json.py documentation',
        link: 'https://opengeospatial.github.io/ogc-na-tools/reference/ogc/na/ingest_json/'
      },
      {
        title: 'Sample context definition',
        link: 'https://opengeospatial.github.io/ogc-na-tools/examples/#sample-json-ld-uplifting-context'
      },
      {
        title: 'JSON-LD 1.1 specification',
        link: 'https://www.w3.org/TR/json-ld11/'
      },
      {
        title: 'JSON-LD Playground',
        link: 'https://json-ld.org/playground/'
      },
    ]
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
    axios.get(`${BACKEND_URL}/remote-fetch`)
        .then(resp => {
          this.remoteFetchRegex = resp.data.enabled ? resp.data.regex : false;
        })
        .catch(err => {
          console.log('Error obtaining remote fetch configuration', err);
        });
  },
  computed: {
    canSubmit() {
      let result = true;
      const remoteRegex = this.remoteFetchRegex ? new RegExp(this.remoteFetchRegex) : null;
      switch (this.jsonContent.type) {
        case 'content':
          result &= this.jsonContent.content && !!this.jsonContent.content.trim();
          break;
        case 'url':
          result &= !!this.jsonContent.url && !remoteRegex || !!this.jsonContent.url.match(remoteRegex);
          break;
        case 'file':
          return !!this.jsonContent.file.length;
      }
      if (this.yamlContext.type == 'url' && remoteRegex) {
        result &= !this.yamlContext.url || !!this.yamlContext.url.match(remoteRegex);
      }
      return result;
    },
    filteredInputSources() {
      return this.remoteFetchRegex === false
          ? this.inputSources.filter(i => i.value != 'url')
          : this.inputSources;
    },
    remoteFetchHint() {
      return this.remoteFetchRegex ? `Allowed URLs: ${this.remoteFetchRegex}` : null;
    },
    filteredExamples() {
      return this.remoteFetchRegex === false
          ? this.examples.filter(e => !e.contextUrl && !e.contentUrl)
          : this.examples;
    },
  },
  methods: {
    loadExample(example) {
      if (example.contextUrl) {
        this.yamlContext.url = example.contextUrl;
        this.yamlContext.type = 'url';
      } else {
        this.yamlContext.content = example.context;
        this.yamlContext.type = 'content';
      }
      if (example.contentUrl) {
        this.jsonContent.url = example.contentUrl;
        this.jsonContent.type = 'url';
      } else {
        this.jsonContent.content = example.content;
        this.jsonContent.type = 'content';
      }
      this.baseUri = example.baseUri || '';
    },
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
      this.processing = true;
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
          })
          .finally(() => this.processing = false);
    },
  },
}
</script>
<style>
.fade-loading {
  opacity: 0.5;
}
</style>
