import {defineStore} from 'pinia';
import {reactive} from "vue";

export const useGlobalStore = defineStore('global', () => {

  const hashParams = Object.fromEntries(
      new URLSearchParams(
          location.hash.replace(/^#[^?]*/, ''))
          .entries());

  const snackbar = reactive({
    color: 'primary',
    open: false,
    text: null,
  });

  function showSnackbar(text, color='primary') {
    Object.assign(snackbar, { text, color, open: true });
  }

  return { hashParams, snackbar, showSnackbar };
});
