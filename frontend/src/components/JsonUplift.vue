<template>
  <v-container>
    <v-row>
      <v-col class="d-flex justify-start flex-wrap">
        <process-pill
            v-for="(step, idx) in steps"
            :key="idx"
            :bg-color="stepBgColors[step.type]"
            :active="activeStepIdx === idx"
            @click.prevent="activeStepIdx = idx"
            :start-marker="step.type !== 'input'"
            :end-marker="step.type !== 'output'"
            :opacity="step.pending ? 0.4 : 1.0"
            class="step"
            :class="{ active: activeStepIdx === idx }"
        >
          <v-progress-circular v-if="step.loading" indeterminate size="20" class="mr-1"/>
          <v-icon>{{ stepIcons[step.type] }}</v-icon>
          {{ step.errors && step.errors.length ? '!' : '' }}
          {{ step.modified ? '*' : '' }}
          {{ step.title }}
        </process-pill>
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn
              icon="mdi-plus"
              size="x-small"
              color="success"
              v-bind="props"
              class="ml-1"
            ></v-btn>
          </template>
          <v-list density="compact">
            <v-list-item :link="true">
              <v-list-item-title @click.prevent="addUpliftStep">JSON-LD uplift</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          icon="mdi-play"
          size="x-small"
          color="primary"
          class="ml-5"
          title="Run full workflow"
          :disabled="running"
          :loading="running"
          @click.prevent="runFullWorkflow"
        ></v-btn>
        <v-spacer></v-spacer>
        <v-btn
          icon="mdi-delete-sweep"
          size="x-small"
          color="error"
          title="Delete all steps"
          :disabled="running"
          @click.prevent="clearWorkflow"
        ></v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-row>
          <v-col>
            <h2>
              {{ activeStep.title }}
              <small>(Step {{ activeStepIdx + 1 }})</small>
              <span v-if="activeStepIdx !== 0 && activeStepIdx !== steps.length - 1">
                <v-btn
                    v-if="canRunStep"
                    class="ml-5"
                    size="x-small"
                    color="primary"
                    title="Run step"
                    :disabled="running"
                    @click.prevent="runStep(activeStepIdx, true)"
                    icon="mdi-play"
                ></v-btn>
                <v-btn
                    v-if="!activeStep.pending"
                    class="ml-1"
                    size="x-small"
                    title="View output"
                    @click.prevent="activeStepOutputDialog = true"
                    icon="mdi-magnify"
                ></v-btn>
                <v-btn
                    class="ml-5"
                    size="x-small"
                    color="error"
                    title="Delete step"
                    @click.prevent="deleteStep"
                    icon="mdi-delete"
                ></v-btn>
              </span>
            </h2>
          </v-col>
        </v-row>
        <v-row v-if="activeStep.errors && activeStep.errors.length">
          <v-col class="text-error">
            <p>
              The following errors were encountered while running this step:
            </p>
            <ul>
              <li v-for="(err, idx) in activeStep.errors" :key="idx">
                {{ err }}
              </li>
            </ul>
          </v-col>
        </v-row>
        <v-row>
          <v-col v-if="activeStep.type !== 'output'">
            <component
              :is="activeStepComponent"
              :step="activeStep"
              @update="updateActiveStep"
            >
            </component>
            <v-dialog
              v-model="activeStepOutputDialog"
              width="90%"
            >
              <v-card>
                <v-card-text>
                  <result-viewer
                    :formats="outputFormats"
                    :output="activeStep.output"
                    v-model:format="selectedOutputFormat"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn @click.prevent="activeStepOutputDialog = false">Close</v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </v-col>
          <v-col v-else>
            <result-viewer
                :formats="outputFormats"
                :output="activeStep.output"
                v-model:format="selectedOutputFormat"
              />
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import ProcessPill from "@/components/ProcessPill";
import YamlJsonEditor from "@/components/YamlJsonEditor";
import axios from "axios";
import jszip from "jszip";
import ResultViewer from "@/components/ResultViewer";
import jsYaml from "js-yaml";
import { debounce } from 'lodash';
import ContentStep from "@/components/steps/ContentStep.vue";

