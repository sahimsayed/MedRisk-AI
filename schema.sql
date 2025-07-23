CREATE DATABASE medriskAI;

USE medriskAI;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE prediction_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    disease VARCHAR(50),
    input_data TEXT,
    prediction_result VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);