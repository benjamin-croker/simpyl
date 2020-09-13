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
  el: '#vue_run',
  created() {this.getRun()},

  data: {
    run: {}
  },

  methods: {

    getRun: function() {
      let searchParams = new URLSearchParams(window.location.search)

      if(!searchParams.has('runid')) {
        this.run = {};
        return;
      }

      fetch('api/run/'+searchParams.get('runid'))
        .then(response => response.json())
        .then((jsonData) => {
          let r = jsonData.run_result
          this.run = {
            ...r,
            proc_results: r.proc_results.map(
              (p) => {
                return {
                  ...p,
                  timestamp_start: toDateTimeString(p.timestamp_start),
                  timestamp_stop: toDateTimeString(p.timestamp_stop)
                }
              }
            )
          };
        })
        .catch(error => this.run = {})

    }
  },
})