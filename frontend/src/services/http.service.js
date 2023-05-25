import axios from 'axios';

const BACKEND_URL = window.ogcPlayground.BACKEND_URL;

const client = axios.create({
  baseURL: BACKEND_URL,
});

export default new Proxy({}, {
  get(target, prop) {
    return client[prop];
  }
});