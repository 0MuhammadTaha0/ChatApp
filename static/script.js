// Initializing FlaskSocketIO
const socket = io();
let contacts = {}
const chatInputForm = document.querySelector('.chat-input')

async function fileClickListener(fid, name, mimetype) {
    let response = await fetch(`/fetchFile?fid=${fid}`);
    if (response.status == 204) {
        alert("You do not have rights to the file or it does not exist!");
    } else {
        // BLOB to FILE
        let data = await response.blob();
        const myFile = new File([data], name, {
            type: mimetype
        });

        // Download Pop Up
        var url = URL.createObjectURL(myFile);
        const link = document.createElement('a')

        link.href = url
        link.download = name
        document.body.appendChild(link)
        link.click()

        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
    }
}

//Making contacts clickable and updating chat header
function clickableContact(contactDiv, contact) {

    contactDiv.addEventListener('click', function() {
        // When clicked make it the active contact
        const chatHeader = document.querySelectorAll('.profile-content div')
        const activeContact = document.querySelector('.activeContact')
        if (activeContact) {
            activeContact.classList.remove('activeContact')
        }
        contactDiv.classList.add('activeContact');
        let contactName = contact["username"];
        let contactStatus = contact["status"];

        // Contact Header
        chatHeader[0].innerHTML = contactName;
        chatHeader[1].innerHTML = contactStatus;

        const chatMessagesContainer = document.querySelector('.chat-messages');
        chatMessagesContainer.innerHTML = '';

        //Changing Default Dp
        const dpContainer = document.querySelector('#profile-icon');
        dpContainer.src = contact["dp"];

        // Load messages
        if ('messages' in contact) {
            const messages = contact["messages"];

            // Append the messages
            messages.forEach(function(message) {
                const messageDiv = document.createElement('div');
                // If message contains a File
                if (message['fid']) {

                    const fileDiv = document.createElement("div");
                    fileDiv.innerHTML = message["name"];
                    fileDiv.classList.add('message-file');
                    fileDiv.classList.add("message-text")

                    messageDiv.appendChild(fileDiv);

                    fileDiv.addEventListener('click', function() {
                        fileClickListener(message['fid'], message['name'], message['mimetype']);
                    });

                }

                if (message["receiver"] === contactName) {
                    messageDiv.classList.add('own-message');
                }


                messageDiv.classList.add('message');

                const messageText = document.createElement("div");
                messageText.innerHTML = message["message"];
                messageText.classList.add('message-text');

                const messageTimestamp = document.createElement("div");
                messageTimestamp.innerHTML = message["timestamp"];
                messageTimestamp.classList.add('message-timestamp');

                messageDiv.appendChild(messageText);
                messageDiv.appendChild(messageTimestamp);
                chatMessagesContainer.appendChild(messageDiv);
            });

            // Scroll to the bottom of the chat
            chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        }
    });
}



function appendMessage(message, contact) {
    for (let i = 0; i < contacts.length; i++) {
        if (contacts[i]["id"] == contact) {
            contacts[i]["messages"].push(message)
        }
    }
}

// e.preventDefault() syntax help from ChatGPT
const sendMessage = (e) => {
    e.preventDefault()
    // Checking if the user has an active contact
    const activeContact = document.querySelector('.activeContact')
    if (!activeContact) {
        return
    }

    // Fetching message data elements
    const fileInput = document.querySelector('#file-input')
    const textInput = document.querySelector('#message-input');
    const receiverInput = document.querySelector('#receiver-input');
    const timestampInput = document.querySelector('#timestamp-input');
    const textInputValue = textInput.value.trim();

    textInput.value = textInputValue;
    // Assigning to the 2 hidden inputs
    receiverInput.value = activeContact.id;
    timestampInput.value = new Date().toLocaleString();

    // https://stackoverflow.com/questions/74195369/post-request-form-data-without-reloading-page-flask-fetch
    const formData = new FormData(e.target);

    fetch("/upload/message", {
            'method': 'POST',
            'body': formData
        })
        .then(response => response.json()
            .then(data => {

                const chatMessages = document.querySelector('.chat-messages');
                const newMessage = document.createElement('div');
                let message = {};

                message = {
                    message: textInputValue,
                    receiver: activeContact.id,
                    timestamp: timestampInput.value
                }

                if (fileInput) {
                    let filename = "";
                    // If File is given
                    if (fileInput.files.length != 0) {
                        filename = fileInput.files[0].name;
                        message["fid"] = data["fid"];
                        message["name"] = filename;
                        message["mimetype"] = fileInput.files[0].mimetype;

                        const fileDiv = document.createElement("div");
                        fileDiv.innerHTML = filename;
                        fileDiv.classList.add('message-file');

                        newMessage.appendChild(fileDiv);

                        // implement Click to Download
                        fileDiv.addEventListener('click', function() {
                            fileClickListener(message['fid'], message['name'], message['mimetype']);
                        });
                    }
                }

                // Appending in messages div for user to see his sent message

                newMessage.classList.add('own-message');
                newMessage.classList.add('message');

                const messageText = document.createElement("div");
                messageText.innerHTML = message["message"];
                messageText.classList.add('message-text');

                const messageTimestamp = document.createElement("div");
                messageTimestamp.innerHTML = message["timestamp"];
                messageTimestamp.classList.add('message-timestamp');

                newMessage.appendChild(messageText);
                newMessage.appendChild(messageTimestamp);
                chatMessages.appendChild(newMessage);

                chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom

                // Appending in messages data for user to see later
                appendMessage(message, activeContact.id);

                // Clearing inputs
                fileInput.value = "";
                textInput.value = "";
                receiverInput.value = "";
                timestampInput.value = "";
            }));
}

