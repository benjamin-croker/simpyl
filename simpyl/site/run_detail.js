const toDateTimeString = function(timestamp) {
  const d = new Date(1000*timestamp);
  return d.toLocaleString();
}

const toProcResultStrings = function(proc_results) {
  return proc_results.map(
    (p) => p.proc_name + ": " + p.result
  );
}

const formatProc = function(proc) {
  return {
    ...proc,
    timestamp_start: toDateTimeString(proc.timestamp_start),
    timestamp_stop: toDateTimeString(proc.timestamp_stop)
  };
}

const formatRun = function(run) {
  return {
    ...run,
    proc_results: run.proc_results.map(formatProc)
  }
}

const getRunId = function() {
  let searchParams = new URLSearchParams(window.location.search)
  if(!searchParams.has('runid')) {
    return null;
  }
  return searchParams.get('runid');
}

var app = new Vue({
  el: '#vue_run',
  created() {
    this.getRun();
    this.getLog();
    this.getFigures();
  },

  data: {
    run_result: {},
    log: "",
    figures: []
  },

  methods: {
    getRun: function() {
      let runid = getRunId();
      if(!runid) {
        return;
      }
      fetch('api/run/'+runid)
        .then(response => response.json())
        .then(jsonData => this.run_result = formatRun(jsonData.run_result))
    },

    getLog: function() {
      let runid = getRunId();
      if(!runid) {
        return;
      }
      fetch('api/log/'+runid)
        .then(response => response.json())
        .then(jsonData => this.log = jsonData.log)
    },

    getFigures: function() {
      let runid = getRunId();
      if(!runid) {
        return;
      }
      fetch('api/figures/'+runid)
        .then(response => response.json())
        .then(jsonData => this.figures = jsonData.figures)
    }
  }
})