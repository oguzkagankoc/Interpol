# Interpol Task

## Technologies

Interpol Task is built using the following technologies:

- Python 3: The backend of the application is written in Python 3 using the Flask web framework.

- PostgreSQL: The application uses PostgreSQL as the database management system.

- HTML, CSS, JavaScript: The frontend of the application is built using HTML, CSS, and JavaScript, and utilizes the Bootstrap framework for styling and responsiveness.

- Docker: The application is containerized using Docker for easy deployment and scalability.
## Getting Started

1. Clone the repository:

   ```bash
   git clone https://gitlab.com/oguz.koc/interpol_task.git

2. Navigate to the project directory:

   ```bash
   cd interpol_task

3. Build and start the Docker containers using Docker Compose:
   - Notes: The Docker containers are still in the development phase and may require further configuration or adjustments.

    ```bash
    docker-compose up --build
   
This command will build the Docker images and start the containers for database_creation.py, rabbitmq_postgresql_consumer.py, interpol.py, and application.py scripts.

The containers will be orchestrated as follows:

 - database_creation.py will run and create the necessary database tables.
 - rabbitmq_postgresql_consumer.py will consume messages from RabbitMQ and insert them into the database.
 - interpol.py will perform data interpolation based on the consumed messages.
 - application.py will run the main application.
4. Access the application:

    Once the containers are up and running, you can access the application by opening your web browser and navigating to http://localhost:5000.

