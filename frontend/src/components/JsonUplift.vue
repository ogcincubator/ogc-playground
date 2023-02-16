<template>
  <v-container>
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
      <v-col>
        <process-pill :start-marker="false">
          Hola
        </process-pill>
        <yaml-json-editor
            v-model="testContent"
        />
        {{ testContent }}
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" md="6">
        <div>Uplift definition (YAML)</div>
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
            label="Uplift definition URL"
            placeholder="https://..."
        ></v-text-field>
        <v-alert v-if="yamlContext.type == 'url'" type="info">
          Uplift definition URLs must match the following pattern(s):
          <ul>
            <li class="ml-6" v-for="(r, index) in remoteFetchRegex" :key="index"><code>{{r}}</code></li>
          </ul>
        </v-alert>
        <v-file-input
            v-if="yamlContext.type == 'file'"
            v-model="yamlContext.file"
            label="YAML context definition file"
        ></v-file-input>
        <div class="mt-2">
          <v-alert v-if="remoteContextFetchType == 'disabled'" type="warning">
            Remote context URL imports are disabled.
          </v-alert>
          <v-alert v-if="remoteContextFetchType == 'open'" type="info">
            Remote context URL imports are enabled.
          </v-alert>
          <v-alert v-if="remoteContextFetchType == 'whitelist'" type="info">
            Remote context URL imports are limited to the following pattern(s):
            <ul>
              <li class="ml-6" v-for="(r, index) in remoteContextFetchWhitelist" :key="index"><code>{{ r }}</code></li>
            </ul>
          </v-alert>
        </div>
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
        ></v-text-field>
        <v-alert v-if="jsonContent.type == 'url'" type="info">
          JSON document URLs must match the following pattern(s):
          <ul>
            <li class="ml-6" v-for="(r, index) in remoteFetchRegex" :key="index"><code>{{r}}</code></li>
          </ul>
        </v-alert>
        <v-file-input
            v-if="jsonContent.type == 'file'"
            v-model="jsonContent.file"
            label="JSON input file"
        ></v-file-input>
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-col class="text-center" xs="6" sm="4">
        <v-btn @click.prevent="uplift" :disabled="!canSubmit" :loading="processing" prepend-icon="mdi-play">JSON Uplift</v-btn>
      </v-col>
    </v-row>
    <v-row v-if="result" class="result">
      <v-col>
        <v-row no-gutters>
          <v-col cols="12" v-if="resultError">
            <div class="text-red-lighten-1">
              {{ resultError }}
            </div>
          </v-col>
        </v-row>
        <v-row no-gutters>
          <v-col sm="9" md="6" v-if="!resultError">
            <v-select
                v-model="resultFormat"
                label="Output format"
                :items="resultFormats"
                :disabled="processing"
            >
            </v-select>
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
          <v-col v-if="!resultError">
            <v-textarea
                ref="resultText"
                variant="filled"
                class="output"
                v-model="result[resultFormat]"
                :rows="15"
                :disabled="processing"
                :class="{ 'fade-loading': processing }"
            ></v-textarea>
          </v-col>
        </v-row>
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
import jszip from 'jszip';
import examples from '@/assets/json-uplift-examples.json';
import YamlJsonEditor from "@/components/YamlJsonEditor";
import ProcessPill from "@/components/ProcessPill";

const BACKEND_URL = window.ogcPlayground.BACKEND_URL;

