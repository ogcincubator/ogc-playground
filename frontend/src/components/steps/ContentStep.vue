<template>
  <div>
    <source-loader
      :input-source="step.inputSource"
      @update:inputSource="$emit('update', { inputSource: $event })"
      @contents="$emit('update', { contents: $event })"
      class="mb-4"
      :profile-roles="['http://www.w3.org/ns/dx/prof/role/validation']"
    />
    <yaml-json-editor
      v-if="step.inputSource === 'contents'"
      :model-value="step.contents"
      @update:modelValue="$emit('update', { contents: $event })"
      :mode="step.mode"
      @update:mode="$emit('update', { mode: $event })"
    />
    <v-text-field
      v-if="step.inputSource === 'url'"
      :model-value="step.url"
      prepend-inner-icon="mdi-web"
      placeholder="https://www..."
      @update:modelValue="$emit('update', { url: $event })"
      append-inner-icon="mdi-magnify"
      @click:append-inner="loadContentsFromUrl"
    >
    </v-text-field>

    <v-dialog
      v-model="previewUrl"
      width="800px"
    >
      <v-card>
        <v-card-text>
          <v-textarea
            rows="15"
            readonly
            :model-value="step.contents"
          >
          </v-textarea>
          <div class="loader" v-if="previewUrlLoading">
            <v-progress-circular
              indeterminate
              size="64"
              color="primary"
            >
            </v-progress-circular>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn
            @click.prevent="loadContentsFromUrl(true)"
            prepend-icon="mdi-reload"
            :disabled="previewUrlLoading"
          >
            Reload data
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn @click.prevent="previewUrl = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import SourceLoader from "@/components/SourceLoader.vue";
import YamlJsonEditor from "@/components/YamlJsonEditor.vue";

export default {
  components: {
    YamlJsonEditor,
    SourceLoader,
  },
  props: {
    step: {
      type: Object,
      required: true,
    },
  },
  emits: [
    'update'
  ],
  data() {
    return {
      previewUrl: false,
      previewUrlLoading: false,
    };
  },
  methods: {
    async loadContentsFromUrl(force = false) {
      if (this.previewUrlLoading) {
        return;
      }
      this.previewUrlLoading = true;
      this.previewUrl = await this.step.fetchContents(force);
      this.previewUrlLoading = false;
    },
  },
}
</script>

<style>
textarea {
  font-family: monospace !important;
}

.v-dialog .v-overlay__content > .v-card > .v-card-text {
  position: relative;
}

.v-card-text .loader {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  right: 0;
  background-color: rgba(33, 33, 33, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
