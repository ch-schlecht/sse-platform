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

$(window).trigger('hashchange');

/** This function checks if email is valid.
 * @param {String} email - email (input)
 */
function validateEmail(email) {
  var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

/**
 * login - This is a function to login a user in our database.
 */
function login() {
  var username = $('input#username').val();
  var password = $('input#password').val();

  var win = window.open('main.html', '_self');
  if (win) {
    win.focus();
  } else {
    alert('Please allow popups for this page.');
  }
}

/**
 * register - This is a function to register a user in our database.
 */
function register() {

  var username = $('input#newnickname').val();
  var mail = $('input#email').val();
  var password = $('input#newpassword').val();

  if (validateEmail(mail)) {
    console.log('register');

  }else {
    alert('Please enter a valid email!');
  }
}

$body.delegate('.login', 'click', function () {
    alert('clicked');
    login();
  });

$body.delegate('.register', 'click', function () {
    register();
  });
