const toDateTimeString = function(timestamp) {
  const d = new Date(1000*timestamp);
  return d.toLocaleString();
}

const toProcResultStrings = function(proc_results) {
  return proc_results.map(
    (p) => p.proc_name + ": " + p.result
  );
}

var app = new Vue({
  el: '#vue_runs',
  created() {this.get_runs()},

  data: {
    runs: []
  },

  methods: {

    get_runs: function() {
      fetch('api/runs/')
        .then(response => response.json())
        .then(jsonData => this.runs = jsonData.run_results.map(
          (r) => {
            return {
              id: r.id,
              description: r.description,
              timestamp_start: toDateTimeString(r.timestamp_start),
              timestamp_stop: toDateTimeString(r.timestamp_stop),
              proc_results: r.proc_results
              // results: toProcResultStrings(r.proc_results)
            }
          }
        ))
    }
  },
})