
var baseUrl = 'http://localhost:8888';

$(function () {

      var $modules = $('#modules');

      $.ajax({
        type: 'GET',
        url: baseUrl + '/modules/list_available',
        dataType: 'json',
        success: function (modules) {
          console.log(modules);
          $.each(modules.modules, function (i, module) {
            $modules.append('<li> ' + module + '</li>');
          });
        },

        error: function (xhr, status, error) {
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });
