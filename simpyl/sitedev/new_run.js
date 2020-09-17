const defaultInput = {selected: '', value: 0}

var app = new Vue({
  el: '#vue_test',
  created() {},

  data: {
    input: {...defaultInput},
    test_array: []
  },

  methods: {
    appendInput: function() {
      this.test_array = [...this.test_array, this.input];
      this.input = {...defaultInput};
    }
  },
})