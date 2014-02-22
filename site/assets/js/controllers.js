'use strict';

/* Controllers */

var simpylApp = angular.module('simpylApp', []);

simpylApp.controller('EnvListCtrl', function($scope, $http) {
  $http.get('api/envs').success(
      function(data, status) {
          $scope.envs = data.environment_names;
      }
  );
});
