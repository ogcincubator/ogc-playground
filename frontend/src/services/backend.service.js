import httpService from '@/services/http.service';
import jszip from "jszip";

const BACKEND_URL = window.ogcPlayground.BACKEND_URL;

const upliftOutputFormats = [
  {value: 'ttl', title: 'Turtle', fn: 'ttl.ttl'},
  {value: 'json', title: 'Uplifted JSON-LD', fn: 'uplifted.jsonld'},
];

class BackendService {

  jsonUplift(jsonDoc, context, output='all') {
    const formData = new FormData();
    formData.append('output', output);
    formData.append('context', context);
    formData.append('json', jsonDoc);
    return httpService.post(`${BACKEND_URL}/json-uplift`, formData, {
          responseType: 'blob'
        })
        .then(res => jszip.loadAsync(res.data))
        .then(zipfile => Promise.all(upliftOutputFormats.map(async fmt => [fmt.value, await zipfile.file(fmt.fn).async('string')])));
  }

  getJsonUpliftOutputFormats() {
    return upliftOutputFormats;
  }

}

export default new BackendService();