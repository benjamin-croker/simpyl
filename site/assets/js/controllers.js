'use strict';

/* Controllers */

var simpylApp = angular.module('simpylApp', []);

simpylApp.controller('EnvListCtrl', function($scope, $http) {
  $scope.run_init = {discription: "", environment_name: "", proc_inits: []};

  $scope.selected_proc_init = {};
  $scope.selected_env = "";

  $http.get('api/envs').success(
      function(data, status) {
          $scope.envs = data.environment_names;
      });

  $http.get('api/proc_inits').success(
      function(data, status) {
          $scope.avail_proc_inits = data.proc_inits;
      });

  $scope.addProc = function() {
    // deep copy the proc_init
    $scope.run_init.proc_inits.push(jQuery.extend(true, {}, $scope.selected_proc_init));
    $scope.selected_proc_init = {};
  };
});
