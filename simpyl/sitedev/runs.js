const toDateTimeString = function(timestamp) {
  const d = new Date(1000*timestamp);
  return d.toLocaleString();
}

const toProcResultStrings = function(proc_results) {
  return proc_results.map(
    (p) => p.proc_name + ": " + p.result
  );
}

const formatRun = function(run) {
  return {
    ...run,
    timestamp_start: toDateTimeString(run.timestamp_start),
    timestamp_stop: toDateTimeString(run.timestamp_stop)
  };
}

var app = new Vue({
  el: '#vue_runs',
  created() {this.getRuns()},

  data: {
    run_results: []
  },

  methods: {
    getRuns: function() {
      fetch('api/runs/')
        .then(response => response.json())
        .then(jsonData => this.run_results = jsonData.run_results.map(formatRun))
    }
  },
})