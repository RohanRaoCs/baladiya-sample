/** Baladiya AI Chatbot — Floating Widget */
(function () {
    'use strict';

    const bubble = document.getElementById('baladiyaChatBubble');
    const chatWindow = document.getElementById('baladiyaChatWindow');
    const closeBtn = document.getElementById('baladiyaChatClose');
    const input = document.getElementById('baladiyaChatInput');
    const sendBtn = document.getElementById('baladiyaChatSend');
    const messagesEl = document.getElementById('baladiyaChatMessages');

    if (!bubble) return;

    let history = [];

    bubble.addEventListener('click', function () {
        chatWindow.style.display = 'flex';
        bubble.style.display = 'none';
        input.focus();
    });

    closeBtn.addEventListener('click', function () {
        chatWindow.style.display = 'none';
        bubble.style.display = 'flex';
    });

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = 'baladiya-chat-msg ' + sender;
        div.innerHTML = '<div class="baladiya-chat-msg-content">' + escapeHtml(text) + '</div>';
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addTyping() {
        const div = document.createElement('div');
        div.className = 'baladiya-chat-msg bot typing-indicator';
        div.id = 'typingIndicator';
        div.innerHTML = '<div class="baladiya-chat-msg-content"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function removeTyping() {
        const el = document.getElementById('typingIndicator');
        if (el) el.remove();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async function sendMessage() {
        const msg = input.value.trim();
        if (!msg) return;

        input.value = '';
        addMessage(msg, 'user');
        history.push({ role: 'user', content: msg });

        addTyping();
        sendBtn.disabled = true;

        try {
            const resp = await fetch('/baladiya/chatbot/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { message: msg, history: history.slice(-10) },
                }),
            });
            const data = await resp.json();
            removeTyping();

            const botReply = (data.result && data.result.response) || 'Sorry, something went wrong.';
            addMessage(botReply, 'bot');
            history.push({ role: 'assistant', content: botReply });
        } catch (e) {
            removeTyping();
            addMessage('Unable to reach the AI assistant. Please try again.', 'bot');
        }

        sendBtn.disabled = false;
        input.focus();
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') sendMessage();
    });
})();
