(function () {

    var launcher = document.getElementById('chatbotLauncher');
    var panel = document.getElementById('chatbotPanel');
    var closeBtn = document.getElementById('chatbotClose');
    var messages = document.getElementById('chatbotMessages');
    var form = document.getElementById('chatbotForm');
    var input = document.getElementById('chatbotInput');

    if (!launcher || !panel) return;

    function openPanel() {
        panel.classList.add('open');
        input.focus();
    }

    function closePanel() {
        panel.classList.remove('open');
    }

    launcher.addEventListener('click', function () {
        if (panel.classList.contains('open')) {
            closePanel();
        } else {
            openPanel();
        }
    });

    closeBtn.addEventListener('click', closePanel);

    function scrollToBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(text, sender) {
        var bubble = document.createElement('div');
        bubble.className = 'chatbot-msg ' + (sender === 'user' ? 'chatbot-msg-user' : 'chatbot-msg-bot');
        bubble.textContent = text;
        messages.appendChild(bubble);
        scrollToBottom();
    }

    function showTyping() {
        var typing = document.createElement('div');
        typing.className = 'chatbot-typing';
        typing.id = 'chatbotTyping';
        typing.textContent = 'Assistant is typing...';
        messages.appendChild(typing);
        scrollToBottom();
    }

    function hideTyping() {
        var typing = document.getElementById('chatbotTyping');
        if (typing) typing.remove();
    }

    function sendMessage(text) {
        if (!text || !text.trim()) return;

        addMessage(text, 'user');
        showTyping();

        fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                hideTyping();
                addMessage(data.reply || "Sorry, something went wrong.", 'bot');
            })
            .catch(function () {
                hideTyping();
                addMessage("Sorry, I couldn't reach the server. Please try again.", 'bot');
            });
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var text = input.value;
        input.value = '';
        sendMessage(text);
    });

    // Suggestion chips
    messages.addEventListener('click', function (e) {
        var chip = e.target.closest('.chatbot-chip');
        if (chip) {
            sendMessage(chip.getAttribute('data-msg'));
        }
    });

})();
