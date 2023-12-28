function sendMessage() {
    var userInput = document.getElementById("user-input").value;
    if (userInput !== "") {
        appendMessage("user", userInput);
        document.getElementById("user-input").value = "";
        getChatResponse(userInput);
    }
}

function appendMessage(sender, message) {
    var chatBox = document.getElementById("chat-box");
    var messageDiv = document.createElement("div");
    messageDiv.className = sender;
    messageDiv.innerHTML = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function getChatResponse(userInput) {
    fetch("/get", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "msg=" + userInput,
    })
    .then(response => response.text())
    .then(data => {
        appendMessage("bot", data);
    });
}
