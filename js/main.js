const form = document.getElementById("chat-form");
const input = document.getElementById("req-input");
const sendButton = document.getElementById("req-send");
const conversation = document.getElementById("conversation");
const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");
const status = document.getElementById("chat-status");
const chatHeading = document.getElementById("chat-heading");
const chatList = document.getElementById("chat-list");
const chatItemTemplate = document.getElementById("chat-item-template");
const newChat = document.getElementById("new-chat");
const emptyHistory = document.getElementById("empty-history");
const storageStatus = document.getElementById("storage-status");
const historyToggle = document.getElementById("history-toggle");
const dialog = document.getElementById("chat-dialog");
const dialogForm = document.getElementById("dialog-form");
const dialogHeading = document.getElementById("dialog-heading");
const renameField = document.getElementById("rename-field");
const chatName = document.getElementById("chat-name");
const deleteConfirmation = document.getElementById("delete-confirmation");
const cancelDialog = document.getElementById("cancel-dialog");
const confirmDialog = document.getElementById("confirm-dialog");

const storageKey = "logihelper.chats";
const chats = loadChats();
const drafts = new Map();
const notices = new WeakMap();
let selected = null;
let pending = null;
let menuItem = null;
let dialogThread = null;

function loadChats() {
    try {
        const saved = JSON.parse(localStorage.getItem(storageKey) ?? "[]");
        return saved.filter((thread) =>
            typeof thread?.title === "string" &&
            Array.isArray(thread.messages) &&
            thread.messages.every((message) =>
                (message?.role === "user" || message?.role === "assistant") &&
                typeof message.text === "string"
            )
        );
    } catch {
        storageStatus.textContent = "Could not load saved chats.";
        return [];
    }
}

function saveChats() {
    try {
        localStorage.setItem(storageKey, JSON.stringify(chats));
        storageStatus.textContent = "";
    } catch {
        storageStatus.textContent = "Could not save chats to this browser.";
    }
}

function titleFrom(text) {
    const characters = Array.from(text.replace(/\s+/g, " "));
    return characters.length > 32 ? characters.slice(0, 32).join("").trimEnd() + "…" : characters.join("");
}

function closeChatMenu() {
    if (menuItem) {
        menuItem.querySelector(".chat-menu-toggle").setAttribute("aria-expanded", "false");
        menuItem.querySelector(".chat-menu").hidden = true;
        menuItem = null;
    }
}

function positionChatMenu(toggle, menu) {
    const edge = 8;
    const gap = 4;
    const anchor = toggle.getBoundingClientRect();
    const { clientWidth, clientHeight } = document.documentElement;
    const { width, height } = menu.getBoundingClientRect();
    const below = clientHeight - anchor.bottom;
    const above = anchor.top;
    const top = below < height + gap + edge && above > below
        ? anchor.top - height - gap
        : anchor.bottom + gap;

    menu.style.left = `${Math.max(edge, Math.min(anchor.right - width, clientWidth - width - edge))}px`;
    menu.style.top = `${Math.max(edge, Math.min(top, clientHeight - height - edge))}px`;
}

function renderHistory(focusThread) {
    closeChatMenu();
    chatList.replaceChildren();
    emptyHistory.hidden = chats.length > 0;

    const orderedChats = [...chats].sort((a, b) => Number(b.pinned === true) - Number(a.pinned === true));
    for (const thread of orderedChats) {
        const item = chatItemTemplate.content.firstElementChild.cloneNode(true);
        const choice = item.querySelector(".chat-choice");
        const toggle = item.querySelector(".chat-menu-toggle");
        const menu = item.querySelector(".chat-menu");
        const pin = menu.querySelector('[data-action="pin"]');
        item.querySelector(".chat-title").textContent = thread.title;
        choice.title = thread.title;
        toggle.setAttribute("aria-label", `Actions for ${thread.title}`);
        if (thread.pinned === true) {
            item.classList.add("is-pinned");
            choice.setAttribute("aria-label", `${thread.title} (pinned)`);
            pin.textContent = "Unpin";
        }
        if (thread === selected) {
            choice.setAttribute("aria-current", "true");
        }
        choice.addEventListener("click", () => {
            selectChat(thread);
            historyToggle.setAttribute("aria-expanded", "false");
            chatHeading.focus();
        });

        toggle.addEventListener("click", () => {
            const wasOpen = menuItem === item;
            closeChatMenu();
            if (!wasOpen) {
                menuItem = item;
                toggle.setAttribute("aria-expanded", "true");
                menu.hidden = false;
                positionChatMenu(toggle, menu);
            }
        });

        menu.addEventListener("click", (event) => {
            const action = event.target.dataset.action;
            if (!action) {
                return;
            }
            closeChatMenu();
            toggle.focus();

            if (action === "pin") {
                thread.pinned = thread.pinned !== true;
                saveChats();
                renderHistory(thread);
            } else {
                openChatDialog(thread, action === "rename");
            }
        });

        chatList.append(item);
        if (thread === focusThread) {
            toggle.focus();
        }
    }
}

function updateSendButton() {
    sendButton.disabled = Boolean(pending) || !input.value.trim();
}

function updateStatus() {
    if (pending && pending.thread === selected) {
        status.textContent = pending.reply ? "Logihelper is responding…" : "Waiting for Logihelper…";
    } else {
        status.textContent = notices.get(selected) ?? "";
    }
}

