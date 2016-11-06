var chat_was_minimized = false;
var missing_messages = 0;

(function() {

	$('#live-chat header').on('click', function() {

		$('.chat').slideToggle(300, 'swing');
		$('.chat-message-counter').fadeToggle(300, 'swing');

		if (chat_was_minimized) {
			chat_was_minimized = false;
			missing_messages = 0;
			$("span.chat-message-counter").remove();
		} else {
			chat_was_minimized = true;
		}

		console.log('Chat is minimized: ' + chat_was_minimized.toString());

		// scroll to the bottom
		// var messages = document.getElementById('log');
		// messages.scrollTop = messages.scrollHeight;
	});

	$('.chat-close').on('click', function(e) {

		e.preventDefault();
		$('#live-chat').fadeOut(300);

	});

}) ();


function scroll_to(div){
   if (div.scrollTop < div.scrollHeight - div.clientHeight)
        div.scrollTop += 10; // move down

}