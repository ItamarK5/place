const ConvertBoolToInteger = (val) => val ? 1 : 0;

const sock = io('/admin-io', {transports:['websocket']})
$(document).ready(() => {
    sock.connect()
    $('[data-toggle="tooltip"]').tooltip();
    $('tr').click(function() {
        let name = $(this).children('.name-col').text();
        if(name){
            window.location.href = `/edit/${$(this).children('.name-col').text()}`
        };
    });
    $('#place-button').click(function(){
        let board_state = $(this).attr('state');
        let button = this;
        Swal.fire({
            title: 'Are you sure?',
            text: `You want to ${board_state == "1" ? "pause" : "unpause"} the place`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
          }).then((result) => {
            if (result.value) {
              sock.emit('turn_app', board_state, (data) => {
                if(data.success){
                  console.log(data)
                  text = `The place is ${data.response == '0' ? 'paused' : 'unpause'}`;
                  $(button).attr('state', ConvertBoolToInteger(data.response));
                  $(button).children('h6').text(data.response == '0' ? 'Turn Place On' : 'Turn Place Off')
                }
                Swal.fire({
                    title: data.success ? `App is ${data.response == '0' ? 'paused' : 'unpause'}` : 'Error!',
                    icon:  data.success ? 'success' : 'error',
                    text: data.response
                });
              });
                /*
              $.ajax({
                  url:`/set-power-button`,
                  method:'POST',
                  contentType: 'application/json;charset=UTF-8',
                  data: state,
                // success message
                  success:function(data){
                    let text = data.text;
                    if(data.success){
                        text = `The place is ${data.text == '0' ? 'paused' : 'unpause'}`;
                        $(button).attr('state', data.text);
                        $(button).children('h6').text(data.text == '0' ? 'Turn Place On' : 'Turn Place Off')
                    }
                    Swal.fire({
                        title: data.success ? `App is ${data.text == '0' ? 'paused' : 'unpause'}` : 'Error!',
                        icon:  data.success ? 'success' : 'error',
                        text: text
                    });
                  },
                // error message
                  error: function(err) {
                      Swal.fire({
                        title: 'Error!',
                        icon:  'error',
                        html: err.responseText
                      })
                  }
              })
              */
            }
          })
    })
});