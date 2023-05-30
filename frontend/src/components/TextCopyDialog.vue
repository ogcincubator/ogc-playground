<template>
  <v-dialog v-model="show" width="800">
    <v-card>
      <v-card-title v-if="title">
        {{ title }}
      </v-card-title>
      <v-card-text>
        <v-text-field
          readonly
          :model-value="text"
        >
          <template v-slot:append-inner>
            <v-icon @click="copyToClipboard">mdi-clipboard</v-icon>
          </template>
        </v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="show = false">
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import {useGlobalStore} from "@/stores/global";
import {mapActions} from "pinia";

export default {
  props: {
    modelValue:  String,
    title: String,
  },
  emits: [
    'update:modelValue',
  ],
  data() {
    return {
      text: '',
    }
  },
  mounted() {
    this.text = this.modelValue || '';
  },
  computed: {
    show: {
      get() {
        return !!this.modelValue;
      },
      set(v) {
        if (!v) {
          this.$emit('update:modelValue', null);
        }
      }
    }
  },
  methods: {
    ...mapActions(useGlobalStore, ['showSnackbar']),
    copyToClipboard() {
      if (this.modelValue) {
        navigator?.clipboard?.writeText(this.modelValue)
          .then(() => {
            this.showSnackbar('Copied to clipboard');
          })
          .catch(e => {
            console.log(e);
            this.showSnackbar('Error copying to clipboard', 'error');
          });
      }
    },
  },
  watch: {
    modelValue(v) {
      if (v) {
        this.text = v;
      }
    },
  },
}
</script>