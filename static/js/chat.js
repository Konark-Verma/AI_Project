const chatBody = document.getElementById('chat-body');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message');

function appendMessage(text, sender) {
    const messageCard = document.createElement('div');
    messageCard.className = `chat-message ${sender}`;
    messageCard.innerHTML = `<p>${text.replace(/\n/g, '<br>')}</p>`;
    chatBody.appendChild(messageCard);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function appendActionButton(text, trip) {
    const buttonWrapper = document.createElement('div');
    buttonWrapper.className = 'chat-action-wrapper';
    buttonWrapper.innerHTML = `<button class="chat-action-button">${text}</button>`;
    buttonWrapper.querySelector('button').addEventListener('click', () => {
        localStorage.setItem('source', trip.source);
        localStorage.setItem('destination', trip.destination);
        localStorage.setItem('travelers', trip.travelers);
        localStorage.setItem('budget', trip.budget);
        localStorage.setItem('days', trip.days);
        localStorage.setItem('travelType', trip.travel_type || 'city');
        window.location.href = '/result';
    });
    chatBody.appendChild(buttonWrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
}

async function sendChatMessage(message) {
    const response = await fetch('/chat_api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    });
    return response.json();
}

chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }

    appendMessage(message, 'user');
    messageInput.value = '';
    messageInput.focus();

    const data = await sendChatMessage(message);
    appendMessage(data.reply, 'bot');

    if (data.plan && data.trip) {
        appendActionButton('View full plan', data.trip);
    }
});
