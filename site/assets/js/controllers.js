'use strict';

/* Controllers */

var simpylApp = angular.module('simpylApp', []);

simpylApp.controller('EnvListCtrl', function($scope, $http) {
  $http.get('api/envs').success(
      function(data, status) {
          $scope.envs = data.environment_names;
      });
  $http.get('api/proc_inits').success(
      function(data, status) {
          $scope.proc_inits = data.proc_inits;
      });
});
