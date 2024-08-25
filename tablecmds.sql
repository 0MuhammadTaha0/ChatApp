CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    status INTEGER default 1,
    dp BLOB,
    CHECK (status in (0, 1))
);
CREATE TABLE File(
    fid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    file BLOB,
    name TEXT NOT NULL,
    mimetype TEXT NOT NULL
);
CREATE TABLE messages(
    mid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    sender INTEGER NOT NULL,
    receiver INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    fid INTEGER,
    FOREIGN KEY (sender) REFERENCES users(id),
    FOREIGN KEY (receiver) REFERENCES users(id),
    FOREIGN KEY (fid) REFERENCES File(fid)
);
CREATE TABLE friend_requests(
    frid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    userid INTEGER,
    friendid INTEGER,
    UNIQUE (userid, friendid),
    FOREIGN KEY (userid) REFERENCES users(id),
    FOREIGN KEY (friendid) REFERENCES users(id)
);
CREATE TABLE friendships (
    fsid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    userid INTEGER,
    friendid INTEGER,
    UNIQUE (userid, friendid),
    FOREIGN KEY (userid) REFERENCES users(id),
    FOREIGN KEY (friendid) REFERENCES users(id)
);
CREATE UNIQUE INDEX username on users(username);
CREATE INDEX msg on messages(sender, receiver);