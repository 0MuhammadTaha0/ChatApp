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

//Making contacts clickable and updating chat header
const contact = document.querySelectorAll('.contact')

for (let i = 0; i < contact.length; i++) {
    contact[i].addEventListener('click', function() {
      const chatHeader = document.querySelector('.profile-name')
      for (let j = 0; j < contact.length; j++) {
        contact[j].style.backgroundColor = 'white';
      }
      contact[i].style.backgroundColor = '#D3D3D3';
      let contactName = contact[i].innerHTML;
      chatHeader.innerHTML = contactName;
    });
}

//Implementing icons
const icons = document.querySelectorAll('.icon')

icons[2].onclick = function(){
  location.href='/friends/add';
};

icons[3].onclick = function(){
  location.href='/settings';
};

icons[4].onclick = function(){
  location.href='/logout';
};
