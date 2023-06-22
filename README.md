# Interpol Data Processing System

The Interpol Data Processing System is a Python-based application that processes and manages data obtained from Interpol's public API. The system retrieves information about wanted individuals and stores it in a PostgreSQL database. It provides a web-based user interface to view and search the stored data.

## Features

- Fetches data from Interpol API and stores it in a PostgreSQL database
- Provides a web interface to browse and search the stored data
- Supports pagination for efficient data retrieval
- Handles real-time updates by consuming messages from a RabbitMQ message queue
- Uses SQLAlchemy ORM for database operations
- Implements object-oriented programming principles for code organization
## Getting Started

1. Clone the repository:

   ```bash
   git clone https://gitlab.com/oguz.koc/interpol_task.git

2. Navigate to the project directory:

   ```bash
   cd interpol_task

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt

4. Set up the PostgreSQL database:

- Create a PostgreSQL database with the name specified in the .env file.
- Update the database connection details in the .env file with your own credentials.

5. Set up the RabbitMQ message queue:
- Install RabbitMQ on your local machine or use a remote RabbitMQ server.
- Update the RabbitMQ connection details in the .env file with your own credentials.

6. Run the application

`python consumer.py`

`python producer.py`

- This will start the consumer, producer, and web application components.
7. Open the web application in your browser:
- Navigate to http://localhost:5000 to access the application's user interface.

# Usage
- When the application starts, it will fetch data from the Interpol API and store it in the database.
- The web interface allows users to view and search the stored data.
- Real-time updates are handled by the consumer component, which listens to the RabbitMQ message queue and performs database operations accordingly.
- The producer component periodically fetches new data from the Interpol API and publishes it to the message queue for processing.

# Dockerization (In Progress)
The Interpol Data Processing System is currently being Dockerized for easier deployment and scalability. Docker configuration files and instructions will be provided in future updates to enable easy containerization of the application.