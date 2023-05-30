import backendService from "@/services/backend.service";
import jsYaml from "js-yaml";

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
  contents = '';
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

    Object.defineProperty(this, 'type',{
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

  toJSON() {
    const serializable = {};
    this.serializableFields.forEach(k => serializable[k] = this[k]);
    return serializable;
  }

  get serializableFields() {
    return [
      'type', 'title',  'contents',
      ...(this._serializableFields || [])
    ];
  }
}

class InputStep extends BaseStep {

  _serializableFields = ['mode'];
  output = null;
  pending = false;
  mode = 'json';

  constructor() {
    super('Input step');
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
    })
  }

  get pending() {
    return false;
  }

  async _run() {
    try {
      const inputData = jsYaml.load(this.contents);
      if (typeof inputData !== 'object') {
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

class UpliftStep extends BaseStep {

  _serializableFields = ['mode'];
  mode = 'yaml';

  constructor(title) {
    super(title);
  }

  async _run(input) {
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