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
        $modules.append(Mustache.render(document.getElementById('runningModulesTemplate').innerHTML, {"port":module.port, "name":i}));
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
