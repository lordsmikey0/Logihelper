const input = document.getElementById("req-input");
const button = document.getElementById("req-send");
const chat = document.getElementById("chat");
const awaitResponse = document.querySelector(".await_response");


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

        awaitResponse.style.opacity = "1";

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

        addMessage("", "assistant");
        const assistantMessage = chat.lastElementChild;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();

            if (done) {
                break;
            }

            assistantMessage.textContent += decoder.decode(
                value,
                { stream: true }
            );

            chat.scrollTop = chat.scrollHeight;
        }

        awaitResponse.style.opacity = "0";
    }
});