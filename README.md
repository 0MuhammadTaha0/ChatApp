# WhisperLine
### Video Demo:  <https://youtu.be/eM4AhE23EpY>
### Instructions:

1. You must have python installed in order to run this.
2. Download the repository or clone it by `git clone https://github.com/0MuhammadTaha0/WhisperLine`.
3. While in project directory, run `pip install -r requirements.txt`.
4. While in project directory, run `python app.py` or `python3 app.py`.

## Introduction
WhisperLine is a private texting and file sharing web application build with Flask. Text messages are sent in real-time by Flask-SocketIO. Sqlite database is used to store messages and Files, and it maintains the history. User display picture, online status, and name is shown while chatting. Friend management include sending friend requests, accepting or declining friend requests, and unfriending. In settings the user can change personal details like username, password, status (Show/Hide), and display picture.

## Files explanation

### app.py
`cs50` library is used for sqlite.

On connecting with socketio user `SID` is maintained with respect to session `user_id`.

On disconnecting user sid is deleted from `users` dictionary.

`users` dictionary is maintained, which contains all the SID's of flask-socketIO to send messages privately, and find if a user is online.

In `/register` route user input is validated and `dp` is checked. If user has inputed `dp` it is stored in the database. `user_id` which is primary key in `users` table, is maintained as session and user is redirected the the `/route`.

`/login` route was imlpemented by staff from [CS50x](https://cs50.harvard.edu/x/2024/).

`/fetchContacts` route returns contacts which are friends of the session user with all the messages and statuses of the friends.

`/fetchDp` route return `dp` from database based on `id` given by front end.

`/fetchFile` route returns binary data of File based on `id` given, and also checks if the client has access to that file.

`/completeFriendRequest` route checks if a friend request is valid and then if status is 1 from client is deletes the friend_requests table record and inserts into friendships table to make friendship.

`/friends/add` route after all the validation stores the request in database which can be fetched by the client later.

`/friends/requests` route returns the friend requests page of the session user.

`/friends` route returns friends page for user.

`/unfriend` route firsts checks if friendship exists and then deletes the friendships table record.

`/upload/message` route after validation of user form, inserts the received file into the database. If there is a File it includes the file id (fid) in the message structure. File BLOB is in file table and `fid` will be in the messages table as a foreign key.
If receiver is in `users` dictionary, then socketio emit is used to send message. At the end, message is stored in `messages` table. 

`/settings` route contains simple conditional logic to process which input fields user had entered, and updates them only. If user has entered nothing or faulty entries then server aborts the whole process and notifies the user.

### script.js

At the start of the file `io()` is used to start socketio.

`fileClickListener(fid, name, mimetype)` is an asynchronous function that fetches any file on based of file id (`fid`). On response, it converts the BLOB data to file and shows download pop up. This function is used in the event listener event of clicking files in chat.

`clickableContact(contactDiv, contact)` takes a div and adds an event listener on click. It makes the clicked contact the active contact. Assigns name and status to chat header to make it seem you are chatting the contact. Dp is also taken from contact dictionary like `contact["dp"]`. All the messages with the contact is loaded which are in `contact["messages"]`. If message contains `fid`, then it gets a file class. Here `fileClickListener` is used for the file. If the sender of the message is the user, then it gets an `own-message` css class for formatting. 

`appendMessage(message, contact)` just appends a given message to matching contact in global variable `contacts`.

`sendMessage` is an event listener function that activates when user sends a message i.e. a form. It takes the form inputs and also give values to the hidden form inputs like `receiverInput`, and `timestampInput`. Then it submits the form to `/upload/message` which responds with a file id, if a file was given. At the end, the message details are also inserted into the messages div so that user can see his own message sent. The message is also appended to `contacts` for user to see whenever that contact is clicked.

`fetchContacts()` fetches the contacts data from `/fetchContacts` and make divs for them. It also fetches the dp's and assigns all this data to the `contacts` global variable. At the end, it calls the `clickableContact` function.

`socket.on("send_message")` is for receiving messages in realtime. It calls the `appendMessage` function to append the message to `contacts` to see when clicked on the sender contact. It checks if that contact is already opened i.e. sender is the active contact. If message contains a file it gives it the file css and `fileClickListener`, else a normal message is created.

### .html files

`layout.html` is extended by all the .html files. `index.html` is the chatting page.

### dashboard-style.css

It contains all the css for all the .html files except `login.html`, `register.html`, and `settings.html`.

### form-style.css

It contins css for `login.html`, `register.html`, and `settings.html`.

### helpers.py 

It is imlpemented by staff from [CS50x](https://cs50.harvard.edu/x/2024/), and it does not give access to routes without login, and redirects user to `/login`

### tablecmds.sql

It contains all the `sqlite3` schema commands for making the tables.

### chatapp.db

It is the `sqlite3` database file.