const BACKEND_URL = window.ogcPlayground.BACKEND_URL;
const LS_KEY_STATUS = 'ogc-playground.v2.status';

const STEP_COMPONENTS = {
  'input': ContentStep,
  'uplift': ContentStep,
};

export default {
  components: {
    ResultViewer,
    YamlJsonEditor,
    ProcessPill,
  },
  data() {
    const defaultSteps = [{
      type: 'input',
      title: 'Input',
      contents: '',
      mode: 'json',
      modified: false,
    },
      {
        type: 'output',
        title: 'Output',
        contents: '',
        pending: true,
        output: null,
      },
    ];
    return {
      defaultSteps,
      steps: JSON.parse(JSON.stringify(defaultSteps)),
      stepIcons: {
        input: 'mdi-import',
        uplift: 'mdi-database-arrow-up-outline',
        output: 'mdi-export',
      },
      stepBgColors: {
        input: '#00b1ff',
        uplift: '#6200ee',
        output: '#00695C',
      },
      activeStepIdx: 0,
      oldStepContents: '',
      outputFormats: [
        {value: 'ttl', title: 'Turtle', fn: 'ttl.ttl'},
        {value: 'json', title: 'Uplifted JSON-LD', fn: 'uplifted.jsonld'},
        {value: 'expanded', title: 'Expanded JSON-LD', fn: 'expanded.jsonld'},
      ],
      selectedOutputFormat: null,
      activeStepOutputDialog: false,
    };
  },
  created() {
    this.debouncedSaveStatus = debounce(() => {
        const status = {
          steps: this.steps,
          selectedOutputFormat: this.selectedOutputFormat,
        };
        localStorage.setItem(LS_KEY_STATUS, JSON.stringify(status));
      }, 2000);
  },
  beforeUnmount() {
    this.debouncedSaveStatus.cancel();
  },
  mounted() {
    const savedStatusJson = localStorage.getItem(LS_KEY_STATUS);
    if (savedStatusJson) {
      try {
        const savedStatus = JSON.parse(savedStatusJson);
        if (Array.isArray(savedStatus.steps)) {
          this.steps.length = 0;
          this.steps.push(...savedStatus.steps);
        }
        if (savedStatus.selectedOutputFormat
            && this.outputFormats.some(v => v.value === savedStatus.selectedOutputFormat)) {
          this.selectedOutputFormat = savedStatus.selectedOutputFormat;
        }
      } catch {
        // Clear key
        localStorage.removeItem(LS_KEY_STATUS);
      }
    }
  },
  methods: {
    addUpliftStep() {
      this.steps.splice(this.steps.length - 1, 0,{
        type: 'uplift',
        title: `Uplift step ${this.steps.length - 1}`,
        pending: true,
        mode: 'yaml',
        contents: '',
        modified: false,
        output: null,
        running: false,
        errors: [],
      });
      this.activeStepIdx = this.steps.length - 2;
    },
    getStepStyle(step) {
      const style = {};
      if (step.pending) {
        style.opacity = 0.4;
      }
      return style;
    },
    deleteStep() {
      this.steps.splice(this.activeStepIdx, 1);
      this.activeStepIdx--;
    },
    async runFullWorkflow() {
      for (let i = 0; i < this.steps.length; i++) {
        this.activeStepIdx = i;
        const result = await this.runStep(i);
        if (!result) {
          return false;
        }
      }
    },
    async runStep(idx, force) {
      if (idx === this.steps.length - 1) {
        return true;
      }
      const step = this.steps[idx], prevStep = idx === 0 ? null : this.steps[idx - 1];
      if (!step.pending && !step.modified && !force) {
        return true;
      }
      step.loading = true;

      if (idx === 0) {
        // input step - validate JSON / YAML
        try {
          const inputData = jsYaml.load(step.contents);
          if (typeof inputData !== 'object') {
            step.errors = [
              'Input data must be an object or array'
            ];
            step.loading = false;
            return false;
          }
        } catch {
          step.errors = [
            'Input data is not a valid JSON or YAML document'
          ];
          step.loading = false;
          return false;
        }
        if (this.steps.length > 2) {
          // do not go any further
          step.modified = false;
          step.loading = false;
          return true;
        }
      }
      if (step.type === 'uplift' || step.type === 'input') {
        // Uplift step OR input step and no other workflow steps
        let inputData;
        switch (idx) {
          case 0: inputData = step.contents; break;
          case 1: inputData = prevStep.contents; break;
          default: inputData = prevStep.output['json'];
        }
        const upliftConfig = idx === 0 ? '' : step.contents;

        const formData = new FormData();
        formData.append('output', 'all');
        formData.append('context', upliftConfig);
        formData.append('json', inputData);
        try {
          const result = await axios.post(`${BACKEND_URL}/json-uplift`, formData, {
              responseType: 'blob'
            })
            .then(res => jszip.loadAsync(res.data))
            .then(zipfile => Promise.all(this.outputFormats.map(async fmt => [fmt.value, await zipfile.file(fmt.fn).async('string')])))
            .then(r => this.result = Object.fromEntries(r))
            .finally(() => {
              step.loading = false;
            });
          step.pending = false;
          step.modified = false;
          step.output = result;

          if (idx === this.steps.length -2) {
            this.steps[idx + 1].pending = false;
            this.steps[idx + 1].output = result;
          }

          return true;
        } catch (err) {
          console.log(err);

          const errText = await err.response.data.text();
          let errMsg = null;
          try {
            const errObj = JSON.parse(errText);
            if (errObj?.detail?.msg) {
              errMsg = errObj.detail.msg;
              if (errObj?.detail?.cause) {
                errMsg += ': ' + errObj.detail.cause.split('|', 2)[1];
              }
            } else if (err.message) {
              errMsg = err.message;
            }
          } catch {
            // ignore
          }

          if (!errMsg) {
            errMsg = 'Unknown error';
          }

          step.errors = [errMsg];

          return false;
        }
      } else {
        return true;
      }
    },
    saveStatus() {
      this.debouncedSaveStatus.call(this);
    },
    updateActiveStep(values) {
      Object.entries(values).forEach(([k, v]) => this.activeStep[k] = v);
    },
    clearWorkflow() {
      this.steps.splice(0, Infinity, ...JSON.parse(JSON.stringify(this.defaultSteps)));
      this.saveStatus();
    },
  },
  computed: {
    activeStep() {
        return this.steps[this.activeStepIdx];
    },
    running() {
      return this.steps.some(s => s.loading);
    },
    canRunStep() {
      return this.activeStepIdx > 0 && this.activeStepIdx < this.steps.length - 1
          && this.steps.slice(1, this.activeStepIdx).every(s => !s.pending);
    },
    inputStep() {
      return this.steps[0];
    },
    outputStep() {
      return this.steps[this.steps.length - 1];
    },
    activeStepComponent() {
      return STEP_COMPONENTS[this.activeStep.type];
    },
  },
  watch: {
    activeStep: {
      handler(newv, oldv) {
        if (newv !== oldv) {
          this.oldStepContents = newv.contents;
          return;
        }
        if (newv.contents === this.oldStepContents) {
          return;
        }
        this.oldStepContents = newv.contents;
        this.activeStep.errors = [];
        this.activeStep.modified = true;
        this.saveStatus();
        if (this.activeStepIdx > 0) {
          this.activeStep.pending = true;
        }
        this.steps.forEach((s, i) => {
          if (i > this.activeStepIdx) {
            s.errors = [];
            s.pending = true;
            s.output = null;
          }
        });
      },
      deep: true,
    },
  },
}
</script>
<style>
ul {
  padding-left: 1em;
}
.step.active {
  position: relative;
}
.step.active::after {
  content: '';
  position: absolute;
  bottom: -5px;
  width: 70%;
  left: 15%;
  background: #666;
  height: 3px;
}
</style>