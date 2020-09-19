var app = new Vue({
  el: '#vue_test',
  created() {this.getProcInits()},

  data: {
    proc_inits: {},
    proc_working: {},
    run_init: {
      description: "",
      environment_name: "default",
      proc_inits: []
    }
  },

  methods: {
    addProcToRun: function() {
      // add an ID
      this.proc_working.run_order = this.run_init.proc_inits.length;
      // and convert the argument string
      this.proc_working.arguments_str = this.proc_working.arguments.map(
        item => item.name+":"+item.value
      ).join(", ");

      this.run_init.proc_inits = [...this.run_init.proc_inits, this.proc_working];

      this.proc_working = {};
    },
    getProcInits: function() {
      fetch('api/proc_inits')
        .then(response => response.json())
        .then(jsonData => this.proc_inits = jsonData.proc_inits)
    }
  },
})