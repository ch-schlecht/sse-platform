var baseUrl = window.location.origin;
var newTabUrl= baseUrl.replace('https','http').substr(0, baseUrl.lastIndexOf(':'));
var loginURL = baseUrl + '/login';
var $modules = $('#modules');
var $body = $('body');
var routingTable = {};


/**
 * on page load - get all available and installed modules
 * add installed modules to list
 */
$(document).ready(function() {
    getRouting();
    getRunningModules();
    getUsersWithRoles();

    getEnmeshedInformation();
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
    var win = window.open(routingTable[$name] + tailUrl, '_blank');
    if (win) {
      win.focus();
    } else {
      alert('Please allow popups for this page.');
    }
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

/**
 * get the routing table to correctly set urls of the modules
 */
function getRouting(){
  $.ajax({
    type: "GET",
    url: "/routing",
    success: function(response){
      routingTable = response;
      console.log(routingTable);
    },
    error: function(xhr, status, error){
      if(xhr.status === 401){
        window.location.href = loginURL;
      }
    }
  })
}

function syncProfileInformation() {
  $.ajax({
    type: "GET",
    url: "/sync",
    success: function(response){
      console.log(response)
      console.log("Succesfully synced account data")
      location.reload();
    },
    error: function(xhr, status, error) {
      if(xhr.status === 400){
        window.location.href = loginURL;
      }
    }
  })
}

function getEnmeshedInformation(){
  $.ajax({
    type: "GET",
    url: "/enmeshed",
    success: function(response){
      console.log(response);
      id = response.id
      user = response.user
      console.log(id)
      $('#enmeshed').append(Mustache.render(document.getElementById('enmeshed_profile').innerHTML, {"id":id.enmeshed_id, "user":user}));
    },
    error: function(xhr, status, error){
      if(xhr.status === 400){
        window.location.href = loginURL;
      } else if (xhr.status === 404) {
        $('#enmeshed').append(Mustache.render(document.getElementById('enmeshed_qr').innerHTML));
      }
    }
  });
}
