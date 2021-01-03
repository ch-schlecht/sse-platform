var baseUrl = window.location.origin;
var newTabUrl= baseUrl.replace('s','').substr(0, baseUrl.lastIndexOf(':')-1);
var loginURL = baseUrl + '/login';
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


/**
 * on page load - get all available and installed modules
 * add installed modules to list
 */
$(document).ready(function() {
    getRunningModules();
    getUsersWithRoles();
});

/**
 * add or removes class 'loading' on ajax request
 */
$(document).on({
    ajaxStart: function () { $body.addClass('loading');    },

    ajaxStop: function () { $body.removeClass('loading');  },
  });

/**
 * on logout click -  redirect to login page
 *
 */
$('.logout').click(function () {
  $.ajax({
    type: 'POST',
    url: '/logout',
    success: function (data) {
      window.location.href = loginURL;
    },

    error: function (xhr, status, error) {
      if (xhr.status == 401) {
        window.location.href = loginURL;
      } else {
        alert('error logout');
        console.log(error);
        console.log(status);
        console.log(xhr);
      }
    },
  });
});

$('.change_password').click(function(){
  window.location.href = '/password/change';
});

/**
 * addModuleInstalled - if Module is installed:
 * add moduleTemplate to HTML and sets the ids and classes with module name
 * add class 'edit'
 * @param  {String} module name of the module
 */
function addModuleInstalled(module) {
  $modules.append(Mustache.render(modulesTemplate, { name: '' + module + '' }));
  var $mod = $('[data-id=' + module + ']');
  var $li = $mod.closest('li');
  $li.addClass('edit');
  $('[data-id=' + module + ']').addClass('noedit');
  $('[id=' + module + ']').addClass('edit');
}

/**
 * addModuleAvailable - if Module is not installed
 * add moduleTemplate to HTML and sets the ids and classes with module name
 * @param  {String} module name of the module
 */
function addModuleAvailable(module) {
  if (modulesInstalledList.indexOf(module) == -1) {
    $modules.append(Mustache.render(modulesTemplate, { name: '' + module + '' }));
    $('[data-id=' + module + ']').addClass('noedit');
    $('[id=' + module + ']').addClass('edit');
  }
}

/**
 * getRunningModules - display if a module already runs on a port
 * on success display HTML and add running class to elements
 */
function getRunningModules(){
  return $.ajax({
    type: 'GET',
    url: '/execution/running',
    dataType: 'json',
    async: false,
    success: function (data) {
      console.log(data);
      $.each(data.running_modules, function (i, module) {
        var $li = $body.find('li[name=' + i + ']');
        if(!$li.length && i!="platform"){
          $modules.append(Mustache.render(document.getElementById('runningModulesTemplate').innerHTML, {"port":module.port, "name":i}));
          return;
        }
        var $start = $body.find('button#' + i + '.start');
        var $stop = $body.find('button#' + i + '.stop');
        try {
          tailUrl = '';
          //modify URL if its SocialServ
          if(i == 'SocialServ' || i == 'chatsystem') tailUrl = '/main';
          $li.children('p').append('<span id="port"> running on port <a target="_blank" rel="noopener noreferrer" href=' + newTabUrl + '' + ':' + module.port + tailUrl + '>' + module.port + '</a></span>');
        } catch (e) {
          $li.children('p').append('<span id="port"> running on a port </span>');
        }

        $start.addClass('running');
        $stop.addClass('running');
      });
    },

    error: function (xhr, status, error) {
      alert('error loading running modules');
      console.log(error);
      console.log(status);
      console.log(xhr);
    },
  });
}

function getUsersWithRoles(){
  $.ajax({
    type: "GET",
    url:"/users",
    success: function(response){
      $.each(response.user_list, function(index, user){
        $("#users").append(Mustache.render(document.getElementById("userRoleTemplate").innerHTML, {"name": user.name}));
        $("#roleSelect_" + user.name).val(user.role);
      });
      console.log(response.user_list);
    }
  })
}

