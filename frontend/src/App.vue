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
      <component :is="activeComponent" :tab-title="activeComponentTitle"></component>
    </v-main>
  </v-app>
</template>

<script>
import {useProfilesStore} from "@/stores/profiles";
import {useUpliftStore} from "@/stores/uplift";
import JsonUplift from './components/JsonUplift.vue';
import PlaceholderComponent from './components/PlaceholderComponent.vue';
import logoUrl from '@/assets/logo.png';

export default {
  name: 'App',

  components: {
    JsonUplift,
    PlaceholderComponent,
  },

  data: () => ({
    tabs: [
      { label: 'Semantic uplift', component: 'JsonUplift' },
      { label: 'BB Schema annotation', component: 'PlaceholderComponent' },
      { label: 'Building block validation', component: 'PlaceholderComponent' },
    ],
    activeTab: 0,
    logoUrl,
    dataStatus: 'loading',
  }),

  beforeCreate() {
    this.allStores = [useProfilesStore(), useUpliftStore()];
  },

  mounted() {
    Promise.all(this.allStores.filter(s => s.dataReadyPromise).map(s => s.dataReadyPromise))
      .then(r => {
        if (r.every(v => v)) {
          this.dataStatus = 'ready';
        } else {
          this.dataStatus = 'error';
        }
      });
  },

  computed: {
    activeComponent() {
      return this.tabs[this.activeTab].component;
    },
    activeComponentTitle() {
      return this.tabs[this.activeTab].label;
    },
  },
}
</script>
