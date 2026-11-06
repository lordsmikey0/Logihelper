const form = document.getElementById("chat-form");
const input = document.getElementById("req-input");
const sendButton = document.getElementById("req-send");
const conversation = document.getElementById("conversation");
const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");
const status = document.getElementById("chat-status");

let sending = false;

function updateSendButton() {
    sendButton.disabled = sending || !input.value.trim();
}

function addMessage(role, label, text) {
    const message = document.createElement("article");
    message.classList.add("message", role);

    const author = document.createElement("header");
    author.className = "message-author";
    author.textContent = label;

    const content = document.createElement("div");
    content.className = "message-content";
    const body = document.createTextNode(text);
    content.append(body);
    message.append(author, content);
    chat.append(message);

    return body;
}

function isNearBottom() {
    const { scrollHeight, scrollTop, clientHeight } = conversation;
    return scrollHeight - scrollTop - clientHeight <= 40;
}

function scrollToBottom() {
    conversation.scrollTop = conversation.scrollHeight;
}

input.addEventListener("input", updateSendButton);
input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || event.shiftKey || event.isComposing || event.keyCode === 229) {
        return;
    }

    event.preventDefault();
    if (!event.repeat && !sendButton.disabled) {
        form.requestSubmit();
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const text = input.value.trim();
    if (!text || sending) {
        return;
    }

    sending = true;
    input.value = "";
    updateSendButton();
    input.focus();
    welcome.hidden = true;
    status.textContent = "Waiting for Logihelper…";
    addMessage("user", "You", text);
    scrollToBottom();

    let reader;
    let reply;

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });

        if (!response.ok || !response.body) {
            throw new Error("Response stream unavailable");
        }

        reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            const chunk = done ? decoder.decode() : decoder.decode(value, { stream: true });

            if (chunk) {
                const follow = isNearBottom();
                if (reply) {
                    reply.appendData(chunk);
                } else {
                    status.textContent = "Logihelper is responding…";
                    reply = addMessage("assistant", "Logihelper", chunk);
                }

                if (follow) {
                    scrollToBottom();
                }
            }

            if (done) {
                break;
            }
        }

        status.textContent = reply?.data.trim() ? "" : "Logihelper returned an empty response.";
    } catch {
        status.textContent = reply
            ? "The response was interrupted. You can send another message."
            : "Could not get a response. Check the connection and try again.";

        if (!reply && !input.value) {
            input.value = text;
        }
    } finally {
        reader?.releaseLock();
        sending = false;
        updateSendButton();
    }
});