function updateUserRole(formElement){
  var userName = formElement.id;
  var assignedRole = $("#roleSelect_" + userName).val();
  $.ajax({
    type: "POST",
    url: "/roles?user_name=" + userName + "&role=" + assignedRole,
    success: function(response){
      console.log("successful") // TODO make little green alert or so
    }
  });

  return false; //needed to prevent default behaviour of a form
}

$body.delegate('.module', 'click', function () {
    var $port = $(this).attr('id');
    var $name = $(this).attr('name');
    var tailUrl = '';
    //modify URL if its SocialServ or chatsystem
    if($name == 'SocialServ' || $name == 'chatsystem') tailUrl = '/main';
    var win = window.open('' + newTabUrl + ':' + $port + '' + tailUrl, '_blank');
    if (win) {
      win.focus();
    } else {
      alert('Please allow popups for this page.');
    }
  });

/**
 * getAvailableModules - on success displays html
 * calls addModuleAvailable
 */
function getAvailableModules(){
   return $.ajax({
    type: 'GET',
    url: '/modules/list_available',
    dataType: 'json',
    async: false,
    success: function (modules) {
      console.log(modules);
      if(modules.success == true){
        $.each(modules.modules, function (i, module) {
          addModuleAvailable(module);
        });
      }
      else{
        console.log("error: " + modules.reason);
        alert("Could not connect to Github API");
      }
    },

    error: function (xhr, status, error) {
      if (xhr.status == 401) {
        window.location.href = loginURL;
      } else {
        alert('error loading available modules');
        console.log(error);
        console.log(status);
        console.log(xhr);
      }
    },
  });
}

/**
 * on download click - download module and add it to installed-list
 * add class 'edit'
 */
$modules.delegate('.download', 'click', function () {
    var $li = $(this).closest('li');
    $.ajax({
      type: 'GET',
      url: '/modules/download?module_name=' + $(this).attr('data-id'),
      dataType: 'json',
      success: function (module) {
        if(module.success == true){
          modulesInstalledList.push(module.module);
          $li.addClass('edit');
        }
        else{
          console.log("error: " + module.reason);
          alert("installation failure");
        }
      },

      error: function (xhr, status, error) {
        if (xhr.status == 401) {
          window.location.href = loginURL;
        } else {
          alert('error downloading module');
          console.log(error);
          console.log(status);
          console.log(xhr);
      }
      },
    });
  });

/**
 * on uninstall click - uninstall module and remove it from installed-list
 * removes class 'edit'
 */
$modules.delegate('.uninstall', 'click', function () {
    var $li = $(this).closest('li');
    $.ajax({
      type: 'GET',
      url: '/modules/uninstall?module_name=' + $(this).attr('id'),
      dataType: 'json',
      success: function (module) {
        var index = modulesInstalledList.indexOf(module.module);
        if (index > -1) {
          modulesInstalledList.splice(index, 1);
          $li.removeClass('edit');
        }
      },

      error: function (xhr, status, error) {
        if (xhr.status == 401) {
          window.location.href = loginURL;
        } else {
          alert('error uninstalling module');
          console.log(error);
          console.log(status);
          console.log(xhr);
        }
      },
    });
  });

/**
 * on start click - starts module if its not already running and opens new tab
 * add text to li:paragraph
 * add class 'running' to buttons
 */
