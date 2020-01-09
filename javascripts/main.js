
var baseUrl = 'http://localhost:8888';

var $modules = $('#modules');
var modulesInstalledList = [];
var modulesTemplate =    '' +
       '<li>' +
            '<p><strong>{{name}}</strong></p>' +
            '<button data-id={{name}} class=download>Download</button>' +
            '<button id={{name}} class=uninstall>Uninstall</button>' +
          '</li>';

function addModuleInstalled(module) {
  $modules.append(Mustache.render(modulesTemplate, { name: '' + module + '' }));
  $('[data-id=' + module + ']').addClass('noedit');
  $('[id=' + module + ']').addClass('edit');
}

function addModuleAvailable(module) {
  if (modulesInstalledList.indexOf(module) == -1) {
    $modules.append(Mustache.render(modulesTemplate, { name: '' + module + '' }));
    $('[data-id=' + module + ']').addClass('noedit');
    $('[id=' + module + ']').addClass('edit');
  }
}

/*

function removeModuleInstalled(module) {
  if ($('.uninstall').attr('data-id') == module) {
    $('[data-id=' + module + ']').remove();
    var $downloadBtn = $('<button data-id=' + module + ' class=download> Download </button>');
    $('[id=' + module + ']').append($downloadBtn);
  }
}
*/
$(function () {
      $.ajax({
        type: 'GET',
        url: baseUrl + '/modules/list_installed',
        dataType: 'json',
        success: function (modules) {
          $.each(modules.installed_modules, function (i, module) {
            modulesInstalledList.push(module);
            console.log(module);
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
    var $li = $(this).closest('li');

    console.log('clicked');
    $.ajax({
      type: 'GET',
      url: baseUrl + '/modules/download?module_name=' + $(this).attr('data-id'),
      dataType: 'json',
      success: function (module) {
        console.log(module.module);
        modulesInstalledList.push(module.module);
        $li.addClass('edit');
      },

      error: function (xhr, status, error) {
        alert('error downloading module');
        console.log(error);
        console.log(status);
        console.log(xhr);
      },
    });
  });

$modules.delegate('.uninstall', 'click', function () {
    console.log('clicked uninstall');
    var $li = $(this).closest('li');
    $.ajax({
      type: 'GET',
      url: baseUrl + '/modules/uninstall?module_name=' + $(this).attr('id'),
      dataType: 'json',
      success: function (module) {
        console.log(module.module);
        var index = modulesInstalledList.indexOf(module.module);
        if (index > -1) {
          modulesInstalledList.splice(index, 1);
          $li.removeClass('edit');
        }

      },

      error: function (xhr, status, error) {
        alert('error downloading module');
        console.log(error);
        console.log(status);
        console.log(xhr);
      },
    });
  });
