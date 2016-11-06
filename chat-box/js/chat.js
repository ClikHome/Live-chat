/**
 * Created by Eugene on 02.10.2016.
 */

function load_chat_template() {
    $('body').append()
}

var api_url = 'http://127.0.0.1:8000/api/v1.0/';
var socket_url = 'http://127.0.0.1:5000/echo';
var messages = document.getElementById('log');
var username = null;

$("#message_input").keyup(function(event){
    if(event.keyCode == 13) {
        var message = document.getElementById('message_input');

        if (window.username == null) {
            socket.send(JSON.stringify({
                'data_type': 'auth',
                'channel': window.channel,
                'username': message.value
            }));

        } else {
            var dateTime = new Date();
            socket.send(JSON.stringify({
                'body': message.value,
                'data_type': 'message'
            }));
        }

        $('#message_input').val('')
    }
});

function message_html(username, body, date) {
    var output_date = new Date(date + ' UTC');
    return '<div class="chat-message clearfix"><span class="chat-time">' + output_date.toLocaleTimeString() +
        '</span> <h5>' + username + '</h5><p>' + body + '</p></div><hr>'
}

function connect(url, channel) {
    var sock = new SockJS(url);

    sock.onopen = function(e) {
        // var now = new Date();
        //
        // sock.send(JSON.stringify({
        //     'data_type': 'get_history',
        //     'channel': channel,
        //     'timezone': now.getTime() / 1000
        // }));

        sock.send(JSON.stringify({
            'data_type': 'auth',
            'channel': channel
        }))
    };

    sock.onmessage =  function (event) {
        data = jQuery.parseJSON(event.data);

        if (data.data_type == 'auth_error') {
            throw data.data.message;

        } else if (data.data_type == 'auth_success') {
            window.username = data.username;
            $('#username').html(data.username + " (connected)");
            document.getElementById('message_input').setAttribute(
                    "placeholder", "Type your message…");
            console.log('Connected!')

        } else if (data.data_type == 'message') {
            $('#log').append(message_html(data.data.user, data.data.body, data.data.datetime));

            if (chat_was_minimized) {
                missing_messages += 1;
                var header = $('#header');

                if (header.children('span.chat-message-counter').length > 0) {
                    $('span.chat-message-counter').text = missing_messages;
                } else {
                    header.append('<span class="chat-message-counter">'
                            + missing_messages.toString() +  '</span>');
                }
            }

            if (username == data.data.user) {
                messages.scrollTop = messages.scrollHeight;
            }

        // } else if (data.data_type == 'history') {
        //     data.messages.forEach(function(item, i, arr) {
        //         $('#log').append(message_html(item.user, item.body, item.datetime));
        //     });
        //     messages.scrollTop = messages.scrollHeight;
        //
        // } else if (data.data_type == 'more_history') {
        //     if (data.messages.length > 0) {
        //         var current_position = messages.scrollHeight - messages.scrollTop;
        //         data.messages.reverse().forEach(function(item, i, arr) {
        //             $('#log').prepend(message_html(item.user, item.body, item.datetime));
        //         });
        //         messages.scrollTop = messages.scrollHeight - current_position;
        //
        //     }
        // } else if (data.data_type == 'set_cookie') {
        //     setCookie(data.key, data.value, data.path, data.expires);
        }
    };

    // sock.onclose = function (e) {
    //     $('#username').html(username + ' (disconnect)');
    // };

    return sock;
}


function get_auth_data() {
    var current_domain = 'site.com';
    var channel_uid = 'b2a829cd-e6f9-4b28-8b8b-5b51ed3bc4f8';


    $.get(
        api_url + 'channels/validation',
        {'domain': current_domain, 'channel_uid': channel_uid},
        function (data) {
             if (data.success == true) {
                 console.log('Channel is valid!');

                 window.socket = connect(socket_url, channel_uid);
                 window.channel = channel_uid;

                 console.log('Channel was connected!')
            }
        }
    );
}



messages.scrollTop = messages.scrollHeight;