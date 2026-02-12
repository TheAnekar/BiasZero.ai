async function send() {
    const input = document.getElementById("input");
    const text = input.value.trim();
    if (!text) return;

    addMsg(text, "user");
    input.value = "";

    const typing = addMsg("Typing...", "ai");

    const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: text})
    });

    const data = await res.json();
    typing.remove();
    addMsg(data.reply, "ai");
}

function addMsg(text, cls) {
    const div = document.createElement("div");
    div.className = `msg ${cls}`;
    div.textContent = text;
    document.getElementById("chat-area").appendChild(div);
    div.scrollIntoView();
    return div;
}