function change_password(){
    let oldPw = $("input#old_password").val();
    let newPw = $("input#new_password").val();
    let newPwConfirm = $("input#new_password_confirm").val();

    if(newPw == newPwConfirm) {
        $.ajax({
            type: "POST",
            url: "/password/change?old_password=" + oldPw + "&new_password=" + newPw,
            success: function (data) {
                alert("Password succesfully changed. You may proceed to login with your new credentials");
                setTimeout(function () {
                    window.location.href = '/main';
                }, 500);
            },
            error: function (xhr, status, error) {
                console.log(error);
                console.log(status);
                errorObj = JSON.parse(xhr.responseText);
                console.log(errorObj);
                if (errorObj == "old_password_not_valid") {
                    alert("The old password was not valid, Please try again");
                } else {
                    alert("an uexpected error occured.");
                }
            }
        });
    }
    else{
        alert("confirmation does not match the new password");
    }
}