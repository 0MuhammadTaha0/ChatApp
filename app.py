from cs50 import SQL
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from flask_socketio import SocketIO
from helpers import login_required
from werkzeug.security import check_password_hash, generate_password_hash


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
            SELECT users.id, users.username, users.status FROM friendships
            JOIN users ON users.id = CASE 
                WHEN friendships.friendid = ? THEN friendships.userid 
                ELSE friendships.friendid 
            END
            WHERE ? IN (friendships.userid, friendships.friendid);
        """
        ,session["user_id"], session["user_id"])

        if not contacts:
            return ('', 204)

        for contact in contacts:
            if contact["status"] == 1:
                if contact["id"] in users:
                    contact["status"] = "online"
                else:
                    contact["status"] = "offline"
            else:
                contact["status"] = ""

            #Loading messages
            contact["messages"] = db.execute(
            """     
                SELECT users.username as sender, b.username as receiver, message, timestamp, File.fid, File.name, File.mimetype FROM messages
                JOIN users ON users.id = messages.sender
                JOIN users b ON b.id = messages.receiver
                FULL OUTER JOIN File ON File.fid = messages.fid
                WHERE
                (messages.sender = ? and messages.receiver = ?)
                OR
                (messages.sender = ? and messages.receiver = ?)
                ORDER BY messages.mid ASC;
            """
            ,session["user_id"], contact["id"], contact["id"], session["user_id"])
    
        return jsonify(contacts), 200


@app.route('/fetchDp')
@login_required
def fetchDp():
    id = request.args.get('id')
    id = int(id)
    file = db.execute("SELECT dp FROM users where id = ?", id)
    if not file:
        return "", 204
    file = file[0]["dp"]
    if not file:
        return "", 204
    # Continue From Here
    return file, 200


@app.route('/fetchFile')
@login_required
def fetchFile():
    fid = request.args.get('fid')
    fid = int(fid)
    
    check = db.execute(
            """     
                SELECT fid FROM messages
                WHERE
                (messages.sender = ? or messages.receiver = ?)
                AND 
                fid = ?

            """
            ,session["user_id"], session["user_id"], fid)
    
    if len(check) != 1:
        return "", 204

    file = db.execute("SELECT file FROM File where fid = ?", fid)
    if not file:
        return "", 204
    file = file[0]["file"]
    if not file:
        return "", 204
    # Continue From Here
    return file, 200


@app.route('/completeFriendRequest')
@login_required
def completeFriendRequest():
    frid = request.args.get('frid')
    status = request.args.get('status')
    userid = request.args.get('userid')
    frid = int(frid)
    status = int(status)
    userid = int(userid)

    check = db.execute(
        """     
            SELECT frid FROM friend_requests
            WHERE
            friend_requests.friendid = ?
            AND 
            frid = ?

        """
        ,session["user_id"], frid)
    
    if len(check) != 1:
        return "", 204
    else:
        if status == 1:
            db.execute("INSERT INTO friendships (userid, friendid) VALUES (?, ?)", userid, session["user_id"])
            db.execute("DELETE FROM friend_requests WHERE frid = ?", frid)
            return "", 200
        else:
            db.execute("DELETE FROM friend_requests WHERE frid = ?", frid)
            return "", 200
    


@app.route('/')
@login_required
def index():
    username = db.execute("SELECT username from users WHERE id = ?", session["user_id"])[0]
    return render_template("index.html", username=username)


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
        dp = request.files['file']
        mimetype = None
        if dp:
            mimetype = dp.mimetype
            if mimetype not in ["image/jpeg", "image/png", "image/jpg"]:
                dp = None
            else:
                dp = dp.read()
        else:
            dp = None

        
        db.execute("INSERT INTO users (username, hash, dp) VALUES (?, ?, ?)", username, password, dp)

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
def add_friends():
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

        # Checking if already friends
        user = db.execute("SELECT * from friendships WHERE userid = ? and friendid = ?", session["user_id"], userid)
        friend = db.execute("SELECT * from friendships WHERE userid = ? and friendid = ?", userid, session["user_id"])

        if len(user) != 0 or len(friend) != 0:
            flash("Already Friends")
            return redirect("/friends/add")
        
        # Checking if already there is a friend request
        user = db.execute("SELECT * from friend_requests WHERE userid = ? and friendid = ?", session["user_id"], userid)

        if len(user) != 0:
            flash("Friend request already exists!")
            return redirect("/friends/add")

        #Making friendship
        db.execute("INSERT into friend_requests (userid, friendid) VALUES (?, ?)", session["user_id"], userid)

        flash("Friend Request Sent!")
        return redirect("/friends/add")
    
@app.route("/friends/requests")
@login_required
def friend_requests():

    friend_requests = db.execute(
        """     
            SELECT friend_requests.frid, users.id, users.username FROM friend_requests
            JOIN users ON users.id = friend_requests.userid 
            WHERE friend_requests.friendid = (?);
        """
        , session["user_id"])

    return render_template("friend-requests.html", friend_requests=friend_requests)


@app.route("/friends")
@login_required
def get_friends():

    friends = db.execute(
        """     
            SELECT friendships.fsid, users.id, users.username FROM friendships
            JOIN users ON users.id = CASE 
                WHEN friendships.friendid = ? THEN friendships.userid 
                ELSE friendships.friendid 
            END
            WHERE ? IN (friendships.userid, friendships.friendid);
        """
        ,session["user_id"], session["user_id"])

    return render_template("manage-friends.html", friends=friends)


@app.route("/unfriend")
@login_required
def unfriend():
    fsid = request.args.get('fsid')
    fsid = int(fsid)

    check = db.execute(
        """     
            SELECT fsid FROM friendships
            WHERE
            (friendships.userid = ? or friendships.friendid = ?)
            AND 
            fsid = ?

        """
        ,session["user_id"], session["user_id"], fsid)
    
    if len(check) != 1:
        return "", 204
    else:
        db.execute("DELETE FROM friendships WHERE fsid = ?", fsid)
        return "", 200


@app.route("/upload/message", methods=["POST"])
@login_required
def message_upload():
    fid = None
    if not request.files["file"].filename == '':
        file = request.files["file"]
        fid = db.execute("INSERT INTO File (file, name, mimetype) VALUES (?, ?, ?)", file.read(), file.filename, file.mimetype)        
    
    message = {}
    message["sender"] = session["user_id"]
    message["message"] = request.form.get("message")
    message["receiver"] = request.form.get("receiver")
    message["timestamp"] = request.form.get("timesstamp")
    message["fid"] = fid

    if int(request.form.get("receiver")) in users:
        socketio.emit("send_message", message, room=users[int(request.form.get("receiver"))])
    db.execute("INSERT INTO messages (sender, receiver, message, timestamp, fid) VALUES (?, ?, ?, ?, ?)", session["user_id"], request.form.get("receiver"), request.form.get("message"), request.form.get("timestamp"), fid)
    return {"fid" : fid}, 200

@app.route("/settings", methods=["GET", "POST"])
@login_required
def get_settings():
    if request.method == "GET":
        return render_template("settings.html")
    else:
        if not request.form.get("newUsername") and not request.form.get("oldPassword") and not request.form.get("status") and not request.files['file']:
            flash("Nothing to change!")
            return redirect("/settings")

        newUsername = None
        newPassword = None
        status = None
        dp = None

        if request.form.get("newUsername"):
            check = db.execute("SELECT username FROM users WHERE username = ?",
                              request.form.get("newUsername"))
            if len(check) != 0:
                flash("Username already exists!")
                return redirect("/settings")
            else:
                newUsername = request.form.get("newUsername")
        
        if request.form.get("oldPassword"):
            oldPassword = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])[0]["hash"]
            if not check_password_hash(oldPassword, request.form.get("oldPassword")):
                flash("Old Pasword does not match!")
                return redirect("/settings")
            
            if request.form.get("newPassword") and request.form.get("confirmation"):
                if request.form.get("newPassword") == request.form.get("confirmation"):
                    newPassword = request.form.get("newPassword")
                else:
                    flash("New Password and Confimration does not match!")
                    return redirect("/settings")
            else:
                flash("Enter Both New Password and Confimration!")
                return redirect("/settings")
        
        if request.form.get("status"):
            if request.form.get("status") in ["0", "1"]:
                status = request.form.get("status")
            else:
                flash("Wrong status value!")
                return redirect("/settings")
            
        dp = request.files['file']
        if dp:
            if dp.mimetype not in ["image/jpeg", "image/png", "image/jpg"]:
                dp = None
            else:
                dp = dp.read()
        else:
            dp = None
        
        if newUsername:
            db.execute("UPDATE users SET username = ? WHERE id = ?", newUsername, session["user_id"])
        
        if newPassword:
            newPassword = generate_password_hash(newPassword)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", newPassword, session["user_id"])

        if status:
            status = int(status)
            db.execute("UPDATE users SET status = ? WHERE id = ?", status, session["user_id"])

        if dp:
            db.execute("UPDATE users SET dp = ? WHERE id = ?", dp, session["user_id"])


        flash("Change successful")
        return redirect("/settings")



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

    
if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)