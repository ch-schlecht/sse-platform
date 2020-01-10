
var baseUrl = 'http://localhost:8888';
var $modules = $('#modules');
var modulesInstalledList = [];
var modulesTemplate =    '' +
       '<li name={{name}}>' +
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
    $.ajax({
      type: 'GET',
      url: baseUrl + '/modules/download?module_name=' + $(this).attr('data-id'),
      dataType: 'json',
      success: function (module) {
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
    var $li = $(this).closest('li');
    $.ajax({
      type: 'GET',
      url: baseUrl + '/modules/uninstall?module_name=' + $(this).attr('id'),
      dataType: 'json',
      success: function (module) {
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
      $(this).addClass('running');
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
      $('#' + $(this).attr('id') + '.start').removeClass('running');
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
        url: baseUrl + '/configs/view?module_name=' + $li.attr('name'),
        dataType: 'json',
        success: function (module) {
          $('.bg-modal').css('display', 'flex');
          $('#save').addClass($li.attr('name'));
          console.log(module.config);

          //var obj = JSON.parse(module.config);
          var pretty = JSON.stringify(module.config, undefined, 4);
          $('#config-area').val(pretty);
        },

        error: function (xhr, status, error) {
          alert('error loading config of module');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });

$body.delegate('.close', 'click', function () {
      $('.bg-modal').css('display', 'none');
      $('#config-area').val('');
    });

$body.delegate('#save', 'click', function () {

      prettyPrint();
      config = $('#config-area').val();
      console.log(config);
      $.ajax({
        type: 'POST',
        url: baseUrl + '/configs/update?module_name=' + $(this).attr('class'),
        data: config,
        success: function (module) {
          console.log(module);
          $('.bg-modal').css('display', 'none');
          $('#config-area').val('');
        },

        error: function (xhr, status, error) {
          alert('error saving config of module, check syntax');
          console.log(error);
          console.log(status);
          console.log(xhr);
        },
      });
    });

function prettyPrint() {
  var $ugly = $('#config-area').val();
  var obj = JSON.parse($ugly);
  var pretty = JSON.stringify(obj, undefined, 4);
  $('#config-area').val(pretty);
}
