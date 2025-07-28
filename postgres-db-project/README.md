# PostgreSQL Docker Database Setup

This project provides a setup for a PostgreSQL database using Docker. It includes the necessary files to create and initialize the database with specific tables for managing users, item categories, items, item requests, and item history.

## Project Structure

```
postgres-db-project
├── docker-compose.yml
├── init.sql
└── README.md
```

## Steps to Set Up the Database

1. **Pull the PostgreSQL Docker Image**:
   Run the command:
   ```
   docker pull postgres
   ```

2. **Create a `docker-compose.yml` File**:
   Define the PostgreSQL service in the `docker-compose.yml` file:
   ```yaml
   version: '3.1'
   services:
     db:
       image: postgres
       restart: always
       environment:
         POSTGRES_USER: your_username
         POSTGRES_PASSWORD: your_password
         POSTGRES_DB: your_database
       ports:
         - "5432:5432"
       volumes:
         - ./init.sql:/docker-entrypoint-initdb.d/init.sql
   ```

3. **Create an `init.sql` File**:
   Add the following SQL commands to create the tables:
   ```sql
   CREATE TABLE Users (
       user_id SERIAL PRIMARY KEY,
       username VARCHAR(50) NOT NULL,
       password VARCHAR(255) NOT NULL,
       role VARCHAR(10) CHECK (role IN ('admin', 'user'))
   );

   CREATE TABLE ItemCategory (
       category_id SERIAL PRIMARY KEY,
       category_name VARCHAR(50) NOT NULL
   );

   CREATE TABLE Item (
       item_id SERIAL PRIMARY KEY,
       name VARCHAR(50) NOT NULL,
       quantity INT NOT NULL,
       category_id INT REFERENCES ItemCategory(category_id),
       user_id INT REFERENCES Users(user_id)
   );

   CREATE TABLE ItemRequested (
       id SERIAL PRIMARY KEY,
       date_of_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       user_id INT REFERENCES Users(user_id),
       item_id INT REFERENCES Item(item_id),
       reason TEXT
   );

   CREATE TABLE ItemHistory (
       id SERIAL PRIMARY KEY,
       date_of_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       date_of_approve TIMESTAMP,
       user_id INT REFERENCES Users(user_id),
       item_id INT REFERENCES Item(item_id),
       status VARCHAR(10) CHECK (status IN ('Approved', 'Rejected')),
       reason TEXT
   );
   ```

4. **Run the Docker Container**:
   In the terminal, navigate to the project directory and run:
   ```
   docker-compose up
   ```

5. **Access the PostgreSQL Database**:
   You can enter the PostgreSQL container using:
   ```
   docker exec -it <container_id> psql -U your_username -d your_database
   ```

6. **Verify the Tables**:
   Once inside the PostgreSQL prompt, you can check if the tables were created successfully by running:
   ```
   \dt
   ```

This setup will create a PostgreSQL database with the specified tables and relationships.