chatInputForm.addEventListener('submit', sendMessage)

//Implementing icons
const icons = document.querySelectorAll('.icon')

icons[0].onclick = function() {
    location.href = '/friends/add';
};

icons[1].onclick = function() {
    location.href = '/settings';
};

icons[2].onclick = function() {
    location.href = '/logout';
};

async function fetchContacts() {
    const contactSectionContainer = document.querySelector('.contacts-section');
    let response = await fetch('/fetchContacts');

    if (response.status == 204) {
        // If there are no friends ;(
        const contactDiv = document.createElement('div');
        contactDiv.classList.add('contact');
        contactDiv.innerHTML = `<a href="/friends/add">Click</a> to add friends!`;
        contactSectionContainer.appendChild(contactDiv);
    } else {
        contacts = await response.json();

        for (let i = 0; i < contacts.length; i++) {
            // Making contact div for friend
            const contactDiv = document.createElement('div');
            contactDiv.id = contacts[i]["id"];
            contactDiv.classList.add('contact');
            contactDiv.textContent = contacts[i]["username"];
            contactSectionContainer.appendChild(contactDiv);

            // Fetching Display Picture
            response = await fetch(`/fetchDp?id=${contacts[i]["id"]}`);
            if (response.status == 204) {
                // Default picture in case of no dp
                contacts[i]["dp"] = "/static/images/vecteezy_default-profile-account-unknown-icon-black-silhouette_20765399.jpg";
            } else {
                let data = await response.blob();
                const myFile = new File([data], contacts[i]["id"]);
                var url = URL.createObjectURL(myFile);
                contacts[i]["dp"] = url;
            }

            clickableContact(contactDiv, contacts[i]);
        }
    }
}

fetchContacts();

socket.on("send_message", function(message) {
    // Append messages to contacts data
    appendMessage(message, message["sender"])
    const activeContact = document.querySelector('.activeContact')
    // If you have tha contact opened
    if (activeContact.id == message["sender"]) {
        // If message is a file
        if (message["fid"]) {
            const chatMessagesContainer = document.querySelector('.chat-messages');
            const newFile = document.createElement('div');
            newFile.classList.add('message');

            const fileDiv = document.createElement("div");
            fileDiv.innerHTML = message["name"];
            fileDiv.classList.add('message-file');
            fileDiv.classList.add("message-text")

            fileDiv.addEventListener('click', function() {
                fileClickListener(message['fid'], message['name'], message['mimetype']);
            });

            const messageText = document.createElement("div");
            messageText.innerHTML = message["message"];
            messageText.classList.add('message-text');

            const messageTimestamp = document.createElement("div");
            messageTimestamp.innerHTML = message["timestamp"];
            messageTimestamp.classList.add('message-timestamp');

            newFile.appendChild(fileDiv);
            newFile.appendChild(messageText);
            newFile.appendChild(messageTimestamp);

            chatMessagesContainer.appendChild(newFile);
            chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        } else {
            const chatMessagesContainer = document.querySelector('.chat-messages');
            const newMessage = document.createElement('div');
            newMessage.classList.add('message');
            newMessage.textContent = message['message'];
            chatMessagesContainer.appendChild(newMessage);
            chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        }
    }
});
