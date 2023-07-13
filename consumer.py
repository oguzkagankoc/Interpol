import json
import time

# Import the create_tables function from database_creation module
from database_creation import create_tables

time.sleep(2)
create_tables()
import pika
from multiprocessing import Process
from app import application
from database_operations import DatabaseOperationsCallback
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve RabbitMQ host from environment variable
rabbitmq_host = os.getenv('RABBITMQ_HOST')

# Define a class to consume messages from a RabbitMQ queue
class RabbitMQConsumer:
    """
    A consumer class for consuming messages from RabbitMQ queues.

    Attributes:
        connection (pika.BlockingConnection): Connection to RabbitMQ server.
        channel (pika.channel.Channel): Channel to communicate with RabbitMQ server.
    """
    def __init__(self):
        """
        The constructor for RabbitMQConsumer class. It initializes connection and channel to the RabbitMQ server,
        and declares the queues to consume messages from.
        """
        # Create a connection to the local RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        self.channel = self.connection.channel()

        # Declare queues to consume messages from
        self.channel.queue_declare(queue='add_data')
        self.channel.queue_declare(queue='change_data')

        # Set up consumers to consume messages from the queue and call the callback function for each message
        self.channel.basic_consume(queue='add_data', on_message_callback=self.callback, auto_ack=True)
        self.channel.basic_consume(queue='change_data', on_message_callback=self.callback_change, auto_ack=True)

    # Define callback functions to be called for each message consumed from the queue
    def callback_change(self, ch, method, properties, body):
        """
        The callback function to be executed when a message is received from the 'change_data' queue.
        If there is a record in the database with the same 'entity_id', it will compare the new data
        with the existing one and make necessary changes based on this comparison.

        Parameters:
            ch (pika.channel.Channel): The channel object.
            method (pika.spec.Basic.Deliver): The method frame.
            properties (pika.spec.BasicProperties): The properties.
            body (bytes): The body of the message containing the data for a certain 'entity_id'.
        """
        # Print the message received from the queue
        data = json.loads(body.decode('utf-8'))
        entity_id = data['entity_id']
        print(f"A record of {entity_id} entity id has been received.")

        # Process the message body by passing it to the DatabaseOperationsCallback class
        operator = DatabaseOperationsCallback()
        operator.callback_change_db(body)

    def callback(self, ch, method, properties, body):
        """
        The callback function to be executed when a message is received from the 'add_data' queue.

        This function first decodes the received message and retrieves the 'entity_id' from the message.
        If there is no record in the database with the same 'entity_id', it performs the necessary operations
        to add the new data to the database.

        Parameters:
            ch (pika.channel.Channel): The channel object.
            method (pika.spec.Basic.Deliver): The method frame.
            properties (pika.spec.BasicProperties): The properties.
            body (bytes): The body of the message containing the data for a certain 'entity_id'.
        """
        # Print the message received from the queue
        data = json.loads(body.decode('utf-8'))
        entity_id = data['entity_id']
        print(f"A record of {entity_id} entity id has been received.")

        # Process the message body by passing it to the DatabaseOperationsCallback class
        operator = DatabaseOperationsCallback()
        operator.callback_db(body)

    def start_consuming(self):
        # Start consuming messages from the queue
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def close(self):
        # Close the RabbitMQ connection
        self.connection.close()


# Define a consumer function that initializes and starts a RabbitMQ consumer
def consumer():
    """
    Function to initialize and start a RabbitMQ consumer.
    """
    consumer = RabbitMQConsumer()
    consumer.start_consuming()


# Check if the current script is being run as the main entry point
if __name__ == "__main__":

    time.sleep(1)
    # Create two Process objects, each associated with a target function
    process1 = Process(target=consumer)
    process2 = Process(target=application)

    # Start the processes, which will execute the target functions concurrently
    process1.start()
    process2.start()

    # Wait for the processes to finish their execution
    process1.join()
    process2.join()
