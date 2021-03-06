// for creating a deep copy
const formatProcInit = function(proc_init, run_order) {
  const copied_proc_init = {
    proc_name: proc_init.proc_name,
    run_order: run_order,
    arguments: proc_init.arguments.map(
      (a) => {
        return {name: a.name, value: a.value};
      }
    ),
    arguments_str: proc_init.arguments.map(
      item => item.name+":"+item.value
    ).join(", ")
  };
  return copied_proc_init;
}


const createRequest = function(run_init) {
  return {
    headers: { "Content-Type": "application/json; charset=utf-8" },
    method: 'POST',
    body: JSON.stringify(run_init)
  };
}


var app = new Vue({
  el: '#vue_test',
  created() {this.getProcInits()},

  data: {
    proc_inits: {},
    proc_working: {},
    run_init: {
      description: "",
      proc_inits: []
    }
  },

  methods: {
    addProcToRun: function() {
      // do a deep copy of the working data
      let proc_working = formatProcInit(
        this.proc_working, this.run_init.proc_inits.length
      )
      this.run_init.proc_inits = [...this.run_init.proc_inits, proc_working];
      this.proc_working = {};
    },

    startRun: function() {
      fetch('api/newrun', createRequest(this.run_init))
        .then(window.location.href = '/runs')
    },

    getProcInits: function() {
      fetch('api/proc_inits')
        .then(response => response.json())
        .then(jsonData => this.proc_inits = jsonData.proc_inits)
    }
  }
})