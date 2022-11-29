<template>
  <v-app>
    <v-main>
      <JsonUplift/>
    </v-main>
  </v-app>
</template>

<script>
import JsonUplift from './components/JsonUplift.vue'

export default {
  name: 'App',

  components: {
    JsonUplift,
  },

  data: () => ({
    //
  }),
}
</script>
