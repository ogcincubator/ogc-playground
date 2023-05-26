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
    <v-snackbar v-model="snackbar.open" timeout="5000" :color="snackbar.color">

      {{ snackbar.text }}

      <template v-slot:actions>
        <v-btn @click="snackbar.open = false">Ok</v-btn>
      </template>
    </v-snackbar>
  </v-dialog>
</template>

<script>
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
      snackbar: {
        color: 'primary',
        open: false,
        text: null,
      },
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
    showSnackbar(text, color='primary') {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.open = true;
    }
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