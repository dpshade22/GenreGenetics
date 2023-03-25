document.getElementById('send-btn').addEventListener('click', function () {
    var message = document.getElementById('chat-input').value;
    if (message.trim() !== '') {
        // Add user message to the chat
        appendMessage('user', message);

        // Send message to the ChatGPT API and handle the response
        sendToChatGPTAPI(message).then(function (response) {
            // Add ChatGPT response to the chat
            appendMessage('chatgpt', response);
        });
    }
    document.getElementById('chat-input').value = '';
});

function appendMessage(sender, message) {
    var messageArea = document.querySelector('.message-area');
    var messageWrapper = document.createElement('div');
    messageWrapper.className = sender === 'user' ? 'user-message' : 'chatgpt-message';
    messageWrapper.innerText = message;
    messageArea.appendChild(messageWrapper);
    messageArea.scrollTop = messageArea.scrollHeight;
}

async function sendToChatGPTAPI(message) {
    // Implement your API call here
    // Return the response from ChatGPT
}