$modules.delegate('.start', 'click', function () {
      var $li = $(this).closest('li');
      var $start = $(this);
      var $stop = $('#' + $(this).attr('id') + '.stop');
      $.ajax({
        type: 'GET',
        url: '/execution/start?module_name=' + $(this).attr('id'),
        dataType: 'json',
        success: function (module) {
          //console.log(module);
          if (module.reason !== 'already_running') {
            tailUrl = '';
            //modify URL if its SocialServ or chatsystem
            if(module.module == 'SocialServ' || module.module == 'chatsystem') tailUrl = '/main';
            $li.children('p').append('<span id="port"> running on port <a target="_blank" rel="noopener noreferrer" href=' + newTabUrl + '' + ':' + module.port + tailUrl + '>' + module.port + '</a></span>');

            var win = window.open('' + newTabUrl + ':' + module.port + "/main", '_blank');
            if (win) {
              win.focus();
            } else {
              alert('Please allow popups for this page.');
            }

          } /*else {
            try {
              $li.children('p').append('<span id="port"> already running on port <a target="_blank" rel="noopener noreferrer" href=' + newTabUrl + '' + ':' + module.port + '>' + module.port + '</a></span>');
            } catch (e) {
              $li.children('p').append('<span id="port"> already running on a port </span>');
            }
          }*/

          $start.addClass('running');
          $stop.addClass('running');
        },

        error: function (xhr, status, error) {
          if (xhr.status == 401) {
            window.location.href = loginURL;
          } else {
            alert('error starting module');
            console.log(error);
            console.log(status);
            console.log(xhr);
          }
        },
      });
    });

/**
 * on stop click - stops the running module
 * removes id 'port' and class 'running'
 */
$modules.delegate('.stop', 'click', function () {
      var $li = $(this).closest('li');
      var $p = $(this).siblings('p');
      var $stop = $(this);
      var $start = $('#' + $(this).attr('id') + '.start');
      var $port = $p.children('#port');
      $.ajax({
        type: 'GET',
        url: '/execution/stop?module_name=' + $(this).attr('id'),
        dataType: 'json',
        success: function (module) {
          alert('stopped');
          $stop.removeClass('running');
          $start.removeClass('running');
          $port.remove();
        },

        error: function (xhr, status, error) {
          if (xhr.status == 401) {
            window.location.href = loginURL;
          } else {
            alert('error stopping module');
            console.log(error);
            console.log(status);
            console.log(xhr);
          }
        },
      });
    });

/**
 * on config click - loads actual config of modules
 * displays 'bg-modal'
 * add class 'name' to save btn
 * convert config to JSON and display it in textarea
 */
$modules.delegate('.config', 'click', function () {
      var $li = $(this).closest('li');
      $.ajax({
        type: 'GET',
        url: '/configs/view?module_name=' + $li.attr('name'),
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
          if (xhr.status == 401) {
            window.location.href = loginURL;
          } else {
            alert('error loading config of module');
            console.log(error);
            console.log(status);
            console.log(xhr);
          }
        },
      });
    });

/**
 * on close click - resets textarea and display of bg-modal
 */
$body.delegate('.close', 'click', function () {
      $('.bg-modal').css('display', 'none');
      $('#config-area').val('');
    });

/**
 * on save click - saves content of textarea as JSON to config of module
 * resets textarea and display of bg-modal
 */
$body.delegate('#save', 'click', function () {

      try {
        prettyPrint();
      } catch (e) {
        alert('Config needs to be JSON.');
        return;
      }

      config = $('#config-area').val();
      console.log(config);
      $.ajax({
        type: 'POST',
        url: '/configs/update?module_name=' + $(this).attr('class'),
        data: config,
        success: function (module) {
          console.log(module);
          $('.bg-modal').css('display', 'none');
          $('#config-area').val('');
        },

        error: function (xhr, status, error) {
          if (xhr.status == 401) {
            window.location.href = loginURL;
          } else {
            alert('error saving config of module, check syntax');
            console.log(error);
            console.log(status);
            console.log(xhr);
          }
        },
      });
    });

/**
 * prettyPrint - prints the text of 'config-area' pretty
 */
function prettyPrint() {
  var $ugly = $('#config-area').val();
  var obj = JSON.parse($ugly);
  var pretty = JSON.stringify(obj, undefined, 4);
  $('#config-area').val(pretty);

}
