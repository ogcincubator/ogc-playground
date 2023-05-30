<template>
  <v-app>
    <v-main>
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
              OGC Playground
            </h1>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-tabs v-model="activeTab" v-if="dataStatus === 'ready'">
              <v-tab v-for="(tab, index) in tabs" :key="index" :value="index">{{ tab.label }}</v-tab>
            </v-tabs>
            <v-overlay
              :model-value="dataStatus !== 'ready'"
              class="align-center justify-center text-center"
            >
              <v-progress-circular
                color="primary"
                indeterminate
                size="64"
              ></v-progress-circular>
              <div class="text-h5 mt-3">Loading data&hellip;</div>
            </v-overlay>
          </v-col>
        </v-row>
      </v-container>
      <keep-alive v-if="dataStatus === 'ready'">
        <component :is="activeComponent" :tab-title="activeComponentTitle"></component>
      </keep-alive>
    </v-main>
    <v-snackbar v-model="snackbar.open" timeout="5000" :color="snackbar.color">

      {{ snackbar.text }}

      <template v-slot:actions>
        <v-btn @click="snackbar.open = false">Ok</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import {useProfilesStore} from "@/stores/profiles";
import {useUpliftStore} from "@/stores/uplift";
import {useGlobalStore} from "@/stores/global";
import JsonUplift from './components/JsonUplift.vue';
import PlaceholderComponent from './components/PlaceholderComponent.vue';
import logoUrl from '@/assets/logo.png';
import {mapState} from "pinia";

const tabParamValues = {
  u: 0,
  b: 1,
  v: 2,
};

export default {
  name: 'App',

  components: {
    JsonUplift,
    PlaceholderComponent,
  },

  data: () => ({
    tabs: [
      {label: 'Semantic uplift', component: 'JsonUplift'},
      {label: 'BB Schema annotation', component: 'PlaceholderComponent'},
      {label: 'Building block validation', component: 'PlaceholderComponent'},
    ],
    activeTab: 0,
    logoUrl,
    dataStatus: 'loading',
  }),

  beforeCreate() {
    this.allStores = [useProfilesStore(), useUpliftStore(), useGlobalStore()];
  },

  mounted() {
    this.activeTab = tabParamValues[this.hashParams.t] || 0;
    Promise.all(this.allStores.filter(s => s.dataReadyPromise).map(s => s.dataReadyPromise))
      .then(r => {
        if (r.every(v => v)) {
          this.dataStatus = 'ready';
        } else {
          this.dataStatus = 'error';
        }
        console.log('Data status:', this.dataStatus);
      });
  },

  computed: {
    ...mapState(useGlobalStore, ['hashParams', 'snackbar']),
    activeComponent() {
      return this.tabs[this.activeTab].component;
    },
    activeComponentTitle() {
      return this.tabs[this.activeTab].label;
    },
  },
}
</script>
