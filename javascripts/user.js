var $modules = $('#modules');
var $body = $('body');
var baseUrl = window.location.origin;
var newTabUrl= baseUrl.replace('s','').substr(0, baseUrl.lastIndexOf(':')-1);
var loginURL = baseUrl + '/login';

$(document).ready(function() {
  getRunningModules();
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

$('#delete_account').click(function(){
  $("#modal_placeholder").append(Mustache.render(document.getElementById("delete_account_modal").innerHTML));

  $("#confirm_delete_account").click(function(){
    if(window.confirm("Do you really want to delete your account. You will no longer be able to connect and your data will be lost.")){
      let password = $("#password_input").val();
      $.ajax({
        type: "DELETE",
        url: "/delete_account?password=" + password,
        success: function(){
          // TODO this href also does not work, but after reloading the page the user gets redirected to login (because no token, so actual logic works)
          window.location.href = loginURL;
        },
        error: function(xhr, status, error){
          // TODO if error occurs modal will close without showing the alert and console logs are also empty
          console.log(xhr);
          console.log(status);
          console.log(error);
          if(errorObj.reason == "password_validation_failed"){
            alert("incorrect password");
          }
        }
      });
    }
  });
});

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

function getRunningModules(){
  return $.ajax({
    type: 'GET',
    url: '/execution/running',
    dataType: 'json',
    async: false,
    success: function (data) {
      $.each(data.running_modules, function (i, module) {
        if(i!="platform"){
          $modules.append(Mustache.render(document.getElementById('runningModulesTemplate').innerHTML, {"port":module.port, "name":i}));
        }
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
