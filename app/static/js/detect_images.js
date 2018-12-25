var interval = null;
var flagSide = false;
$(document).ready(function () {
    $('#modalChange').modal({
      backdrop: 'static',
      keyboard: false
    });
    $('#modalChange').modal('hide');
    interval = setInterval(check_images,1000)

    $('#modalChange').on('click', 'button.btn-primary', function (e) {
        $.ajax({
            type: 'GET',
            url: '/change-side-ajax',
            contentType: "application/json",
            dataType: 'json',
            data: [],
        }).done(function( msg ) {
            if( msg == 'success' ){
                $('#modalChange').modal('hide');
            }
        });
    });
});

function check_images(){
    $.ajax({
            type: 'GET',
            url: '/detect-package-ajax',
            contentType: "application/json",
            dataType: 'json',
            data: [],
    }).done(function( msg ) {
        if(msg == 'empty'){
            clearInterval(interval)
            window.location.assign("/package-create");
        }else if(msg == 'change side'){
            if(!flagSide){
                $('#modalChange').modal('toggle');
                flagSide = true;
            }

        }
        return true;
    });
    return false;
}