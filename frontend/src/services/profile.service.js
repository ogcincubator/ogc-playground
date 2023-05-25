import httpService from '@/services/http.service';

class ProfileService {

  getProfiles() {
    return httpService.get('profiles')
      .then(resp => resp.data);
  }

}

export default new ProfileService();