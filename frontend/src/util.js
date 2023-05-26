import {watch} from "vue";

export const createDataReadyPromise = dataReadyRef => {
  return new Promise(resolve => {
    if (dataReadyRef.value) {
      resolve(true);
    } else {
      watch(dataReadyRef, v => {
        if (v) {
          resolve(true);
        }
      });
    }
  });
};

