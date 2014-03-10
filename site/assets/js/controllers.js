var simpylControllers = angular.module('simpylControllers', [])

simpylControllers.controller('NewRunCtrl', function($scope, $http, $window) {
  $scope.run_init = {description: "", environment_name: "", proc_inits: []};

  $scope.selected_proc_init = {};

  $http.get('api/envs').success(
      function(data, status) {
          $scope.envs = data.environment_names;
          $scope.run_init.environment_name = $scope.envs[0];
      });

  $http.get('api/proc_inits').success(
      function(data, status) {
          $scope.avail_proc_inits = data.proc_inits;
      });

  $scope.addProc = function() {
    $scope.selected_proc_init.run_order = $scope.run_init.proc_inits.length;
    $scope.selected_proc_init.arguments_str = $scope.selected_proc_init.arguments.map(
      function(item){
        return item.name+":"+item.value
      }).join(", ");
    // deep copy the proc_init
    $scope.run_init.proc_inits.push(jQuery.extend(true, {}, $scope.selected_proc_init));
    $scope.selected_proc_init = {};
  };

  $scope.addEnv = function () {
    $scope.envs.push($scope.run_init.environment_name);
  };

  $scope.postRun = function () {
    $http.post('api/newrun', $scope.run_init).success(
      function(data, status) {
        $window.location.href = '/runs';
      }
    )
  }

});

simpylControllers.controller('RunsCtrl', function($scope, $http) {
  // function to create a string for all proc results
  $scope.resultsString = function(result) {
    return result.proc_results.map(
      function(proc_result) {
        return proc_result.proc_name + ":\n" + proc_result.result;
      }).join("\r\n");
  }

  // function to format the timestamps in a readable way
  $scope.timestampString = function(timestamp) {
    var d = new Date(1000*timestamp);
    return d.toLocaleString()
  }

  $http.get('api/runs').success(
    function(data, status) {
      $scope.run_results = data.run_results;
      $scope.run_results.map(
        function(result) {
          result.result = $scope.resultsString(result);
          result.timestamp_start = $scope.timestampString(result.timestamp_start);
          result.timestamp_stop = $scope.timestampString(result.timestamp_stop);
        });
  });
});


simpylControllers.controller('RunDetailCtrl', function($scope, $http, $location) {
  $http.get('api/run/'+($location.search()).runid).success(
    function(data, status) {
      $scope.run_result = data.run_result;
    });
});