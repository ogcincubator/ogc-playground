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
          :start-marker="step.type !== 'InputStep'"
          :end-marker="step.type !== 'OutputStep'"
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
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn
              color="indigo"
              v-bind="props"
              class="ml-1"
            >
              Pipeline actions
              <v-icon>mdi-menu-down</v-icon>
            </v-btn>
          </template>
          <v-list density="compact">
            <v-list-item @click="exportPipeline" prepend-icon="mdi-file-export" :disabled="steps.length < 2">
              <v-list-item-title>
                Export pipeline...
              </v-list-item-title>
            </v-list-item>
            <v-divider/>
            <v-list-item style="color: red" @click="clearWorkflow" prepend-icon="mdi-delete-sweep">
              <v-list-item-title>
                Delete all pipeline steps
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
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
          <v-col v-if="activeStep.type !== 'OutputStep'">
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
    <text-copy-dialog v-model="exportPipelineUrl" title="Copy pipeline URL"></text-copy-dialog>
  </v-container>
</template>
<script>
import ProcessPill from "@/components/ProcessPill";
import YamlJsonEditor from "@/components/YamlJsonEditor";
import ResultViewer from "@/components/ResultViewer";
import TextCopyDialog from "@/components/TextCopyDialog";
import {debounce} from 'lodash';
import ContentStep from "@/components/steps/ContentStep.vue";
import backendService from "@/services/backend.service";
import upliftSteps from '@/model/upliftSteps';
import {reactive} from "vue";
import {mapActions, mapState} from 'pinia';
import {useGlobalStore} from "@/stores/global";

const LS_KEY_STATUS = 'ogc-playground.v2.status';

const STEP_COMPONENTS = {
  'InputStep': ContentStep,
  'UpliftStep': ContentStep,
};

export default {
  components: {
    ResultViewer,
    YamlJsonEditor,
    ProcessPill,
    TextCopyDialog,
  },
  data() {
    return {
      steps: [
        reactive(new upliftSteps.InputStep()),
        reactive(new upliftSteps.OutputStep()),
      ],
      stepIcons: {
        'InputStep': 'mdi-import',
        'UpliftStep': 'mdi-database-arrow-up-outline',
        'OutputStep': 'mdi-export',
      },
      stepBgColors: {
        'InputStep': '#00b1ff',
        'UpliftStep': '#6200ee',
        'OutputStep': '#00695C',
      },
      activeStepIdx: 0,
      oldStepContents: '',
      outputFormats: backendService.getJsonUpliftOutputFormats(),
      selectedOutputFormat: null,
      activeStepOutputDialog: false,
      exportPipelineUrl: null,
    };
  },
  created() {
    console.log('created');
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
    let savedStatusJson, savedStatusOrigin;
    if (this.hashParams.t === 'u' && this.hashParams.p) {
      savedStatusJson = this.hashParams.p;
      savedStatusOrigin = 'params';
    } else {
      savedStatusJson = localStorage.getItem(LS_KEY_STATUS);
      savedStatusOrigin = 'localStorage';
    }
    if (savedStatusJson) {
      try {
        const savedStatus = JSON.parse(savedStatusJson);
        const savedSteps = savedStatusOrigin === 'params' ? savedStatus : savedStatus.steps;
        if (Array.isArray(savedSteps)) {
          this.steps.splice(0, Infinity,
              ...savedSteps.map(upliftSteps.revive));
          if (this.steps.slice(-1)[0].type !== 'OutputStep') {
            this.steps.push(new upliftSteps.OutputStep());
          }
        }
        this.validatePipeline();
        if (savedStatus.selectedOutputFormat
            && this.outputFormats.some(v => v.value === savedStatus.selectedOutputFormat)) {
          this.selectedOutputFormat = savedStatus.selectedOutputFormat;
        }
        this.saveStatus();
      } catch (e) {
        console.log(`Error loading saved status from ${savedStatusOrigin}`, e);
        if (savedStatusOrigin === 'params') {
          this.showSnackbar('There was an error loading pipeline from URL', 'error');
          location.hash = '';
        } else if (savedStatusOrigin === 'localStorage') {
          // Clear key
          this.showSnackbar('There was an error loading the previously used pipeline', 'error');
          localStorage.removeItem(LS_KEY_STATUS);
        }
      }
    }
  },
  methods: {
    ...mapActions(useGlobalStore, ['showSnackbar']),
    addUpliftStep() {
      this.steps.splice(this.steps.length - 1, 0,
        new upliftSteps.UpliftStep(`Uplift step ${this.steps.length - 1}`));
      this.activeStepIdx = this.steps.length - 2;
      this.saveStatus();
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
      this.saveStatus();
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
    async runStep(idx, force = false) {
      const step = this.steps[idx], prevOutput = idx === 0 ? null : this.steps[idx - 1].output;
      const result = await step.run(prevOutput, force);
      this.saveStatus();
      return result;
    },
    saveStatus() {
      this.debouncedSaveStatus.call(this);
    },
    updateActiveStep(values) {
      Object.entries(values).forEach(([k, v]) => this.activeStep[k] = v);
    },
    clearWorkflow() {
      this.steps.splice(0, Infinity);
      this.steps.push(new upliftSteps.InputStep());
      this.steps.push(new upliftSteps.OutputStep());
      this.saveStatus();
    },
    exportPipeline() {
      // eslint-disable-next-line no-unused-vars
      const steps = this.steps.slice(0, -1);
      const content = encodeURIComponent(JSON.stringify(steps));
      this.exportPipelineUrl = `${location.origin}${location.pathname}#?t=u&p=${content}`;
    },
    validatePipeline() {
      // Check that we have input step > !input && !output step* > output step
      if (!this.steps || this.steps.length < 2) {
        throw new Error('Pipeline has less than 2 steps');
      }
      if (this.steps[0].type !== 'InputStep') {
        throw new Error('First step is not input');
      }
      if (this.steps.slice(-1)[0].type !== 'OutputStep') {
        throw new Error('Last step is not output');
      }
      if (this.steps.slice(1, -1).some(s => ['InputStep', 'OutputStep'].includes(s.type))) {
        throw new Error('Intermediate step is output or input');
      }
    },
  },
  computed: {
    ...mapState(useGlobalStore, ['hashParams']),
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
          this.oldStepContents = newv && newv.contents;
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
