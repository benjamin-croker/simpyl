var app = new Vue({
  el: '#vue_runs',
  created() {this.get_runs()},
  data: {
    runs: {}
  },
  methods: {
    get_runs: function() {
      fetch('api/runs/')
        .then(response => response.json())
        .then(jsonData => this.runs = JSON.stringify(jsonData, undefined, 2))
    }
  },
})