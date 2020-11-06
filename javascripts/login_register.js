
var baseUrl = window.location.origin;
var newTabUrl= baseUrl.replace('s','').substr(0, baseUrl.lastIndexOf(':')-1);
var $body = $('body');
/**
 * on tabchange- adds or removes selected class from tab
 */

$(window).on('hashchange', function () {
	 if (location.hash.slice(1)=='register') {
  		$('.card').addClass('extend');
  		$('#login').removeClass('selected');
  		$('#register').addClass('selected');
    }else {
  		$('.card').removeClass('extend');
  		$('#login').addClass('selected');
  		$('#register').removeClass('selected');
	 }

});



/** This function checks if email is valid.
 * @param {String} email - email (input)
 */
function validateEmail(email) {
  var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

/**
 * on page load, modify URL by setting /login?#login to define a login url for this page
 */
$(document).ready(function () {
		var pathname = window.location.pathname; // Returns path only (/path/example.html)
		var url      = window.location.href;     // Returns full URL (https://example.com/path/example.html)
		var origin   = window.location.origin;   // Returns base URL (https://example.com)
		window.history.pushState("login", "SSE Platform Login", origin + '/login?'); //needs firefox 4+, works in chrome
		window.location.hash = 'login';
		//$('#login').addClass('selected');


});

$(window).trigger('hashchange');

/**
 * load username and password if rememberMe was checked
 */
$(document).ready(function () {

    if (localStorage.chkbox && localStorage.chkbox != '') {
        $('#rememberMe').attr('checked', 'checked');
        $('input#username').val(localStorage.username);
        $('input#password').val(localStorage.pass);
    } else {
        $('#rememberMe').removeAttr('checked');
        $('input#username').val('');
        $('input#password').val('');
    }
	});

/**
 * login - This is a function to login a user in our database.
 * save username and password
 */
function login() {
  var username = $('input#username').val();
  var password = $('input#password').val();

	if ($('#rememberMe').is(':checked')) {
			// save username and password
			localStorage.username = username;
			localStorage.pass = password;
			localStorage.chkbox = $('#rememberMe').val();
	} else {
			localStorage.username = '';
			localStorage.pass = '';
			localStorage.chkbox = '';
		}

	$.ajax({
		type: 'POST',
		url: '/login?nickname=' + username + '&password=' + password,
		success: function (data) {
			loadMainPage();
		},

		error: function (xhr, status, error) {
			if (xhr.status == 409) {
				alert(username + ' not found.');
			} else if (xhr.status == 401) {
				alert('Invalid password.');
			} else {
				alert('error login');
				console.log(error);
				console.log(status);
				console.log(xhr);
			}
		},
	});
}

/**
 * register - This is a function to register a user in our database.
 */
function register() {

  var username = $('input#newusername').val();
  var mail = $('input#email').val();
  var password = $('input#newpassword').val();

  if (validateEmail(mail)) {
		$.ajax({
			type: 'POST',
			url: '/register?email=' + mail + '&nickname=' + username + '&password=' + password,
			success: function (data) {
				alert('Registered successfully.');
				loadMainPage();
			},

			error: function (xhr, status, error) {
				if (xhr.status == 409) {
					alert(username + ' already exists.');
				} else {
					alert('error register');
					console.log(error);
					console.log(status);
					console.log(xhr);
				}
			},
		});

  }else {
    alert('Please enter a valid email!');
  }
}

$body.delegate('.login', 'click', function () {
    login();
  });

$body.delegate('.register', 'click', function () {
    register();
  });

/**
 * loadMainPage - get request to main page with query url token
 * redirect to main page
 */
function loadMainPage() {

	$.ajax({
		type: 'GET',
		url: '/main',

		success: function (data) {
			setTimeout(function() {
				window.location.href = '/main';
			}, 333);
		},

		error: function (xhr, status, error) {
			if (xhr.status == 401) {
				console.log(error);
				console.log(status);
				console.log(xhr);
			} else {
				alert('error');
				console.log(error);
				console.log(status);
				console.log(xhr);
			}
		},
	});
}
