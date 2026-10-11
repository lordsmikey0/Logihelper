const input = document.getElementById("req-input");
const button = document.getElementById("req-send");
const chat = document.getElementById("chat");

function addMessage(text, role) {
    const message = document.createElement("div");

    message.classList.add("message", role);
    message.textContent = text;

    chat.append(message);
    chat.scrollTop = chat.scrollHeight;
}


button.addEventListener("click", async function() {
    if (input.value.trim() !== "") {

        // юзер
        addMessage(input.value, "user");

        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: input.value
            })
        });
        input.value = "";

        const data = await response.json();

        // модель
        addMessage(data.reply, "assistant");
        console.log(data.reply);
    }
});