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
            :style="getStepStyle(step, idx)"
            class="step"
            :class="{ active: activeStepIdx === idx }"
        >
          <v-icon>{{ stepIcons[step.type] }}</v-icon>
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
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-row>
          <v-col>
            <h2>
              {{ activeStep.title }}
              <small>(Step {{ activeStepIdx + 1 }})</small>
              <v-btn v-if="activeStepIdx !== 0 && activeStepIdx !== steps.length - 1"
                     class="ml-5"
                     size="x-small"
                     color="error"
                     title="Delete step"
                     @click.prevent="deleteStep">
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </h2>
          </v-col>
        </v-row>
        <v-row>
          <v-col class="text-right">
            <source-loader
                v-if="activeStep.type !== 'output'"
                @change="sourceLoaderChanged"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <YamlJsonEditor
                v-if="activeStep.type !== 'output'"
                v-model="activeStep.contents"
                v-model:mode="activeStep.mode"
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
import SourceLoader from "@/SourceLoader";

export default {
  components: {
    YamlJsonEditor,
    ProcessPill,
    SourceLoader,
  },
  data() {
    return {
      steps: [
        {
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
        }
      ],
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
      inputContent: '',
      output: null,
    };
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
    sourceLoaderChanged(v) {
      this.activeStep.contents = v;
      try {
        JSON.parse(v);
        this.activeStep.mode = 'json';
      } catch {
        this.activeStep.mode = 'yaml';
      }
    },
    deleteStep() {
      this.steps.splice(this.activeStepIdx, 1);
      this.activeStepIdx--;
    },
  },
  computed: {
    activeStep() {
      return this.steps[this.activeStepIdx];
    },
  },
  watch: {
    activeStep: {
      handler(newv, oldv) {
        if (newv !== oldv) {
          console.log('changed step');
          return;
        }
        if (this.activeStepIdx > 0) {
          this.activeStep.modified = true;
        }
        this.steps.forEach((s, i) => {
          if (i > this.activeStepIdx) {
            s.pending = true;
          }
        });
      },
      deep: true,
    },
  },
}
</script>
<style>
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