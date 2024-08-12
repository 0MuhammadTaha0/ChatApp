const chatInputForm = document.querySelector('.chat-input')

const sendMessage = (e) => {
    e.preventDefault()
    const input = document.querySelector('.chat-input input');
    const message = input.value.trim();

    if (message) {
        const chatMessages = document.querySelector('.chat-messages');
        const newMessage = document.createElement('div');
        newMessage.classList.add('message');
        newMessage.textContent = message;
        chatMessages.appendChild(newMessage);
        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
    }
  }

chatInputForm.addEventListener('submit', sendMessage)
