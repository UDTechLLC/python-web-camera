var interval = null;
$(document).ready(function () {
    interval = setInterval(get_train_status,1000)
});

function get_train_status(){
    $.ajax({
            type: 'GET',
            url: '/train-status',
            contentType: "application/json",
            dataType: 'json',
            data: [],
    }).done(function( msg ) {
        if(msg == 'empty'){
            clearInterval(interval)
            //window.location.assign("/package-create");
        }else{
            $('.log_area .status').text(msg.status);
            $('h2.title-operation span').text(msg.operation);
            percents = parseInt(msg.step) / ( parseInt(msg.amount) / 100);
            $('.log_area .progress-bar').css('width', percents + '%');
        }
        return true;
    });
    return false;
}