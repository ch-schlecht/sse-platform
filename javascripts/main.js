var url = "localhost:8888"
$(function (){

    var $modules = $('#modules');

    $.ajax({
        type: 'GET',
        url: this.url + "/modules/list_available",
        dataType: 'json',
        success: function(modules) {
            $.each(modules, function(i, module){
                $modules.append('<li> name: '+ module + '</li>');
            });
        }
    });

});