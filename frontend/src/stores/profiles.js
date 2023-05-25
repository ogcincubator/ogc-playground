import {defineStore} from 'pinia';
import {onMounted, ref} from "vue";
import profileService from "@/services/profile.service";

export const useProfilesStore = defineStore('profiles', () => {

  const profiles = ref({});

  onMounted(() => {
    profileService.getProfiles()
      .then(p => profiles.value = p);
  });

  return { profiles };
})