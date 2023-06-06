import backendService from "@/services/backend.service";
import jsYaml from "js-yaml";
import axios from 'axios';

const getErrorMessage = async err => {
  try {
    if (err.response) {
      const errText = await err.response.data.text();
      const errObj = JSON.parse(errText);
      if (errObj?.detail?.msg) {
        let errMsg = errObj.detail.msg;
        if (errObj?.detail?.cause) {
          errMsg += ': ' + errObj.detail.cause.split('|', 2)[1];
        }
        return errMsg;
      }
    }
  } catch {
    // ignore
  }
  if (err.message) {
    return err.message;
  }
  return 'Unknown error';
}

const REVIVED_CLASSES = ['InputStep', 'OutputStep', 'UpliftStep'];
const revive = (obj) => {
  if (!REVIVED_CLASSES.includes(obj.type)) {
    throw new Error('Unknown class ' + obj.type);
  }
  const step = eval(`new ${obj.type}()`);
  step.serializableFields.filter(k => k !== 'type').forEach(k => step[k] = obj[k]);
  return step;
};

class BaseStep {

  title = '';
  _contents = '';
  pending = true;
  modified = false;
  output = null;
  errors = [];
  loading = false;
  _serializableFields = [];

  constructor(title) {
    if (this.constructor === BaseStep) {
      throw new Error('Abstract class cannot be instantiated');
    }

    Object.defineProperty(this, 'type', {
      enumerable: true,
      configurable: false,
      get() {
        return this.constructor.name;
      },
    });

    this.title = title;
  }

  // eslint-disable-next-line no-unused-vars
  async _run(input) {
    // Do nothing by default
    return true;
  }

  async run(input, force = false) {
    if (typeof this._run === 'function') {
      if (!this.pending && !this.modified && !force) {
        return true;
      }
      this.errors = [];
      this.loading = true;
      try {
        const result = await this._run(input);
        const runOk = result === true || (typeof result === 'undefined' && !this.errors.length);
        if (runOk) {
          this.modified = false;
          this.pending = false;
        }
        return runOk;
      } finally {
        this.loading = false;
      }
    }
    return true;
  }

  toJSON(excludeFields = null) {
    const serializable = {};
    this.serializableFields
      .filter(f => !excludeFields || !excludeFields.includes(f))
      .forEach(k => serializable[k] = this[k]);
    return serializable;
  }

  get serializableFields() {
    return [
      'type', 'title', 'contents',
      ...(this._serializableFields || [])
    ];
  }

  get contents() {
    return this._contents;
  }

  set contents(v) {
    if (this._contents !== v) {
      this._contents = v;
      this.modified = true;
    }
  }
}

class BaseContentStep extends BaseStep {

  _inputSources = ['contents', 'url'];
  _inputSource = 'contents';
  _url = null;
  mode = 'json';
  _serializableFields = ['contents', 'url', 'mode', 'inputSource'];
  contentsFetched = false;

  constructor(title) {
    super(title);
    if (this.constructor === BaseStep) {
      throw new Error('Abstract class cannot be instantiated');
    }
  }

  get inputSource() {
    return this._inputSource;
  }

  set inputSource(v) {
    if (!v) {
      return;
    }
    if (v === this._inputSource) {
      return;
    }
    if (!this._inputSources.includes(v)) {
      throw new Error(`Input source "${v}" not in ${this._inputSources}`);
    }
    this._inputSource = v;
    this.modified = true;
  }

  toJSON(excludeFields = null) {
    if (!Array.isArray(excludeFields)) {
      excludeFields = [];
    }
    if (this._inputSource === 'contents') {
      excludeFields.push('url');
    } else {
      excludeFields.push('contents');
    }
    return super.toJSON(excludeFields);
  }

  async fetchContents(force = false) {
    if (!this.modified && this.contentsFetched && !force) {
      return true;
    }
    if (this._inputSource === 'url') {
      if (!this.url || !this.url.trim()) {
        this.errors = [
          'A URL is required'
        ];
        return false;
      }
      try {
        const response = await axios.get(this.url, {
          responseType: "text",
        });
        this.contents = response.data;
        this.errors = [];
        this.contentsFetched = true;
        return true;
      } catch (e) {
        console.log('Error loading remote URL', this.url, e);
        this.errors = [
          'Error loading data from remote URL'
        ];
      }
    }
    return false;
  }

  get url() {
    return this._url;
  }

  set url(v) {
    if (v !== this._url) {
      this._url = v;
      this.modified = true;
      this.contentsFetched = false;
    }
  }

}

class InputStep extends BaseContentStep {

  output = null;
  pending = false;

  constructor() {
    super('Input step');
    this.mode = 'json';
    Object.defineProperty(this, 'output', {
      enumerable: true,
      get() {
        return {
          json: this.contents,
        };
      },
      set() {
        // do nothing
      },
    });
  }

  get pending() {
    return false;
  }

  async _run() {
    if (!await this.fetchContents(true)) {
      return false;
    }
    try {
      const inputData = jsYaml.load(this.contents);
      if (typeof inputData !== 'object') {
        console.log('Expected type object, got', typeof inputData)
        this.errors = [
          'Input data must be an object or array'
        ];
      }
    } catch {
      this.errors = [
        'Input data is not a valid JSON or YAML document'
      ];
    }
  }

}

class OutputStep extends BaseStep {

  constructor() {
    super('Output step');
  }

  async _run(input) {
    this.output = input;
  }

}

class UpliftStep extends BaseContentStep {

  constructor(title) {
    super(title);
    this.mode = 'yaml';
  }

  async _run(input) {
    if (!await this.fetchContents(true)) {
      return false;
    }
    try {
      const result = await backendService.jsonUplift(input.json, this.contents)
        .then(r => this.result = Object.fromEntries(r))
        .finally(() => {
          this.loading = false;
        });
      this.output = result;
    } catch (e) {
      console.log(`Error running ${this.type} step`, e);
      this.errors = [await getErrorMessage(e)];
    }
  }
}

export default {BaseStep, InputStep, OutputStep, UpliftStep, revive};
