import {defineStore} from 'pinia';
import {createDataReadyPromise} from "@/util";
import {ref} from "vue";

export const useUpliftStore = defineStore('uplift', () => {

  const dataReady = ref(true);
  const dataReadyPromise = createDataReadyPromise(dataReady);

  return { dataReady, dataReadyPromise };
});
