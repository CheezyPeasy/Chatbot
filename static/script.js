let lastQuestion = "";

// Append messages to chat
function appendMessage(sender, message) {
    const chatBox = document.getElementById("chat-box");

    // Detect if user was at bottom
    const wasAtBottom =
        chatBox.scrollTop + chatBox.clientHeight >= chatBox.scrollHeight - 10;

    // Format message
    let formatted = message
        .replace(/\n/g, "<br>")
        .replace(/•/g, "<br>•")
        .replace(/^- /gm, "<br>- ");

    const div = document.createElement("div");
    div.className = sender === "You" ? "message-user" : "message-bot";
    div.innerHTML = formatted;

    chatBox.style.scrollBehavior = "auto";
    chatBox.appendChild(div);

    // ⛔ DO NOT force scroll for bot messages
    if (sender === "You" && wasAtBottom) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    chatBox.style.scrollBehavior = "smooth";
}

// Show bot typing indicator
function showTyping() {
    const chatBox = document.getElementById("chat-box");
    const typingDiv = document.createElement("div");
    typingDiv.id = "typing-indicator";
    typingDiv.className = "message-bot";
    typingDiv.textContent = "Bot is typing...";
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Remove typing indicator
function removeTyping() {
    const typingDiv = document.getElementById("typing-indicator");
    if (typingDiv) typingDiv.remove();
}

// Send message to backend
async function sendMessage() {
    const input = document.getElementById("user-input");
    let message = input.value.trim();
    if (message === "") return;

    appendMessage("You", message);
    input.value = "";

    // Show bot typing
    showTyping();

    // Simulate delay before bot responds
    setTimeout(async () => {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message})
        });

        const data = await res.json();

        removeTyping(); // remove typing indicator
        appendMessage("Bot", data.response);

        if (data.learn === true) {
            lastQuestion = message;
            askToLearn();
        }
    }, 1000); // 1000ms = 1 second delay
}

// Ask user to teach bot
function askToLearn() {
    const answer = prompt("Please enter the correct answer:");
    if (answer) saveLearning(answer);
}

// Send learned answer to backend
async function saveLearning(answer) {
    const res = await fetch("/learn", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: lastQuestion, answer})
    });

    const data = await res.json();
    appendMessage("Bot", data.response);
}

// Enter key sends message
let input = document.getElementById("user-input");
input.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});
