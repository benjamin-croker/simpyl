var simpylApp = angular.module('simpylApp', []);

simpylApp.controller('NewRunCtrl', function($scope, $http, $location) {
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
        $location.set('/runs');
      }
    )
  }

});

simpylApp.controller('RunsCtrl', function($scope, $http) {
  $http.get('api/runs').success(
    function(data, status) {
      $scope.run_results = data.run_results;
  });
});