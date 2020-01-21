
var baseUrl = 'https://localhost:8888';
var newTabUrl = 'https://localhost';
var $body = $('body');
var accessToken;
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
		//window.location.replace(origin + '/login?'); Reloads :(
		window.history.pushState("login", "SSE Platform Login", origin + '/login?');
		window.location.hash = 'login';
});

$(window).trigger('hashchange');

/**
 * load username and password if rememberMe was checked
 */
$(function () {

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
		url: baseUrl + '/login?nickname=' + username + '&password=' + password,
		success: function (data) {
			accessToken = data.access_token;
			localStorage.setItem('token', JSON.stringify(accessToken));
			// window.sessionStorage.accessToken = accessToken;
			// document.cookie='access_token=' + accessToken
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
			url: baseUrl + '/register?email=' + mail + '&nickname=' + username + '&password=' + password,
			success: function (data) {
				alert('Registered successfully.');
				accessToken = data.access_token;
				localStorage.setItem('token', JSON.stringify(accessToken));
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
	var token = JSON.parse(localStorage.getItem('token'));
	$.ajax({
		type: 'GET',
		url: baseUrl + '/main?access_token=' + token,

		success: function (data) {
			setTimeout(function() {
				window.location.href = baseUrl + '/main?access_token=' + token;
			}, 333);
		},

		error: function (xhr, status, error) {
			if (xhr.status == 401) {
				alert('no access token or not valid');
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
