CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) CHECK (role IN ('admin', 'user')),
    failed_attempts INT DEFAULT 0,
    lockout_until TIMESTAMP
);

CREATE TABLE ItemCategory (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL
);

CREATE TABLE Item (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    category_id INT REFERENCES ItemCategory(category_id)
);

CREATE TABLE ItemRequested (
    id SERIAL PRIMARY KEY,
    date_of_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT REFERENCES Users(user_id),
    item_id INT REFERENCES Item(item_id),
    quantity INT,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'Pending'
);

CREATE TABLE ItemHistory (
    id SERIAL PRIMARY KEY,
    date_of_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_of_approve TIMESTAMP,
    user_id INT REFERENCES Users(user_id),
    item_id INT REFERENCES Item(item_id),
    quantity INT,
    status VARCHAR(10) CHECK (status IN ('Approved', 'Rejected')),
    reason TEXT
);