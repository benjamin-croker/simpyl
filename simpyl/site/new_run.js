const { createApp } = Vue

// for creating a deep copy
const formatProcInit = function (proc_init, run_order) {
  const copied_proc_init = {
    proc_name: proc_init.proc_name,
    run_order: run_order,
    arguments: proc_init.arguments.map(
      (a) => {
        return { name: a.name, value: a.value };
      }
    ),
    arguments_str: proc_init.arguments.map(
      item => item.name + ":" + item.value
    ).join(", ")
  };
  return copied_proc_init;
}


const createRequest = function (run_init) {
  return {
    method: 'POST',
    headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json;charset=utf-8'
    },
    body: JSON.stringify(run_init)
  };
}


createApp({
  created() { this.getProcInits() },

  data() {
    return {
      proc_inits: {},
      proc_working: {},
      run_init: {
        description: "",
        proc_inits: []
      }
    }
  },

  methods: {
    addProcToRun: function () {
      // do a deep copy of the working data
      let proc_working = formatProcInit(
        this.proc_working, this.run_init.proc_inits.length
      )
      this.run_init.proc_inits = [...this.run_init.proc_inits, proc_working];
      this.proc_working = {};
    },

    startRun: function () {
      const req = createRequest(this.run_init);
      fetch('api/newrun', req)
        .then(window.location.href = '/runs')
        .catch((err) => console.log(err))
    },

    getProcInits: function () {
      fetch('api/proc_inits')
        .then(response => response.json())
        .then(jsonData => this.proc_inits = jsonData.proc_inits)
    }
  }
}).mount('#vue_test')