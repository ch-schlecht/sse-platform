
var baseUrl = 'http://localhost:8888';
var $modules = $('#modules');
var modulesInstalledList = [];
var modulesTemplate =    '' +
       '<li>' +
            '<p><strong>{{name}}</strong></p>' +
            '<button data-id={{name}} class=download>Download</button>' +
            '<button id={{name}} class=uninstall>Uninstall</button>' +
            '<button id={{name}} class=config>Config</button>' +
            '<button id={{name}} class=start>Run</button>' +
            '<button id={{name}} class=stop>Stop</button>' +
          '</li>';
var $body = $('body');

$(document).on({
    ajaxStart: function () { $body.addClass('loading');    },

    ajaxStop: function () { $body.removeClass('loading');  },
  });

function addModuleInstalled(module) {
  $modules.append(Mustache.render(modulesTemplate, { name: '' + module + '' }));
  var $mod = $('[data-id=' + module + ']');
  var $li = $mod.closest('li');
  $li.addClass('edit');
  $('[data-id=' + module + ']').addClass('noedit');
  $('[id=' + module + ']').addClass('edit');
}

function addModuleAvailable(module) {
  if (modulesInstalledList.indexOf(module) == -1) {
    $modules.append(Mustache.render(modulesTemplate, { name: '' + module + '' }));
    $('[data-id=' + module + ']').addClass('noedit');
    $('[id=' + module + ']').addClass('edit');

    //get element with module id and start class
    //$('#' + module + '.start').addClass('running');
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
        alert('error uninstalling module');
        console.log(error);
        console.log(status);
        console.log(xhr);
      },
    });
  });

$modules.delegate('.start', 'click', function () {

      $.ajax({
        type: 'GET',
        url: baseUrl + '/execution/start?module_name=' + $(this).attr('id'),
        dataType: 'json',
        success: function (module) {
          console.log('started');
          console.log(module.reason);

          $(this).addClass('running');
        },

        error: function (xhr, status, error) {
          alert('error starting module');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });

$modules.delegate('.stop', 'click', function () {

      $.ajax({
        type: 'GET',
        url: baseUrl + '/execution/stop?module_name=' + $(this).attr('id'),
        dataType: 'json',
        success: function (module) {
          alert('stopped');

          $('#' + $(this).attr('id') + '.start').removeClass('running');
        },

        error: function (xhr, status, error) {
          alert('error stopping module');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });

$modules.delegate('.config', 'click', function () {
      var $li = $(this).closest('li');
      $.ajax({
        type: 'GET',
        url: baseUrl + '/configs/view?module_name=' + $(this).attr('id'),
        dataType: 'json',
        success: function (module) {
          console.log(module.config);
        },

        error: function (xhr, status, error) {
          alert('error loading config of module');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });
