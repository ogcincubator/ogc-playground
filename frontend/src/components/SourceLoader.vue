<template>
  <div>
    <v-row>
      <v-col cols="12" lg="3">
        <v-select
          label="Input source"
          :items="inputSources"
          :model-value="inputSource"
          @update:model-value="$emit('update:inputSource', $event)"
        >
        </v-select>
      </v-col>
      <v-col v-if="inputSource === 'contents'">
        <v-btn
          color="primary"
          class="ml-1"
          @click="showFilePicker"
        >
          Load data from file...
        </v-btn>
      </v-col>
    </v-row>

    <input type="file" ref="fileField" @change="fileSelected" :accept="fileAccept"/>

    <v-dialog
      v-model="urlDialog"
      width="400px"
    >
      <v-card>
        <v-card-text>
          <v-text-field
            label="URL"
            v-model="url"
            prepend-inner-icon="mdi-web"
            placeholder="https://www..."
            :error-messages="urlErrors"
            :disabled="urlLoading"
            :loading="urlLoading"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click.prevent="urlDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click.prevent="loadFromUrl">Load</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
<script>
import axios from "axios";
import {useProfilesStore} from "@/stores/profiles";
import {mapState} from "pinia";

export default {
  props: {
    inputSource: {
      type: String,
      validator: v => ['contents', 'url'].includes(v),
    },
    showFile: {
      type: Boolean,
      default: true,
    },
    showUrl: {
      type: Boolean,
      default: true,
    },
    fileAccept: {
      type: String,
      default: '.yml,.yaml,.json,.jsonld,.json-ld,text/yaml,application/json,application/x-yaml,application/ld+json',
    },
    profileRoles: {
      type: [Array, Boolean],
    },
  },
  data() {
    return {
      urlDialog: false,
      url: '',
      urlErrors: [],
      urlLoading: false,
      inputSources: [
        {value: 'contents', title: 'Text contents'},
        {value: 'url', title: 'URL'},
      ]
    };
  },
  beforeCreate() {
    this.profilesStore = useProfilesStore();
  },
  methods: {
    clickedOption(func) {
      this[func]();
    },
    showFilePicker() {
      this.$refs.fileField.click();
    },
    showLoadUrlDialog() {
      this.urlDialog = true;
    },
    fileSelected(ev) {
      const files = ev.target.files;
      if (files && files.length) {
        const file = files[0];
        const reader = new FileReader();
        reader.onload = (res) => {
          this.$emit('contents', res.target.result);
        };
        reader.onerror = (err) => {
          alert('An error was encountered while reading the file');
          console.log(err);
        };
        reader.readAsText(file);
      }
    },
    loadFromUrl() {
      this.urlLoading = true;
      this.urlErrors = [];
      axios.get(this.url, {
        responseType: 'text'
      })
        .then(resp => {
          console.log(resp);
          this.$emit('contents', resp.data);
          this.urlDialog = false;
        })
        .catch(err => {
          let e;
          if (err.message) {
            e = err.message;
          } else if (err.code) {
            e = err.code;
          } else if (err.response) {
            e = err.response.statusText;
          } else {
            e = 'Unknown error';
          }
          this.urlErrors = [
            `Error loading remote data: ${e}`
          ];
          console.log(err);
        });
    },
  },
  computed: {
    ...mapState(useProfilesStore, ['profiles']),
    menuOptions() {
      const opts = [];
      if (this.showFile) {
        opts.push({icon: 'file', text: 'File on your computer', click: 'showFilePicker'});
      }
      if (this.showUrl) {
        opts.push({icon: 'web', text: 'URL', click: 'showLoadUrlDialog'})
      }
      return opts;
    },
    filteredProfiles() {
      if (!this.profileRoles) {
        return [];
      }
      if (this.profileRoles === true) {
        return this.profiles;
      }
      return Object.entries(this.profiles)
        .filter(([, v]) => Object.keys(v.artifacts).some(r => this.profileRoles.indexOf(r) >= 0))
        .map(([k, v]) => ({...v, uri: k}));
    },
  },
}
</script>
<style>
input[type=file] {
  display: none;
}
</style>
