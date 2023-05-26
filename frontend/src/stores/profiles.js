import {defineStore} from 'pinia';
import {ref} from "vue";
import profileService from "@/services/profile.service";
import { createDataReadyPromise } from '@/util';

export const useProfilesStore = defineStore('profiles', () => {

  const profiles = ref({});
  const dataReady = ref(false);
  const dataReadyPromise = createDataReadyPromise(dataReady);

  profileService.getProfiles()
    .then(p => {
      profiles.value = p;
      dataReady.value = true;
    });

  return { profiles, dataReady, dataReadyPromise };
})