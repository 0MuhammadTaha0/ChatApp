from cs50 import SQL
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from flask_socketio import SocketIO

# Configure application and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///chatapp.db")

# SID's of all connected users
users = {}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/fetchContacts')
@login_required
def fetch():
        #Fetching the friends from database either current user was in sending or receiving side (Chat-GPT used to simplify query)
        contacts = db.execute(
        """     
            SELECT users.id, users.username, users.status  FROM friendships
            JOIN users ON users.id = CASE 
                WHEN friendships.friendid = ? THEN friendships.userid 
                ELSE friendships.friendid 
            END
            WHERE ? IN (friendships.userid, friendships.friendid);
        """
        ,session["user_id"], session["user_id"])

        for contact in contacts:
            if contact["status"] == 1:
                if contact["id"] in users:
                    contact["status"] = "online"
                else:
                    contact["status"] = "offline"
            else:
                contact["status"] = ""

        #Loading messages
        for contact in contacts:
            contact["messages"] = db.execute(
            """     
                SELECT users.username as sender, b.username as receiver, message, timestamp FROM messages
                JOIN users ON users.id = messages.sender
                JOIN users b ON b.id = messages.receiver
                WHERE
                (messages.sender = ? and messages.receiver = ?)
                OR
                (messages.sender = ? and messages.receiver = ?)
                ORDER BY messages.mid ASC;
            """
            ,session["user_id"], contact["id"], contact["id"], session["user_id"])
            
        if not contacts:
            return ('', 204)
        return jsonify(contacts)


@app.route('/')
@login_required
def index():
    if request.method == "GET":
        username = db.execute("SELECT username from users WHERE id = ?", session["user_id"])[0]["username"]
        return render_template("index.html", username=username)
    else:
        flash("TODO")
        return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            flash("Please Enter All Fields")
            return render_template("register.html")
            
        if not (request.form.get("password") == request.form.get("confirmation")):
            flash("Password fields do not match!")
            return render_template("register.html")

        username = db.execute("SELECT username FROM users WHERE username = ?",
                              request.form.get("username"))
        if username:
            flash("Username already exists!")
            return render_template("register.html")

        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, password)

        user_id = db.execute("SELECT id FROM users WHERE username = ?",
                             request.form.get("username"))[0]["id"]
        session["user_id"] = user_id
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username.")
            return render_template("login.html") 

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password.")
            return render_template("login.html")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("invalid username and/or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    """Log user out"""
    # Redirect user to login form
    return redirect("/login")

@app.route("/friends/add", methods=["GET", "POST"])
@login_required
def friends():
    if request.method == "GET":
        return render_template("add-friends.html")
    else:
        username = request.form.get("username")
        if not username:
            flash("Please Enter Username")
            return redirect("/friends/add")
        
        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # Ensure username exists
        if len(rows) != 1:
            flash("User does not exist!")
            return redirect("/friends/add")

        userid = db.execute("SELECT id from users where username = ?", username)[0]["id"]
        
        if userid == session["user_id"]:
            flash("You cannot be your own friend, duh!")
            return redirect("/friends/add")

        user = db.execute("SELECT * from friendships WHERE userid = ? and friendid = ?", session["user_id"], userid)
        friend = db.execute("SELECT * from friendships WHERE userid = ? and friendid = ?", userid, session["user_id"])

        if len(user) != 0 or len(friend) != 0:
            flash("Already Friends")
            return redirect("/friends/add")

        #Making friendship
        db.execute("INSERT into friendships (userid, friendid) VALUES (?, ?)", session["user_id"], userid)
        flash("Friend Added!")
        return redirect("/")
    
# SocketIO
# https://stackoverflow.com/questions/58468997/use-uid-to-emit-on-flask-socketio
@socketio.on("connect")
def on_connect():
    users[session["user_id"]] = request.sid

@socketio.on("disconnect")
def on_disconnect():
    del users[session["user_id"]]
    # Forget any user_id
    session.clear()

@socketio.on("send_message")
def on_send_message(message):
    message["sender"] = session["user_id"]
    if int(message["receiver"]) in users:
        socketio.emit("send_message", message, room=users[int(message["receiver"])])
    db.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)", session["user_id"], message["receiver"], message["message"], message["timestamp"])
    
if __name__ == "__main__":
    socketio.run(app, host='192.168.18.28', port=5000, debug=True)