export default {
  name: 'JsonUplift',
  components: {
    ProcessPill,
    YamlJsonEditor,
    Codemirror,
  },
  data: () => ({
    testContent: '',
    processing: false,
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
    resultFormats: [
      {value: 'ttl', title: 'Turtle', fn: 'ttl.ttl'},
      {value: 'json', title: 'Uplifted JSON-LD', fn: 'uplifted.jsonld'},
      {value: 'expanded', title: 'Expanded JSON-LD', fn: 'expanded.jsonld'},
    ],
    resultFormat: 'ttl',
    result: null,
    resultError: null,
    remoteFetchRegex: null,
    examples,
    copyToClipboardIcon: 'mdi-content-copy',
    copyToClipboardTimeout: null,
    copyToClipboardTooltip: 'Copy result to clipboard',
    helpItems: [
      {
        title: 'JSON-LD uplift tutorial',
        link: 'https://opengeospatial.github.io/ogc-na-tools/tutorials/#how-to-create-a-json-ld-uplift-context-definition',
      },
      {
        title: 'ingest_json.py documentation',
        link: 'https://opengeospatial.github.io/ogc-na-tools/reference/ogc/na/ingest_json/',
      },
      {
        title: 'Sample context definition',
        link: 'https://opengeospatial.github.io/ogc-na-tools/examples/#sample-json-ld-uplifting-context',
      },
      {
        title: 'JSON-LD 1.1 specification',
        link: 'https://www.w3.org/TR/json-ld11/',
      },
      {
        title: 'JSON-LD Playground',
        link: 'https://json-ld.org/playground/',
      },
    ],
    remoteContextFetchType: null,
    remoteContextFetchWhitelist: null,
  }),
  mounted() {
    this.yamlContext.type = localStorage.getItem("ogcPlayground.lastContextType") || 'content';
    this.yamlContext.content = localStorage.getItem("ogcPlayground.lastContext") || '';
    this.yamlContext.url = localStorage.getItem("ogcPlayground.lastContextUrl") || '';
    this.jsonContent.type = localStorage.getItem("ogcPlayground.lastJsonType") || 'content';
    this.jsonContent.content = localStorage.getItem("ogcPlayground.lastJson") || '';
    this.jsonContent.url = localStorage.getItem("ogcPlayground.lastJsonUrl") || '';
    this.resultFormat = localStorage.getItem("ogcPlayground.lastOutputFormat") || 'ttl';
    axios.get(`${BACKEND_URL}/remote-fetch`)
        .then(resp => {
          this.remoteFetchRegex = resp.data.enabled ? resp.data.regex : false;
          if (resp.data.context) {
            this.remoteContextFetchType = resp.data.context.type;
            this.remoteContextFetchWhitelist = resp.data.context.whitelist;
          }
        })
        .catch(err => {
          console.log('Error obtaining remote fetch configuration', err);
        });
  },
  computed: {
    canSubmit() {
      let result = true;
      const remoteRegex = this.remoteFetchRegex && this.remoteFetchRegex.length
          ? this.remoteFetchRegex.map(e => new RegExp(e))
          : null;
      const remoteRegexMatches = s => !!s && remoteRegex && remoteRegex.some(r => s.match(r));
      switch (this.jsonContent.type) {
        case 'content':
          result &= this.jsonContent.content && !!this.jsonContent.content.trim();
          break;
        case 'url':
          result &= remoteRegexMatches(this.jsonContent.url);
          break;
        case 'file':
          return !!this.jsonContent.file.length;
      }
      if (this.yamlContext.type == 'url') {
        result &= remoteRegexMatches(this.yamlContext.url);
      }
      return result;
    },
    filteredInputSources() {
      return this.remoteFetchRegex === false
          ? this.inputSources.filter(i => i.value != 'url')
          : this.inputSources;
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
      localStorage.setItem("ogcPlayground.lastOutputFormat", this.resultFormat);

      formData.append('output', 'all');
      this.processing = true;
      this.resultError = null;
      axios.post(`${BACKEND_URL}/json-uplift`, formData, {
            responseType: 'blob'
          })
          .then(res => jszip.loadAsync(res.data))
          .then(zipfile => Promise.all(this.resultFormats.map(async fmt => [fmt.value, await zipfile.file(fmt.fn).async('string')])))
          .then(r => this.result = Object.fromEntries(r))
          .catch(err => {
            console.log(err);
            this.result = null;
            const detail = err.response?.data?.detail;
            if (detail.msg) {
              this.resultError = detail.msg;
              if (detail.cause) {
                const msg = detail.cause.split('|', 2)[1];
                this.resultError += ': ' + msg;
              }
            } else {
              this.resultError = err;
            }
          })
          .finally(() => this.processing = false);
    },
    copyToClipboard() {
      clearTimeout(this.copyToClipboardTimeout);
      this.copyToClipboardIcon = 'mdi-check-bold';
      this.copyToClipboardTooltip = 'Copied!'
      this.copyToClipboardTimeout = setTimeout(() => {
        this.copyToClipboardIcon = 'mdi-content-copy';
        this.copyToClipboardTooltip = 'Copy result to clipboard';
      }, 2000);
      navigator.clipboard.writeText(this.result[this.resultFormat]);
    },
  },
}
</script>
<style>
.fade-loading {
  opacity: 0.5;
}
.result textarea {
  font-family: monospace;
}
</style>
