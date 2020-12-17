$(document).ready(function(){

});

function reset_password(){
    let newPw = $("input#new_password").val();
    let newPwConfirm = $("input#new_password_confirm").val();
    const urlParams = new URLSearchParams(window.location.search);
    const phrase = urlParams.get("phrase");

    if(newPw != newPwConfirm){
        alert("entered passwords do not match");
    }
    else{
        $.ajax({
            type: "POST",
            url: "/forgot_password?phrase=" + phrase + "&new_password=" + newPw,
            success: function(data){
                alert("Password succesfully changed. You may proceed to login with your new credentials");
                setTimeout(function() {
                    window.location.href = '/main';
                }, 1000);
            },
            error: function(xhr,status, error){
                console.log(error);
                console.log(status);
                errorObj = JSON.parse(xhr.responseText);
                if(errorObj.reason == "phrase_not_valid"){
                    alert("Your Link is no longer valid, please acquire a new one.");
                }
                else{
                    alert('error while resetting password');
                }
            }

        })
    }
}

