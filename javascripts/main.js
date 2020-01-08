
var baseUrl = 'http://localhost:8888';

var $modules = $('#modules');
var modulesInstalledList = [];

function addModuleInstalled(module) {
  if ($('.download').attr('data-id') == module) {
    $('[data-id=' + module + ']').remove();
  } else {
    $modules.append('<li id=' + module + '><p><strong>' + module + '</strong></p></li>');
  }
}

function addModuleAvailable(module) {
  if (modulesInstalledList.indexOf(module) == -1) {
    $modules.append('<li id=' + module + '><p><strong>' + module + '</strong></p>' +
                    '<button data-id=' + module + ' class=download> Download </button></li>');
  }
}

$(function () {
      $.ajax({
        type: 'GET',
        url: baseUrl + '/modules/list_installed',
        dataType: 'json',
        success: function (modules) {
          console.log(modules);
          $.each(modules.installed_modules, function (i, module) {
            modulesInstalledList.push(module);
            addModuleInstalled(module);
          });
        },

        error: function (xhr, status, error) {
          alert('error loading installed modules');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
      $.ajax({
        type: 'GET',
        url: baseUrl + '/modules/list_available',
        dataType: 'json',
        success: function (modules) {
          console.log(modules);
          $.each(modules.modules, function (i, module) {
            addModuleAvailable(module);
          });
        },

        error: function (xhr, status, error) {
          alert('error loading available modules');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });

$modules.delegate('.download', 'click', function () {
    console.log('clicked');
    $.ajax({
      type: 'GET',
      url: baseUrl + '/modules/download?module_name=' + $(this).attr('data-id'),
      dataType: 'json',
      success: function (module) {
        console.log(module);
        modulesInstalledList.push(module);
        addModuleInstalled(module.module);
      },

      error: function (xhr, status, error) {
        alert('error downloading module');
        console.log(error);
        console.log(status);
        console.log(xhr);
      },
    });
  });
