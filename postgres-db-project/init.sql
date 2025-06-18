CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) CHECK (role IN ('admin', 'user')),
    failed_attempts INT DEFAULT 0,
    lockout_until TIMESTAMP
);

INSERT INTO Users (username, password, role)
SELECT 'admin', 'pbkdf2:sha256:600000$VoWEL4wgYV6GbJzk$0533b5b5455e6cddc9e032ebd5acffa000ea2a25e65ce680bf635cf536bd471f', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM Users WHERE username = 'admin');

CREATE TABLE IF NOT EXISTS ItemCategory (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Item (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    category_id INT REFERENCES ItemCategory(category_id),
    user_id INT REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS ItemRequested (
    id SERIAL PRIMARY KEY,
    date_of_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT REFERENCES Users(user_id),
    item_id INT REFERENCES Item(item_id),
    quantity INT,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS ItemHistory (
    id SERIAL PRIMARY KEY,
    date_of_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_of_approve TIMESTAMP,
    user_id INT REFERENCES Users(user_id),
    item_id INT REFERENCES Item(item_id),
    quantity INT,
    status VARCHAR(10) CHECK (status IN ('Approved', 'Rejected')),
    reason TEXT
);