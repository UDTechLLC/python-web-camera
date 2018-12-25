var led_value = 10;
var title_amount = "Яркость - "
$(document).ready(function () {
    $('body').on('click', 'button.action_led', function (e) {
        send_led_ajax($(this).attr('data-url'), led_value)
    });

    $( "#slider-bright-led" ).slider({
      range: "max",
      min: 10,
      max: 100,
      step:10,
      value: $( "#amount-led" ).val(),
      slide: function( event, ui ) {
        $( "#amount-led" ).val( title_amount + ui.value );
        led_value = ui.value;
      },
      stop: function( event, ui ) {
        $( "#amount-led" ).val( title_amount + ui.value );
        led_value = ui.value;
        send_led_ajax($('.action_led.enable').attr('data-url'), led_value)
      }
    });
    $( "#amount-led" ).val( title_amount + $( "#slider-bright-led" ).slider( "value" ) );
});

function send_led_ajax(url, led){
    data = {'led': led};
    $.ajax({
            type: 'POST',
            url: url,
            contentType: "application/json",
            dataType: 'json',
            data: JSON.stringify(data),
    }).done(function( msg ) {
        console.log(msg)
    });
}