function addMessage({ role, text }) {
    const message = document.createElement("article");
    message.classList.add("message", role);

    const author = document.createElement("header");
    author.className = "message-author";
    author.textContent = role === "user" ? "You" : "Logihelper";

    const content = document.createElement("div");
    content.className = "message-content";
    const body = document.createTextNode(text);
    content.append(body);
    message.append(author, content);
    chat.append(message);

    return body;
}

function selectChat(thread) {
    if (selected !== thread) {
        drafts.set(selected, input.value);
        selected = thread;
        input.value = drafts.get(thread) ?? "";
    }

    chatHeading.textContent = thread?.title ?? "Chat";
    welcome.hidden = Boolean(thread);
    chat.replaceChildren();

    if (pending) {
        pending.body = null;
    }
    for (const message of thread?.messages ?? []) {
        const body = addMessage(message);
        if (pending?.reply === message) {
            pending.body = body;
        }
    }

    renderHistory();
    updateStatus();
    updateSendButton();
    scrollToBottom();
}

function isNearBottom() {
    const { scrollHeight, scrollTop, clientHeight } = conversation;
    return scrollHeight - scrollTop - clientHeight <= 40;
}

function scrollToBottom() {
    conversation.scrollTop = conversation.scrollHeight;
}

function openChatDialog(thread, rename) {
    dialogThread = thread;
    dialogHeading.textContent = rename ? "Rename chat" : "Delete chat?";
    renameField.hidden = !rename;
    chatName.disabled = !rename;
    chatName.setCustomValidity("");
    chatName.value = rename ? thread.title : "";
    deleteConfirmation.hidden = rename;
    deleteConfirmation.textContent = rename ? "" : `Delete “${thread.title}” and its messages?`;
    confirmDialog.textContent = rename ? "Save" : "Delete";
    dialog.showModal();
    if (rename) {
        chatName.select();
    } else {
        cancelDialog.focus();
    }
}

historyToggle.addEventListener("click", () => {
    const expanded = historyToggle.getAttribute("aria-expanded") === "true";
    historyToggle.setAttribute("aria-expanded", String(!expanded));
});

window.addEventListener("resize", closeChatMenu);
chatList.closest(".sidebar").addEventListener("scroll", closeChatMenu);

document.addEventListener("click", (event) => {
    if (menuItem && !menuItem.contains(event.target)) {
        closeChatMenu();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menuItem) {
        menuItem.querySelector(".chat-menu-toggle").focus();
        closeChatMenu();
        event.preventDefault();
    }
});

newChat.addEventListener("click", () => {
    selectChat(null);
    input.value = "";
    updateSendButton();
    historyToggle.setAttribute("aria-expanded", "false");
    input.focus();
});

cancelDialog.addEventListener("click", () => dialog.close());
chatName.addEventListener("input", () => chatName.setCustomValidity(""));

dialogForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const thread = dialogThread;

    if (!chatName.disabled) {
        const title = chatName.value.trim();
        if (!title) {
            chatName.setCustomValidity("Enter a chat name.");
            chatName.reportValidity();
            return;
        }
        thread.title = title;
        if (thread === selected) {
            chatHeading.textContent = title;
        }
        dialog.close();
        renderHistory(thread);
    } else {
        if (pending?.thread === thread) {
            pending.controller.abort();
        }
        chats.splice(chats.indexOf(thread), 1);
        dialog.close();
        if (thread === selected) {
            selectChat(null);
        } else {
            renderHistory();
        }
        drafts.delete(thread);
        newChat.focus();
    }

    saveChats();
});

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
    if (!text || pending) {
        return;
    }

    const thread = selected ?? { title: titleFrom(text), messages: [] };
    const request = { thread, controller: new AbortController(), reply: null, body: null };
    const message = { role: "user", text };
    pending = request;
    notices.delete(thread);
    thread.messages.push(message);
    input.value = "";

    if (selected) {
        addMessage(message);
    } else {
        chats.unshift(thread);
        selectChat(thread);
    }

    saveChats();
    updateStatus();
    updateSendButton();
    input.focus();
    scrollToBottom();

    let reader;
    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
            signal: request.controller.signal,
        });

        if (!response.ok || !response.body) {
            throw new Error("Response stream unavailable");
        }

        reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { value, done } = await reader.read();
            const chunk = done ? decoder.decode() : decoder.decode(value, { stream: true });

            if (chunk && !request.controller.signal.aborted) {
                if (!request.reply) {
                    request.reply = { role: "assistant", text: "" };
                    thread.messages.push(request.reply);
                    updateStatus();
                }
                request.reply.text += chunk;

                if (thread === selected) {
                    const follow = isNearBottom();
                    if (request.body) {
                        request.body.appendData(chunk);
                    } else {
                        request.body = addMessage(request.reply);
                    }

                    if (follow) {
                        scrollToBottom();
                    }
                }
            }

            if (done) {
                break;
            }
        }

        if (!request.reply?.text.trim()) {
            notices.set(thread, "Logihelper returned an empty response.");
        }
    } catch {
        if (!request.controller.signal.aborted) {
            notices.set(thread, request.reply
                ? "The response was interrupted. You can send another message."
                : "Could not get a response. Check the connection and try again.");

            if (!request.reply) {
                if (thread === selected && !input.value) {
                    input.value = text;
                } else if (thread !== selected && !drafts.get(thread)) {
                    drafts.set(thread, text);
                }
            }
        }
    } finally {
        reader?.releaseLock();
        pending = null;
        if (!request.controller.signal.aborted) {
            saveChats();
        }
        updateStatus();
        updateSendButton();
    }
});

renderHistory();
