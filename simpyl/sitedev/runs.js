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
  created() {this.getRuns()},

  data: {
    runs: []
  },

  methods: {

    getRuns: function() {
      fetch('api/runs/')
        .then(response => response.json())
        .then(jsonData => this.runs = jsonData.run_results.map(
          (r) => {
            return {
              ...r,
              timestamp_start: toDateTimeString(r.timestamp_start),
              timestamp_stop: toDateTimeString(r.timestamp_stop)
            }
          }
        ))
        .catch(error => this.runs = [])
    }
  },
})